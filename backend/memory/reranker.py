"""
Reranker - 检索结果重排序
使用 LLM 对候选结果进行相关性排序

功能：
1. LLM Rerank（使用 Qwen 判断相关性）
2. 交叉编码器风格的评分
3. 结果融合优化
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# LLM 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class Reranker:
    """
    检索结果重排序器
    
    策略：
    1. LLM Rerank：让 LLM 判断每个候选与查询的相关性
    2. 批量处理：并行评估多个候选
    3. 分数归一化：将 LLM 评分转换为 0-1 分数
    """
    
    def __init__(self):
        """初始化 Reranker"""
        self._init_client()
        
        # 并行线程池
        self._executor = ThreadPoolExecutor(max_workers=3)
    
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
    
    def rerank(self, query: str, candidates: List[Dict], 
               top_k: int = 3, score_key: str = "rerank_score") -> List[Dict]:
        """
        对候选结果重排序
        
        Args:
            query: 用户查询
            candidates: 候选结果列表，每个包含 moment_id 和 messages
            top_k: 返回数量
            score_key: 分数字段名
            
        Returns:
            List[Dict]: 重排序后的结果
        """
        if not candidates:
            return []
        
        if not self.client:
            print("⚠️ Reranker: LLM 客户端未初始化，跳过重排序")
            return candidates[:top_k]
        
        print(f"🔄 Rerank: 对 {len(candidates)} 个候选重排序")
        
        # 方法1：批量评分（更快）
        scored = self._batch_score(query, candidates)
        
        # 按分数排序
        scored.sort(key=lambda x: x.get(score_key, 0), reverse=True)
        
        # 打印结果
        for i, item in enumerate(scored[:top_k]):
            print(f"   #{i+1} score={item.get(score_key, 0):.2f} | {item.get('moment_id', '')}")
        
        return scored[:top_k]
    
    def _batch_score(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """
        批量评分（一次 LLM 调用评估所有候选）
        """
        # 构建候选摘要
        candidate_texts = []
        for i, c in enumerate(candidates):
            # 提取关键内容
            messages = c.get('messages', [])
            user_msgs = [m['content'] for m in messages if m.get('role') == 'user']
            text = " ".join(user_msgs[:3])[:200]  # 限制长度
            
            summary = c.get('summary', '')
            if summary:
                text = f"{summary} | {text}"
            
            candidate_texts.append(f"[{i}] {text}")
        
        if not candidate_texts:
            return candidates
        
        # 构建 prompt
        prompt = f"""你是一个相关性判断专家。请评估以下候选内容与查询的相关程度。

查询："{query}"

候选内容：
{chr(10).join(candidate_texts)}

请为每个候选打分（0-10分），格式如下：
[0]: 分数
[1]: 分数
...

只返回分数，不要解释。"""

        try:
            response = self.client.chat.completions.create(
                model="qwen-turbo",  # 用快速模型
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析分数
            scores = self._parse_scores(result, len(candidates))
            
            # 合并分数到候选
            for i, c in enumerate(candidates):
                if i < len(scores):
                    c['rerank_score'] = scores[i] / 10.0  # 归一化到 0-1
                else:
                    c['rerank_score'] = 0.0
            
            return candidates
            
        except Exception as e:
            print(f"⚠️ Rerank 批量评分失败: {e}")
            # 降级：保持原有分数
            for c in candidates:
                c['rerank_score'] = c.get('retrieval_score', 0.5)
            return candidates
    
    def _parse_scores(self, result: str, expected_count: int) -> List[float]:
        """解析 LLM 返回的分数"""
        import re
        
        scores = []
        
        # 尝试多种格式
        # 格式1: [0]: 8
        pattern1 = re.findall(r'\[(\d+)\]:\s*(\d+(?:\.\d+)?)', result)
        if pattern1:
            score_map = {int(idx): float(score) for idx, score in pattern1}
            for i in range(expected_count):
                scores.append(score_map.get(i, 5.0))
            return scores
        
        # 格式2: 0: 8 或 0 - 8
        pattern2 = re.findall(r'(\d+)[\s:\-]+(\d+(?:\.\d+)?)', result)
        if pattern2:
            score_map = {int(idx): float(score) for idx, score in pattern2}
            for i in range(expected_count):
                scores.append(score_map.get(i, 5.0))
            return scores
        
        # 格式3: 纯数字列表
        numbers = re.findall(r'(\d+(?:\.\d+)?)', result)
        for num in numbers[:expected_count]:
            scores.append(float(num))
        
        # 补齐
        while len(scores) < expected_count:
            scores.append(5.0)
        
        return scores
    
    def _parallel_score(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """
        并行评分（每个候选单独评估，更准确但更慢）
        """
        def score_one(candidate: Dict) -> Tuple[Dict, float]:
            messages = candidate.get('messages', [])
            user_msgs = [m['content'] for m in messages if m.get('role') == 'user']
            text = " ".join(user_msgs[:3])[:300]
            
            prompt = f"""判断以下内容与查询的相关程度。

查询："{query}"
内容："{text}"

相关程度（只返回数字 0-10）："""

            try:
                response = self.client.chat.completions.create(
                    model="qwen-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                
                score_text = response.choices[0].message.content.strip()
                score = float(re.search(r'(\d+(?:\.\d+)?)', score_text).group(1))
                return candidate, min(score / 10.0, 1.0)
                
            except:
                return candidate, 0.5
        
        # 并行执行
        import re
        futures = []
        for c in candidates:
            futures.append(self._executor.submit(score_one, c))
        
        # 收集结果
        for future in as_completed(futures):
            candidate, score = future.result()
            candidate['rerank_score'] = score
        
        return candidates
    
    def shutdown(self):
        """关闭线程池"""
        self._executor.shutdown(wait=False)


# 全局单例
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """获取 Reranker 单例"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


# ============================================================
# 测试代码
# ============================================================

def test_reranker():
    """测试 Reranker"""
    print("\n" + "="*60)
    print("🧪 测试 Reranker")
    print("="*60 + "\n")
    
    reranker = Reranker()
    
    # 模拟候选
    candidates = [
        {
            "moment_id": "moment_001",
            "messages": [
                {"role": "user", "content": "今天吃了麻辣火锅，太辣了"},
                {"role": "assistant", "content": "辣到流泪吗？"}
            ],
            "retrieval_score": 0.5
        },
        {
            "moment_id": "moment_002", 
            "messages": [
                {"role": "user", "content": "今天在公司被主管夸了，方案用的是亮橙色配灰底"},
                {"role": "assistant", "content": "太棒了！"}
            ],
            "retrieval_score": 0.6
        },
        {
            "moment_id": "moment_003",
            "messages": [
                {"role": "user", "content": "下班买了杯桂花拿铁庆祝"},
                {"role": "assistant", "content": "甜吗？"}
            ],
            "retrieval_score": 0.7
        }
    ]
    
    query = "被表扬的事"
    print(f"🔍 查询: '{query}'")
    print(f"📋 候选数: {len(candidates)}")
    
    results = reranker.rerank(query, candidates, top_k=3)
    
    print("\n📊 重排序结果:")
    for i, r in enumerate(results):
        print(f"   #{i+1} {r['moment_id']}: rerank={r.get('rerank_score', 0):.2f}")
    
    reranker.shutdown()
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_reranker()
