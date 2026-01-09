"""
Vector Store - 向量存储层
使用 ChromaDB + 阿里云 text-embedding-v3

功能：
1. 文本向量化（阿里云 Embedding API）
2. 向量存储（ChromaDB 本地持久化）
3. 语义检索（相似度搜索）
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB 未安装，请运行: pip install chromadb")

# 阿里云 Embedding API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI SDK 未安装，请运行: pip install openai")


class VectorStore:
    """
    向量存储层
    
    特性：
    1. 阿里云 text-embedding-v3 生成向量
    2. ChromaDB 本地持久化存储
    3. 支持语义相似度检索
    4. 多用户数据隔离
    """
    
    # Embedding 配置
    EMBEDDING_MODEL = "text-embedding-v3"
    EMBEDDING_DIMENSION = 1024  # text-embedding-v3 默认维度
    
    def __init__(self, user_id: str = "default_user", base_dir: str = "storage"):
        """
        初始化向量存储
        
        Args:
            user_id: 用户唯一标识
            base_dir: 基础存储目录
        """
        self.user_id = user_id
        self.base_dir = Path(base_dir)
        self.vector_dir = self.base_dir / "vectors"
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Embedding 客户端
        self._init_embedding_client()
        
        # 初始化 ChromaDB
        self._init_chromadb()
        
        print(f"🔮 VectorStore 初始化: user={user_id}, dir={self.vector_dir}")
    
    def _init_embedding_client(self):
        """初始化阿里云 Embedding 客户端"""
        if not OPENAI_AVAILABLE:
            self.embedding_client = None
            return
        
        api_key = os.getenv("ALIYUN_QWEN_KEY")
        if not api_key:
            try:
                from config.api_config import APIConfig
                api_key = APIConfig.QWEN_API_KEY
            except:
                pass
        
        if api_key:
            self.embedding_client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            print("   ✅ Embedding 客户端已初始化")
        else:
            self.embedding_client = None
            print("   ⚠️ 未配置 API Key，Embedding 功能不可用")
    
    def _init_chromadb(self):
        """初始化 ChromaDB"""
        if not CHROMADB_AVAILABLE:
            self.chroma_client = None
            self.collection = None
            return
        
        # 持久化存储路径
        persist_path = str(self.vector_dir / "chromadb")
        
        # 创建客户端（持久化模式）
        self.chroma_client = chromadb.PersistentClient(path=persist_path)
        
        # 获取或创建 Collection（按用户隔离）
        collection_name = f"moments_{self.user_id}".replace("-", "_")[:63]  # ChromaDB 名称限制
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
        
        print(f"   ✅ ChromaDB Collection: {collection_name} (共 {self.collection.count()} 条)")
    
    def set_user_id(self, user_name: str, agent_name: str):
        """切换用户"""
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        self._init_chromadb()  # 重新初始化 Collection
        print(f"🔮 VectorStore 切换用户: {self.user_id}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 向量，失败返回 None
        """
        if not self.embedding_client:
            print("   ⚠️ Embedding 客户端未初始化")
            return None
        
        if not text or not text.strip():
            return None
        
        try:
            response = self.embedding_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text,
                dimensions=self.EMBEDDING_DIMENSION
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            print(f"   ⚠️ Embedding 生成失败: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量获取向量（更高效）
        
        Args:
            texts: 文本列表
            
        Returns:
            List: 向量列表
        """
        if not self.embedding_client:
            return [None] * len(texts)
        
        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [None] * len(texts)
        
        try:
            response = self.embedding_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=valid_texts,
                dimensions=self.EMBEDDING_DIMENSION
            )
            
            # 构建结果映射
            embeddings_map = {}
            for i, data in enumerate(response.data):
                embeddings_map[valid_texts[i]] = data.embedding
            
            # 按原始顺序返回
            result = []
            for t in texts:
                if t and t.strip() and t in embeddings_map:
                    result.append(embeddings_map[t])
                else:
                    result.append(None)
            
            return result
            
        except Exception as e:
            print(f"   ⚠️ 批量 Embedding 生成失败: {e}")
            return [None] * len(texts)
    
    def add_moment(self, moment_id: str, moment_data: Dict) -> bool:
        """
        将 Moment 添加到向量库
        
        Args:
            moment_id: Moment ID
            moment_data: Moment 数据
            
        Returns:
            bool: 是否成功
        """
        if not self.collection:
            print("   ⚠️ ChromaDB 未初始化")
            return False
        
        try:
            # 1. 构建要向量化的文本
            texts_to_embed = []
            doc_ids = []
            metadatas = []
            
            # 提取用户消息
            messages = moment_data.get("messages", [])
            user_messages = [m["content"] for m in messages if m.get("role") == "user"]
            
            # 合并为一个文档（整个对话的语义）
            full_text = " ".join(user_messages)
            if full_text.strip():
                texts_to_embed.append(full_text)
                doc_ids.append(f"{moment_id}_full")
                metadatas.append({
                    "moment_id": moment_id,
                    "type": "full_conversation",
                    "timestamp": moment_data.get("timestamp", ""),
                    "message_count": len(messages)
                })
            
            # 每条用户消息单独向量化（细粒度检索）
            for i, msg in enumerate(user_messages):
                if len(msg.strip()) > 10:  # 过滤太短的消息
                    texts_to_embed.append(msg)
                    doc_ids.append(f"{moment_id}_msg_{i}")
                    metadatas.append({
                        "moment_id": moment_id,
                        "type": "single_message",
                        "message_index": i,
                        "timestamp": moment_data.get("timestamp", "")
                    })
            
            # 摘要（如果有）
            summary = moment_data.get("summary")
            if summary and summary.strip():
                texts_to_embed.append(summary)
                doc_ids.append(f"{moment_id}_summary")
                metadatas.append({
                    "moment_id": moment_id,
                    "type": "summary",
                    "timestamp": moment_data.get("timestamp", "")
                })
            
            if not texts_to_embed:
                return False
            
            # 2. 批量生成向量
            embeddings = self.get_embeddings_batch(texts_to_embed)
            
            # 3. 过滤掉失败的
            valid_docs = []
            valid_ids = []
            valid_embeddings = []
            valid_metadatas = []
            
            for text, doc_id, emb, meta in zip(texts_to_embed, doc_ids, embeddings, metadatas):
                if emb is not None:
                    valid_docs.append(text)
                    valid_ids.append(doc_id)
                    valid_embeddings.append(emb)
                    valid_metadatas.append(meta)
            
            if not valid_docs:
                print(f"   ⚠️ 所有文本向量化失败")
                return False
            
            # 4. 添加到 ChromaDB（upsert 模式，避免重复）
            self.collection.upsert(
                ids=valid_ids,
                documents=valid_docs,
                embeddings=valid_embeddings,
                metadatas=valid_metadatas
            )
            
            print(f"   ✅ 向量已添加: {moment_id} ({len(valid_docs)} 条)")
            return True
            
        except Exception as e:
            print(f"   ❌ 添加向量失败: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, 
               filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filter_dict: 过滤条件（ChromaDB where 语法）
            
        Returns:
            List[Dict]: 检索结果，包含 moment_id, score, text, metadata
        """
        if not self.collection:
            return []
        
        try:
            # 1. 获取查询向量
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                print("   ⚠️ 查询向量化失败")
                return []
            
            # 2. 检索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict,
                include=["documents", "metadatas", "distances"]
            )
            
            # 3. 整理结果
            output = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB 返回的是距离，转换为相似度分数
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1 - distance  # 余弦距离转相似度
                    
                    output.append({
                        "doc_id": doc_id,
                        "moment_id": results["metadatas"][0][i].get("moment_id", ""),
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "score": score,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            
            return output
            
        except Exception as e:
            print(f"   ❌ 向量检索失败: {e}")
            return []
    
    def delete_moment(self, moment_id: str) -> bool:
        """删除 Moment 的所有向量"""
        if not self.collection:
            return False
        
        try:
            # 查找该 moment_id 的所有文档
            results = self.collection.get(
                where={"moment_id": moment_id},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"   🗑️ 向量已删除: {moment_id} ({len(results['ids'])} 条)")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 删除向量失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.collection:
            return {"status": "unavailable"}
        
        return {
            "status": "ok",
            "user_id": self.user_id,
            "document_count": self.collection.count(),
            "embedding_model": self.EMBEDDING_MODEL,
            "embedding_dimension": self.EMBEDDING_DIMENSION
        }


# ============================================================
# 测试代码
# ============================================================

def test_vector_store():
    """测试向量存储"""
    print("\n" + "="*60)
    print("🧪 测试 VectorStore")
    print("="*60 + "\n")
    
    store = VectorStore(user_id="test_user", base_dir="storage/test")
    
    # 测试 Embedding
    print("📝 测试 Embedding...")
    emb = store.get_embedding("今天在公司被主管夸了")
    if emb:
        print(f"   ✅ 向量维度: {len(emb)}")
    else:
        print("   ❌ Embedding 失败")
        return
    
    # 测试添加 Moment
    print("\n📝 测试添加 Moment...")
    test_moment = {
        "moment_id": "test_moment_001",
        "timestamp": datetime.now().isoformat(),
        "messages": [
            {"role": "user", "content": "今天在公司被主管夸了，方案用的是亮橙色配灰底"},
            {"role": "assistant", "content": "太棒了！"},
            {"role": "user", "content": "下班还买了杯桂花拿铁庆祝"}
        ],
        "summary": "用户分享被主管夸奖的喜悦，庆祝买了桂花拿铁"
    }
    
    result = store.add_moment("test_moment_001", test_moment)
    print(f"   添加结果: {'✅ 成功' if result else '❌ 失败'}")
    
    # 测试检索
    print("\n📝 测试语义检索...")
    
    test_queries = [
        "咖啡",  # 精确词
        "被表扬",  # 同义词（向量应该能匹配"被夸"）
        "工作成果",  # 抽象概念
        "开心的事"  # 情感概念
    ]
    
    for query in test_queries:
        print(f"\n   🔍 查询: '{query}'")
        results = store.search(query, top_k=2)
        if results:
            for r in results:
                print(f"      📌 score={r['score']:.3f} | {r['text'][:50]}...")
        else:
            print("      未找到结果")
    
    # 统计
    print(f"\n📊 统计: {store.get_stats()}")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_vector_store()
