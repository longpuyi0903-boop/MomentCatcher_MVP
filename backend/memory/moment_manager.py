"""
Moment Manager - Moment 会话管理（V3 混合检索版）

改进点：
1. SQLite 存储（V2）
2. 写入异步化（V2）
3. 向量存储同步写入（V3 新增）
4. 保持 API 兼容性
"""

import json
import uuid
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

# 导入存储层
from .moment_storage import MomentStorage

# 导入向量存储层
try:
    from .vector_store import VectorStore
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    print("⚠️ VectorStore 未导入，向量功能不可用")


class MomentManager:
    """
    Moment 会话管理器（V3）
    
    改进：
    1. SQLite 存储替代 JSON 文件遍历
    2. 异步实体提取（用户无感知）
    3. 向量存储同步写入（语义检索支持）
    4. 保持 API 兼容
    """
    
    def __init__(self, user_id: str = None, base_storage_dir: str = "storage"):
        """
        初始化 Moment Manager
        
        Args:
            user_id: 用户唯一标识
            base_storage_dir: 基础存储目录
        """
        self.user_id = user_id or "default_user"
        self.base_storage_dir = Path(base_storage_dir)
        
        # 使用 SQLite 存储
        self.storage = MomentStorage(
            user_id=self.user_id,
            base_dir=str(self.base_storage_dir)
        )
        
        # 使用向量存储
        if VECTOR_AVAILABLE:
            self.vector_store = VectorStore(
                user_id=self.user_id,
                base_dir=str(self.base_storage_dir)
            )
        else:
            self.vector_store = None
        
        # 当前会话状态
        self.current_moment_id = None
        self.current_messages = []
        
        # 异步任务线程池
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="moment_")
        
        # 兼容旧代码：保留 storage_dir 属性
        self.storage_dir = self.base_storage_dir / "moments" / self.user_id
        
        print(f"📁 Moment Manager V3 初始化：用户 ID = {self.user_id}")
        if self.vector_store:
            print(f"   🔮 向量存储已启用")
    
    def set_user_id(self, user_name: str, agent_name: str):
        """
        设置用户 ID
        
        Args:
            user_name: 用户名
            agent_name: Agent 名
        """
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        
        # 更新存储层
        self.storage.set_user_id(user_name, agent_name)
        
        # 更新向量存储
        if self.vector_store:
            self.vector_store.set_user_id(user_name, agent_name)
        
        # 兼容旧代码
        self.storage_dir = self.base_storage_dir / "moments" / self.user_id
        
        print(f"📁 用户 ID 更新：{self.user_id}")
    
    def start_new_moment(self) -> str:
        """
        开始新的 Moment 会话
        
        Returns:
            str: moment_id
        """
        self.current_moment_id = f"moment_{uuid.uuid4().hex[:8]}"
        self.current_messages = []
        
        print(f"\n✨ 开始新 Moment: {self.current_moment_id}")
        return self.current_moment_id
    
    def add_message(self, role: str, content: str, emotion: str = "neutral"):
        """
        添加对话消息到当前 Moment
        
        Args:
            role: 'user' 或 'assistant'
            content: 消息内容
            emotion: 情绪标签
        """
        if not self.current_moment_id:
            raise ValueError("请先调用 start_new_moment() 开始新 Moment")
        
        message = {
            "role": role,
            "content": content,
            "emotion": emotion,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_messages.append(message)
        print(f"  📝 添加消息: {role} - {content[:30]}...")
    
    def end_moment(self) -> Dict:
        """
        结束当前 Moment，保存到存储
        
        改进：
        1. 立即保存原始对话到 SQLite（用户无感知）
        2. 异步提取实体并更新
        3. 异步写入向量存储
        
        Returns:
            Dict: Moment 数据
        """
        if not self.current_moment_id:
            raise ValueError("没有活跃的 Moment")
        
        # 构建 Moment 数据（先不含实体）
        moment_data = {
            "moment_id": self.current_moment_id,
            "timestamp": datetime.now().isoformat(),
            "messages": self.current_messages.copy(),
            "message_count": len(self.current_messages),
            "summary": None,
            "emotion_tag": None,
            "card_generated": False,
            "entities": {}  # 先设为空，异步填充
        }
        
        # 立即保存到 SQLite（用户无感知）
        print("💾 Moment 保存中...")
        self.storage.save_moment(moment_data)
        print(f"💾 Moment 已保存: {moment_data['moment_id']}")
        print(f"   共 {len(self.current_messages)} 条消息")
        
        # 保存当前状态用于异步任务
        user_messages = [msg for msg in self.current_messages if msg['role'] == 'user']
        moment_id = self.current_moment_id
        moment_data_copy = moment_data.copy()
        
        # 异步任务：提取实体 + 写入向量
        def async_process():
            try:
                # 1. 提取结构化实体
                print(f"🔍 [异步] 开始提取实体: {moment_id}")
                entities = self._extract_structured_info(user_messages)
                self.storage.update_moment_entities(moment_id, entities)
                print(f"🔍 [异步] 实体提取完成: {moment_id}")
                print(f"   结构化信息：{json.dumps(entities, ensure_ascii=False)[:200]}...")
                
                # 2. 写入向量存储
                if self.vector_store:
                    print(f"🔮 [异步] 开始写入向量: {moment_id}")
                    # 更新 moment_data 的 entities 用于向量化
                    moment_data_copy["entities"] = entities
                    self.vector_store.add_moment(moment_id, moment_data_copy)
                    print(f"🔮 [异步] 向量写入完成: {moment_id}")
                    
            except Exception as e:
                print(f"⚠️ [异步] 处理失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 提交异步任务
        self._executor.submit(async_process)
        
        # 重置当前状态
        self.current_moment_id = None
        self.current_messages = []
        
        return moment_data
    
    def load_moment(self, moment_id: str) -> Optional[Dict]:
        """
        加载指定的 Moment
        
        Args:
            moment_id: Moment ID
        
        Returns:
            Dict: Moment 数据，如果不存在返回 None
        """
        return self.storage.get_moment(moment_id)
    
    def get_all_moments(self) -> List[Dict]:
        """
        获取所有 Moments（按时间倒序）
        
        Returns:
            List[Dict]: Moment 列表
        """
        return self.storage.get_all_moments()
    
    def update_moment(self, moment_id: str, updates: Dict):
        """
        更新 Moment 数据
        
        Args:
            moment_id: Moment ID
            updates: 要更新的字段
        """
        self.storage.update_moment(moment_id, updates)
        
        # 如果更新了 summary，也更新向量
        if self.vector_store and 'summary' in updates:
            moment = self.storage.get_moment(moment_id)
            if moment:
                self.vector_store.add_moment(moment_id, moment)
        
        print(f"✅ Moment 已更新: {moment_id}")
    
    def get_moment_count(self) -> int:
        """获取 Moment 总数"""
        return self.storage.get_moment_count()
    
    def delete_moment(self, moment_id: str):
        """删除 Moment"""
        # 删除 SQLite 记录
        if self.storage.delete_moment(moment_id):
            print(f"🗑️  Moment 已删除: {moment_id}")
            
            # 删除向量记录
            if self.vector_store:
                self.vector_store.delete_moment(moment_id)
        else:
            print(f"⚠️  Moment 不存在: {moment_id}")
    
    def get_vector_stats(self) -> Dict:
        """获取向量存储统计"""
        if self.vector_store:
            return self.vector_store.get_stats()
        return {"status": "unavailable"}
    
    def _extract_structured_info(self, messages: List[Dict]) -> Dict:
        """
        从对话中提取结构化信息（用于精准检索）
        
        Args:
            messages: 对话消息列表（仅用户消息）
        
        Returns:
            Dict: 结构化信息
        """
        # 构建对话文本
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        conversation = ""
        for msg in user_messages:
            conversation += f"用户: {msg['content']}\n"
        
        if not conversation.strip():
            return self._get_empty_entities()
        
        # 使用 LLM 提取结构化信息
        try:
            from openai import OpenAI
            
            # 尝试多种方式获取 API 配置
            import os
            api_key = os.getenv("ALIYUN_QWEN_KEY")
            if not api_key:
                try:
                    from config.api_config import APIConfig
                    api_key = APIConfig.QWEN_API_KEY
                except:
                    pass
            
            if not api_key:
                print("   ⚠️  未配置 QWEN API KEY")
                return self._get_empty_entities()
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            prompt = self._get_extraction_prompt(conversation)
            
            response = client.chat.completions.create(
                model="qwen-turbo",  # 用 turbo 更快
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 移除 markdown 标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 解析 JSON
            try:
                entities = json.loads(result_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    entities = json.loads(json_match.group())
                else:
                    return self._get_empty_entities()
            
            # 确保所有字段存在
            return self._merge_with_default(entities)
            
        except Exception as e:
            print(f"   ⚠️  结构化信息提取失败: {e}")
            return self._get_empty_entities()
    
    def _get_empty_entities(self) -> Dict:
        """返回空的实体结构"""
        return {
            "people": {},
            "places": {},
            "time_info": {
                "daily_routines": [],
                "time_markers": []
            },
            "objects": {},
            "habits": [],
            "events": []
        }
    
    def _merge_with_default(self, entities: Dict) -> Dict:
        """合并实体与默认结构"""
        default = self._get_empty_entities()
        
        for key in default:
            if key in entities:
                if isinstance(default[key], dict):
                    default[key].update(entities[key])
                elif isinstance(default[key], list):
                    default[key] = entities[key]
        
        return default
    
    def _get_extraction_prompt(self, conversation: str) -> str:
        """获取实体提取的 Prompt"""
        return f"""从以下用户消息中提取关键实体信息，用于后续精准检索。

⚠️ **极其重要**：
- **只从用户消息中提取**，不要从Agent回复中提取
- **只提取用户明确提到的内容**，不要推测或编造
- **如果用户没有提到，就不要提取**

用户消息：
{conversation}

请提取以下信息，以 JSON 格式返回：
{{
  "people": {{
    "人名1": {{"role": "关系/身份", "attributes": ["特征1", "特征2"]}}
  }},
  "places": {{
    "地点1": {{"type": "类型", "position": "具体位置"}}
  }},
  "time_info": {{
    "daily_routines": ["完整时间表达1"],
    "time_markers": ["时间1"]
  }},
  "objects": {{
    "物品1": {{"color": "颜色", "type": "类型", "description": "完整描述"}}
  }},
  "habits": ["习惯1"],
  "events": ["事件1"]
}}

⚠️ **关键要求**：
1. 物品必须包含完整描述（颜色、类型、特征）
2. 地点必须包含位置信息
3. 食物/饮料要完整提取名称和特征
4. 只提取明确出现的内容，不推测
5. 如果某类信息没有，返回空对象{{}}或空列表[]
6. 只返回 JSON，不要任何其他文字"""
    
    def shutdown(self):
        """关闭管理器，等待异步任务完成"""
        print("🔄 等待异步任务完成...")
        self._executor.shutdown(wait=True)
        print("✅ Moment Manager 已关闭")


# ============================================================
# 测试代码
# ============================================================

def test_moment_manager():
    """测试 Moment Manager V3"""
    
    print("\n" + "="*60)
    print("🧪 测试 Moment Manager V3 (混合检索)")
    print("="*60 + "\n")
    
    manager = MomentManager(base_storage_dir="storage/test")
    
    # 测试1: 创建 Moment
    print("📝 测试1: 创建 Moment")
    manager.start_new_moment()
    manager.add_message("user", "今天在公司被主管夸了，方案用的是亮橙色配灰底", "joy")
    manager.add_message("assistant", "太棒了！被夸的感觉一定很开心", "neutral")
    manager.add_message("user", "是啊，下班还买了杯桂花拿铁庆祝", "joy")
    moment1 = manager.end_moment()
    
    # 等待异步任务
    import time
    print("\n⏳ 等待异步处理（实体提取 + 向量写入）...")
    time.sleep(5)
    
    # 测试2: 查询
    print("\n📝 测试2: 查询 Moment")
    loaded = manager.load_moment(moment1['moment_id'])
    if loaded:
        print(f"   ✅ 加载成功: {loaded['moment_id']}")
        print(f"   实体: {json.dumps(loaded.get('entities', {}), ensure_ascii=False)[:200]}")
    
    # 测试3: 向量统计
    print("\n📝 测试3: 向量统计")
    stats = manager.get_vector_stats()
    print(f"   {stats}")
    
    # 测试4: 获取所有
    print("\n📝 测试4: 获取所有 Moments")
    all_moments = manager.get_all_moments()
    print(f"   共 {len(all_moments)} 个 Moments")
    
    # 关闭
    manager.shutdown()
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_moment_manager()
