"""
Query Parser - LLM 查询理解
用 LLM 替代硬编码规则，智能解析用户查询意图

功能：
1. 提取查询关键词
2. 识别实体类型
3. 解析时间范围
4. 判断查询类型（事实/情感/模糊）
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# LLM 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class QueryParser:
    """
    查询理解器
    
    使用 LLM 智能解析用户查询，提取：
    - keywords: 检索关键词
    - entity_types: 相关实体类型
    - time_range: 时间范围
    - query_type: 查询类型（fact/emotion/fuzzy）
    - search_strategy: 推荐检索策略
    """
    
    def __init__(self):
        """初始化查询理解器"""
        self._init_client()
        
        # 简单缓存（避免重复调用）
        self._cache: Dict[str, Dict] = {}
        self._cache_max_size = 100
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if not OPENAI_AVAILABLE:
            self.client = None
            return
        
        api_key = os.getenv("ALIYUN_QWEN_KEY")
        if not api_key:
            try:
                from config.api_config import APIConfig
                api_key = APIConfig.QWEN_API_KEY
            except:
                pass
        
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        else:
            self.client = None
    
    def parse(self, query: str) -> Dict:
        """
        解析用户查询
        
        Args:
            query: 用户查询文本
            
        Returns:
            Dict: 解析结果
            {
                "keywords": ["关键词1", "关键词2"],
                "entity_types": ["objects", "places", "people", "events"],
                "time_range": {"start": "2024-01-01", "end": "2024-01-07"} or None,
                "query_type": "fact" | "emotion" | "fuzzy",
                "search_strategy": "structured" | "vector" | "hybrid",
                "expanded_queries": ["扩展查询1", "扩展查询2"],
                "confidence": 0.9
            }
        """
        # 检查缓存
        cache_key = query.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # LLM 解析
        if self.client:
            result = self._parse_with_llm(query)
        else:
            # 降级到规则解析
            result = self._parse_with_rules(query)
        
        # 缓存结果
        if len(self._cache) >= self._cache_max_size:
            # 简单清理：删除一半
            keys_to_delete = list(self._cache.keys())[:self._cache_max_size // 2]
            for k in keys_to_delete:
                del self._cache[k]
        
        self._cache[cache_key] = result
        return result
    
    def _parse_with_llm(self, query: str) -> Dict:
        """使用 LLM 解析查询"""
        prompt = f"""分析用户的查询意图，提取检索所需信息。

用户查询："{query}"

请返回 JSON 格式（不要任何其他文字）：
{{
    "keywords": ["关键词1", "关键词2"],  // 用于检索的核心关键词，包括同义词扩展
    "entity_types": ["objects"],  // 相关实体类型：objects/places/people/events/habits
    "time_reference": "today/yesterday/last_week/specific_date/none",  // 时间引用
    "query_type": "fact",  // fact=问具体事实, emotion=问感受回忆, fuzzy=模糊查询
    "search_strategy": "hybrid",  // structured=精确匹配, vector=语义匹配, hybrid=混合
    "expanded_queries": ["扩展查询1"],  // 语义扩展的查询（用于向量检索）
    "confidence": 0.9  // 解析置信度
}}

示例1：
查询："你记得我昨天喝的咖啡是什么口味吗"
返回：{{"keywords": ["咖啡", "口味", "饮品"], "entity_types": ["objects"], "time_reference": "yesterday", "query_type": "fact", "search_strategy": "structured", "expanded_queries": ["昨天的咖啡", "喝的饮料"], "confidence": 0.95}}

示例2：
查询："上次我心情不好的时候"
返回：{{"keywords": ["心情不好", "难过", "伤心"], "entity_types": ["events"], "time_reference": "none", "query_type": "emotion", "search_strategy": "vector", "expanded_queries": ["情绪低落", "不开心的事"], "confidence": 0.8}}

示例3：
查询："之前聊过的那个事"
返回：{{"keywords": [], "entity_types": [], "time_reference": "none", "query_type": "fuzzy", "search_strategy": "vector", "expanded_queries": ["之前的对话", "聊过的话题"], "confidence": 0.5}}

只返回 JSON，不要其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model="qwen-turbo",  # 用快速模型，节省成本
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 清理 markdown 标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 解析 JSON
            result = json.loads(result_text)
            
            # 处理时间引用
            result["time_range"] = self._parse_time_reference(
                result.get("time_reference", "none")
            )
            
            return result
            
        except Exception as e:
            print(f"   ⚠️ LLM 解析失败: {e}，降级到规则解析")
            return self._parse_with_rules(query)
    
    def _parse_with_rules(self, query: str) -> Dict:
        """规则解析（降级方案）"""
        keywords = []
        entity_types = []
        query_type = "fuzzy"
        search_strategy = "hybrid"
        
        # 简单关键词提取
        # 移除停用词后分词
        stopwords = {'的', '了', '是', '在', '我', '你', '吗', '呢', '啊', '吧', 
                     '什么', '怎么', '记得', '记不记得', '还', '有', '没有'}
        
        words = list(query)
        # 简单的 2-gram
        for i in range(len(words) - 1):
            bigram = words[i] + words[i+1]
            if bigram not in stopwords and len(bigram) == 2:
                keywords.append(bigram)
        
        # 检测实体类型
        if re.search(r'(咖啡|拿铁|奶茶|吃|喝|饭|菜)', query):
            entity_types.append("objects")
            keywords.extend(re.findall(r'(咖啡|拿铁|奶茶|饭|菜|茶)', query))
        
        if re.search(r'(公司|学校|家|店|哪里|在哪)', query):
            entity_types.append("places")
        
        if re.search(r'(谁|朋友|同事|家人)', query):
            entity_types.append("people")
        
        # 检测查询类型
        if re.search(r'(什么|哪个|几|多少|是不是)', query):
            query_type = "fact"
            search_strategy = "structured"
        elif re.search(r'(心情|感觉|开心|难过|情绪)', query):
            query_type = "emotion"
            search_strategy = "vector"
        
        # 检测时间
        time_range = None
        if "今天" in query:
            time_range = self._parse_time_reference("today")
        elif "昨天" in query:
            time_range = self._parse_time_reference("yesterday")
        elif "上周" in query or "最近" in query:
            time_range = self._parse_time_reference("last_week")
        
        # 去重
        keywords = list(set(keywords))[:10]
        entity_types = list(set(entity_types)) or ["objects", "events"]
        
        return {
            "keywords": keywords,
            "entity_types": entity_types,
            "time_reference": "none",
            "time_range": time_range,
            "query_type": query_type,
            "search_strategy": search_strategy,
            "expanded_queries": [query],
            "confidence": 0.5
        }
    
    def _parse_time_reference(self, ref: str) -> Optional[Dict]:
        """解析时间引用为具体日期范围"""
        now = datetime.now()
        
        if ref == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return {
                "start": start.isoformat(),
                "end": now.isoformat()
            }
        
        elif ref == "yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59)
            return {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        
        elif ref == "last_week":
            start = now - timedelta(days=7)
            return {
                "start": start.isoformat(),
                "end": now.isoformat()
            }
        
        elif ref == "last_month":
            start = now - timedelta(days=30)
            return {
                "start": start.isoformat(),
                "end": now.isoformat()
            }
        
        return None
    
    def get_search_config(self, query: str) -> Dict:
        """
        获取检索配置（简化接口）
        
        Args:
            query: 用户查询
            
        Returns:
            Dict: 检索配置
            {
                "use_structured": True,
                "use_vector": True,
                "structured_weight": 0.6,
                "vector_weight": 0.4,
                "keywords": [...],
                "entity_types": [...],
                "time_range": {...}
            }
        """
        parsed = self.parse(query)
        
        strategy = parsed.get("search_strategy", "hybrid")
        
        if strategy == "structured":
            return {
                "use_structured": True,
                "use_vector": False,
                "structured_weight": 1.0,
                "vector_weight": 0.0,
                "keywords": parsed.get("keywords", []),
                "entity_types": parsed.get("entity_types", []),
                "time_range": parsed.get("time_range"),
                "expanded_queries": parsed.get("expanded_queries", [query])
            }
        
        elif strategy == "vector":
            return {
                "use_structured": False,
                "use_vector": True,
                "structured_weight": 0.0,
                "vector_weight": 1.0,
                "keywords": parsed.get("keywords", []),
                "entity_types": parsed.get("entity_types", []),
                "time_range": parsed.get("time_range"),
                "expanded_queries": parsed.get("expanded_queries", [query])
            }
        
        else:  # hybrid
            # 根据置信度调整权重
            confidence = parsed.get("confidence", 0.5)
            if confidence > 0.8:
                # 高置信度：结构化优先
                structured_weight = 0.7
            elif confidence > 0.5:
                # 中置信度：均衡
                structured_weight = 0.5
            else:
                # 低置信度：向量优先
                structured_weight = 0.3
            
            return {
                "use_structured": True,
                "use_vector": True,
                "structured_weight": structured_weight,
                "vector_weight": 1 - structured_weight,
                "keywords": parsed.get("keywords", []),
                "entity_types": parsed.get("entity_types", []),
                "time_range": parsed.get("time_range"),
                "expanded_queries": parsed.get("expanded_queries", [query])
            }


# 全局单例（避免重复初始化）
_query_parser: Optional[QueryParser] = None


def get_query_parser() -> QueryParser:
    """获取查询解析器单例"""
    global _query_parser
    if _query_parser is None:
        _query_parser = QueryParser()
    return _query_parser


# ============================================================
# 测试代码
# ============================================================

def test_query_parser():
    """测试查询解析器"""
    print("\n" + "="*60)
    print("🧪 测试 QueryParser")
    print("="*60 + "\n")
    
    parser = QueryParser()
    
    test_queries = [
        "你记得我昨天喝的咖啡是什么口味吗",
        "上次我心情不好是因为什么",
        "之前聊过的那个事",
        "我方案的配色是什么",
        "在星巴克买的那杯",
        "最近工作上有什么开心的事吗"
    ]
    
    for query in test_queries:
        print(f"🔍 查询: '{query}'")
        result = parser.parse(query)
        print(f"   关键词: {result.get('keywords', [])}")
        print(f"   实体类型: {result.get('entity_types', [])}")
        print(f"   查询类型: {result.get('query_type', '')}")
        print(f"   检索策略: {result.get('search_strategy', '')}")
        print(f"   扩展查询: {result.get('expanded_queries', [])}")
        print(f"   时间范围: {result.get('time_range', None)}")
        print(f"   置信度: {result.get('confidence', 0)}")
        print()
    
    print("="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_query_parser()
