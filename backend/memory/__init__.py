"""
Memory Module - RAG 记忆系统（V4 混合检索 + Rerank 版）

包含：
- MomentManager: Moment 会话管理（SQLite + 向量存储）
- ContextRAG: 上下文检索（混合检索 + Rerank）
- VectorStore: 向量存储层
- QueryParser: LLM 查询理解
- Reranker: 检索结果重排序
- StyleRAG: 风格学习（jieba 分词）
- MomentCard: Moment 卡片生成
"""

from .moment_storage import MomentStorage
from .moment_manager import MomentManager
from .moment_card import generate_moment_card, MomentCard
from .style_rag import StyleRAG
from .context_rag import ContextRAG

# 可选模块（可能未安装依赖）
try:
    from .vector_store import VectorStore
except ImportError:
    VectorStore = None

try:
    from .query_parser import QueryParser, get_query_parser
except ImportError:
    QueryParser = None
    get_query_parser = None

try:
    from .reranker import Reranker, get_reranker
except ImportError:
    Reranker = None
    get_reranker = None

__all__ = [
    'MomentStorage',
    'MomentManager',
    'generate_moment_card',
    'MomentCard',
    'StyleRAG',
    'ContextRAG',
    'VectorStore',
    'QueryParser',
    'get_query_parser',
    'Reranker',
    'get_reranker'
]
