"""
Context RAG - 上下文检索（V4 混合检索 + Rerank 版）

改进点：
1. SQLite 结构化检索（V2）
2. 向量语义检索（V3）
3. LLM Query 理解（V3）
4. 混合检索 + 结果融合（V3）
5. Rerank 重排序（V4 新增）
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# 导入存储层
from .moment_storage import MomentStorage

# 导入向量存储层
try:
    from .vector_store import VectorStore
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

# 导入查询解析器
try:
    from .query_parser import QueryParser, get_query_parser
    QUERY_PARSER_AVAILABLE = True
except ImportError:
    QUERY_PARSER_AVAILABLE = False

# 导入 Reranker
try:
    from .reranker import Reranker, get_reranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False


class ContextRAG:
    """
    上下文检索系统（V4 混合检索 + Rerank）
    
    特性：
    1. 结构化检索（SQLite 实体索引）
    2. 向量检索（ChromaDB 语义匹配）
    3. LLM Query 理解（智能解析查询意图）
    4. 混合检索 + 结果融合
    5. Rerank 重排序
    """
    
    def __init__(self, user_id: str = None, base_moments_dir: str = "storage", 
                 enable_rerank: bool = True):
        """
        初始化 Context RAG
        
        Args:
            user_id: 用户唯一标识
            base_moments_dir: Moments 基础目录
            enable_rerank: 是否启用 Rerank
        """
        self.user_id = user_id or "default_user"
        self.base_moments_dir = Path(base_moments_dir)
        self.enable_rerank = enable_rerank
        
        # SQLite 存储
        self.storage = MomentStorage(
            user_id=self.user_id,
            base_dir=str(self.base_moments_dir)
        )
        
        # 向量存储
        if VECTOR_AVAILABLE:
            self.vector_store = VectorStore(
                user_id=self.user_id,
                base_dir=str(self.base_moments_dir)
            )
        else:
            self.vector_store = None
        
        # 查询解析器
        if QUERY_PARSER_AVAILABLE:
            self.query_parser = get_query_parser()
        else:
            self.query_parser = None
        
        # Reranker
        if RERANKER_AVAILABLE and enable_rerank:
            self.reranker = get_reranker()
        else:
            self.reranker = None
        
        # 兼容旧代码
        self.moments_dir = self.base_moments_dir / "moments" / self.user_id
        
        print(f"🔍 ContextRAG V4 初始化: user={self.user_id}")
        print(f"   结构化检索: ✅")
        print(f"   向量检索: {'✅' if self.vector_store else '❌'}")
        print(f"   Query 解析: {'✅' if self.query_parser else '❌'}")
        print(f"   Rerank: {'✅' if self.reranker else '❌'}")
    
    def set_user_id(self, user_name: str, agent_name: str):
        """设置用户 ID"""
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        self.storage.set_user_id(user_name, agent_name)
        
        if self.vector_store:
            self.vector_store.set_user_id(user_name, agent_name)
        
        self.moments_dir = self.base_moments_dir / "moments" / self.user_id
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        混合检索（主入口）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            List[Dict]: 检索结果
        """
        print(f"\n🔍 混合检索: '{query}'")
        
        # 1. 解析查询
        if self.query_parser:
            search_config = self.query_parser.get_search_config(query)
            print(f"   📊 检索配置: strategy={search_config.get('use_structured', True)}/{search_config.get('use_vector', True)}")
            print(f"   📊 关键词: {search_config.get('keywords', [])}")
            print(f"   📊 扩展查询: {search_config.get('expanded_queries', [])}")
        else:
            # 降级配置
            search_config = {
                "use_structured": True,
                "use_vector": True,
                "structured_weight": 0.5,
                "vector_weight": 0.5,
                "keywords": self._extract_keywords_simple(query),
                "entity_types": ["objects", "places", "people", "events"],
                "expanded_queries": [query]
            }
        
        results = []
        
        # 2. 结构化检索
        if search_config.get("use_structured", True):
            structured_results = self._search_structured(
                keywords=search_config.get("keywords", []),
                entity_types=search_config.get("entity_types", []),
                top_k=top_k
            )
            print(f"   📦 结构化检索: {len(structured_results)} 条")
            
            # 加权
            weight = search_config.get("structured_weight", 0.5)
            for r in structured_results:
                r["source"] = "structured"
                r["weighted_score"] = r.get("score", 0) * weight
            results.extend(structured_results)
        
        # 3. 向量检索
        if search_config.get("use_vector", True) and self.vector_store:
            # 使用扩展查询
            expanded_queries = search_config.get("expanded_queries", [query])
            vector_results = []
            
            for eq in expanded_queries[:2]:  # 最多用2个扩展查询
                vr = self.vector_store.search(eq, top_k=top_k)
                vector_results.extend(vr)
            
            print(f"   🔮 向量检索: {len(vector_results)} 条")
            
            # 加权
            weight = search_config.get("vector_weight", 0.5)
            for r in vector_results:
                r["source"] = "vector"
                r["weighted_score"] = r.get("score", 0) * weight
            results.extend(vector_results)
        
        # 4. 结果融合 + 去重
        merged = self._merge_results(results, top_k * 2)  # 多取一些给 Rerank
        print(f"   ✅ 融合后: {len(merged)} 条")
        
        # 5. 加载完整 Moment 数据
        final_results = []
        seen_ids = set()
        
        for r in merged:
            moment_id = r.get("moment_id", "")
            if moment_id and moment_id not in seen_ids:
                moment = self.storage.get_moment(moment_id)
                if moment:
                    moment["retrieval_score"] = r.get("weighted_score", 0)
                    moment["retrieval_source"] = r.get("source", "unknown")
                    final_results.append(moment)
                    seen_ids.add(moment_id)
        
        # 6. Rerank 重排序
        if self.reranker and len(final_results) > 1:
            print(f"   🔄 Rerank 重排序...")
            final_results = self.reranker.rerank(query, final_results, top_k=top_k)
        
        return final_results[:top_k]
    
    def _search_structured(self, keywords: List[str], 
                           entity_types: List[str], 
                           top_k: int = 5) -> List[Dict]:
        """结构化检索"""
        results = []
        
        for kw in keywords[:5]:  # 最多5个关键词
            # 按实体类型检索
            for et in entity_types:
                matches = self.storage.search_by_entity(et, kw, top_k=3)
                for m in matches:
                    results.append({
                        "moment_id": m["moment_id"],
                        "score": 1.0,  # 精确匹配给满分
                        "match_type": f"{et}:{kw}"
                    })
            
            # 关键词检索
            kw_matches = self.storage.search_by_keywords([kw], top_k=3)
            for m in kw_matches:
                results.append({
                    "moment_id": m["moment_id"],
                    "score": 0.8,
                    "match_type": f"keyword:{kw}"
                })
        
        return results
    
    def _merge_results(self, results: List[Dict], top_k: int) -> List[Dict]:
        """
        结果融合（按 moment_id 聚合分数）
        """
        # 按 moment_id 聚合
        score_map = {}
        
        for r in results:
            mid = r.get("moment_id", "")
            if not mid:
                continue
            
            if mid not in score_map:
                score_map[mid] = {
                    "moment_id": mid,
                    "weighted_score": 0,
                    "sources": [],
                    "match_types": []
                }
            
            score_map[mid]["weighted_score"] += r.get("weighted_score", 0)
            score_map[mid]["sources"].append(r.get("source", ""))
            if "match_type" in r:
                score_map[mid]["match_types"].append(r["match_type"])
        
        # 排序
        merged = list(score_map.values())
        merged.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # 标记来源
        for m in merged:
            sources = set(m["sources"])
            if "structured" in sources and "vector" in sources:
                m["source"] = "hybrid"
            elif "structured" in sources:
                m["source"] = "structured"
            else:
                m["source"] = "vector"
        
        return merged[:top_k]
    
    def _extract_keywords_simple(self, text: str) -> List[str]:
        """简单关键词提取（降级方案）"""
        stopwords = {'的', '了', '是', '在', '我', '你', '吗', '呢', '啊', '吧',
                     '什么', '怎么', '记得', '还', '有', '没有', '那个', '这个'}
        
        keywords = []
        
        # 简单分词
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            if bigram not in stopwords:
                keywords.append(bigram)
        
        return list(set(keywords))[:10]
    
    # ============================================================
    # 兼容旧 API
    # ============================================================
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 3) -> List[Dict]:
        """基于关键词检索（兼容旧 API）"""
        return self.storage.search_by_keywords(keywords, top_k)
    
    def search_by_content(self, query: str, top_k: int = 3) -> List[Dict]:
        """基于内容检索（兼容旧 API，现在使用混合检索）"""
        return self.search(query, top_k)
    
    def get_recent_moments(self, n: int = 5) -> List[Dict]:
        """获取最近的 n 个 Moments"""
        return self.storage.get_recent_moments(n)
    
    def search_by_emotion(self, emotion: str, top_k: int = 3) -> List[Dict]:
        """基于情绪检索"""
        all_moments = self.storage.get_all_moments()
        results = [m for m in all_moments if m.get('emotion_tag') == emotion]
        return results[:top_k]
    
    def is_fact_query(self, query: str) -> bool:
        """判断是否在问事实"""
        if self.query_parser:
            parsed = self.query_parser.parse(query)
            return parsed.get("query_type") == "fact"
        
        # 降级规则
        fact_patterns = [
            r'(什么|啥)(颜色|口味|味道|配色|名字)',
            r'(记得|记不记得).*(吗|嘛)',
            r'(哪|哪里|哪儿|在哪)',
            r'(几点|什么时候|多久)',
            r'(谁|是谁)',
            r'(多少|几个|几次)',
        ]
        return any(re.search(p, query) for p in fact_patterns)
    
    def generate_context_prompt(self, query: str, max_context: int = 2) -> str:
        """
        生成上下文提示（用于注入到 LLM prompt）
        
        Args:
            query: 当前查询
            max_context: 最多包含几个 Moments 的上下文
        
        Returns:
            str: 上下文提示文本
        """
        # 判断是否在问事实
        is_asking_fact = self.is_fact_query(query)
        
        if is_asking_fact:
            print(f"🔍 检测到事实查询: {query}")
            
            # 混合检索
            results = self.search(query, top_k=max_context)
            
            if results:
                # 找到结果
                best_result = results[0]
                fact = self._extract_fact_from_moment(best_result, query)
                
                if fact:
                    print(f"   ✅ 找到事实: {fact[:100]}...")
                    return self._build_fact_prompt_high_confidence(
                        fact,
                        self._get_moment_context(best_result)
                    )
            
            # 没找到
            print(f"   ❌ 未找到相关事实")
            return self._build_fact_prompt_not_found()
        
        # 普通对话检索
        relevant_moments = self.search(query, top_k=max_context)
        
        if not relevant_moments:
            return ""
        
        print(f"   ✅ 找到 {len(relevant_moments)} 个相关 Moments")
        
        # 构建上下文
        context = "【重要：历史记忆】\n你和用户之前聊过以下内容：\n\n"
        
        for i, moment in enumerate(relevant_moments, 1):
            timestamp = moment.get('timestamp', '')
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%Y年%m月%d日')
            else:
                time_str = "之前"
            
            context += f"📌 {time_str}的对话：\n"
            
            # 来源标记
            source = moment.get('retrieval_source', 'unknown')
            if source == 'hybrid':
                context += f"[精确+语义匹配]\n"
            elif source == 'vector':
                context += f"[语义匹配]\n"
            
            if moment.get('summary'):
                context += f"摘要：{moment['summary']}\n"
            
            messages = moment.get('messages', [])
            if messages:
                for msg in messages[:6]:
                    role = "用户" if msg['role'] == 'user' else "你"
                    content = msg['content'][:80]
                    context += f"  {role}：{content}\n"
            
            context += "\n"
        
        context += self._get_memory_rules()
        return context.strip()
    
    def _extract_fact_from_moment(self, moment: Dict, query: str) -> Optional[str]:
        """从 Moment 中提取事实"""
        entities = moment.get('entities', {})
        
        # 尝试从实体中提取
        if "颜色" in query or "配色" in query:
            for obj_name, obj_info in entities.get('objects', {}).items():
                if obj_info.get('color') or obj_info.get('description'):
                    return obj_info.get('description') or obj_info.get('color')
        
        if "口味" in query or "味道" in query:
            for obj_name, obj_info in entities.get('objects', {}).items():
                if '咖啡' in obj_name or '拿铁' in obj_name or '茶' in obj_name:
                    return obj_info.get('description') or obj_name
        
        # 从消息中提取
        user_messages = [m['content'] for m in moment.get('messages', []) if m['role'] == 'user']
        if user_messages:
            return " ".join(user_messages[:2])
        
        return None
    
    def _get_moment_context(self, moment: Dict) -> str:
        """获取 Moment 的完整上下文"""
        parts = []
        
        if moment.get('summary'):
            parts.append(f"摘要：{moment['summary']}")
        
        messages = moment.get('messages', [])
        for msg in messages[:4]:
            role = "用户" if msg['role'] == 'user' else "Agent"
            parts.append(f"{role}：{msg['content']}")
        
        return "\n".join(parts)
    
    def _build_fact_prompt_high_confidence(self, fact: str, full_context: str) -> str:
        """构建高置信度事实的 prompt"""
        return f"""
【⚠️ 极其重要：你必须准确回答这个事实，禁止编造】

用户在询问一个具体事实。我已经从历史对话中找到了准确答案：

✅ **找到的事实**：
{fact}

✅ **完整上下文**：
{full_context}

⚠️ **规则**：
1. 必须使用上面的事实回答
2. 禁止编造或修改
3. 可以加语气词让回答自然
"""
    
    def _build_fact_prompt_not_found(self) -> str:
        """构建未找到事实的 prompt"""
        return """
【🚨 最高优先级：你不记得这个细节，必须承认，禁止编造】

用户在询问一个具体事实，但我在历史记忆中找不到相关信息。

你必须承认不记得：
- ✅ "这个我好像没听你提过，是什么？"
- ✅ "我记不太清了，你能提醒我一下吗？"

绝对禁止编造任何内容！
"""
    
    def _get_memory_rules(self) -> str:
        """返回记忆规则提示"""
        return """
⚠️ **记忆规则**：
- 有明确事实时必须准确使用，不能修改
- 不确定时承认不记得，禁止编造
- 禁止用模糊表达逃避事实
"""


# ============================================================
# 测试代码
# ============================================================

def test_context_rag():
    """测试 Context RAG V3"""
    print("\n" + "="*60)
    print("🧪 测试 Context RAG V3 (混合检索)")
    print("="*60 + "\n")
    
    rag = ContextRAG(base_moments_dir="storage/test")
    
    # 测试混合检索
    test_queries = [
        "咖啡什么口味",
        "被表扬的事",
        "工作上开心的事",
        "方案的配色"
    ]
    
    for query in test_queries:
        print(f"\n{'='*40}")
        results = rag.search(query, top_k=2)
        print(f"   结果数: {len(results)}")
        for r in results:
            print(f"   📌 {r.get('moment_id')}: score={r.get('retrieval_score', 0):.2f}, source={r.get('retrieval_source')}")
    
    # 测试生成上下文
    print(f"\n{'='*40}")
    print("📝 测试生成上下文")
    context = rag.generate_context_prompt("你记得我方案的配色吗", max_context=2)
    print(f"   上下文长度: {len(context)} 字符")
    print(f"   预览: {context[:200]}...")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_context_rag()
