"""
Moment Manager - Moment 会话管理
负责创建、管理、保存 Moment 会话
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class MomentManager:
    """
    Moment 会话管理器
    
    功能：
    1. 创建新 Moment
    2. 添加对话消息
    3. 保存 Moment
    4. 加载历史 Moments
    5. 多用户数据隔离
    """
    
    def __init__(self, user_id: str = None, base_storage_dir: str = "storage/moments"):
        """
        初始化 Moment Manager
        
        Args:
            user_id: 用户唯一标识（格式：username_agentname）
            base_storage_dir: 基础存储目录
        """
        self.user_id = user_id or "default_user"
        self.base_storage_dir = Path(base_storage_dir)
        
        # 用户专属文件夹
        self.storage_dir = self.base_storage_dir / self.user_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_moment_id = None
        self.current_messages = []
        
        print(f"📁 Moment Manager 初始化：用户 ID = {self.user_id}")
    
    def set_user_id(self, user_name: str, agent_name: str):
        """
        设置用户 ID（用户名_Agent名）
        
        Args:
            user_name: 用户名
            agent_name: Agent 名
        """
        # 生成唯一用户 ID
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        
        # 更新存储目录
        self.storage_dir = self.base_storage_dir / self.user_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 用户 ID 更新：{self.user_id}")
        print(f"📁 存储目录：{self.storage_dir}")
        
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
        
        Returns:
            Dict: Moment 数据
        """
        if not self.current_moment_id:
            raise ValueError("没有活跃的 Moment")
        
        # 提取结构化信息（用于精准检索）
        # ⚠️ 重要：只从用户消息中提取，不包含Agent回复
        print("🔍 正在提取结构化信息...")
        user_messages_only = [msg for msg in self.current_messages if msg['role'] == 'user']
        entities = self._extract_structured_info(user_messages_only)
        
        # 构建 Moment 数据
        moment_data = {
            "moment_id": self.current_moment_id,
            "timestamp": datetime.now().isoformat(),
            "messages": self.current_messages,
            "message_count": len(self.current_messages),
            "summary": None,  # 等 Moment Card 生成时填充
            "emotion_tag": None,
            "card_generated": False,
            "entities": entities  # 新增：结构化信息
        }
        
        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        moment_file = self.storage_dir / f"{self.current_moment_id}.json"
        with open(moment_file, 'w', encoding='utf-8') as f:
            json.dump(moment_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Moment 已保存: {moment_file}")
        print(f"   共 {len(self.current_messages)} 条消息")
        print(f"   结构化信息：{entities}\n")
        
        # 重置当前状态
        saved_moment_id = self.current_moment_id
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
        moment_file = self.storage_dir / f"{moment_id}.json"
        
        if not moment_file.exists():
            print(f"⚠️  Moment 不存在: {moment_id}")
            return None
        
        with open(moment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_moments(self) -> List[Dict]:
        """
        获取所有 Moments（按时间倒序）
        
        Returns:
            List[Dict]: Moment 列表
        """
        moments = []
        
        for moment_file in self.storage_dir.glob("moment_*.json"):
            with open(moment_file, 'r', encoding='utf-8') as f:
                moment = json.load(f)
                moments.append(moment)
        
        # 按时间倒序排序（最新的在前）
        moments.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return moments
    
    def update_moment(self, moment_id: str, updates: Dict):
        """
        更新 Moment 数据（例如添加 Moment Card）
        
        Args:
            moment_id: Moment ID
            updates: 要更新的字段
        """
        moment_file = self.storage_dir / f"{moment_id}.json"
        
        if not moment_file.exists():
            raise ValueError(f"Moment 不存在: {moment_id}")
        
        # 加载现有数据
        with open(moment_file, 'r', encoding='utf-8') as f:
            moment_data = json.load(f)
        
        # 更新
        moment_data.update(updates)
        
        # 保存
        with open(moment_file, 'w', encoding='utf-8') as f:
            json.dump(moment_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Moment 已更新: {moment_id}")
    
    def get_moment_count(self) -> int:
        """获取 Moment 总数"""
        return len(list(self.storage_dir.glob("moment_*.json")))
    
    def delete_moment(self, moment_id: str):
        """删除 Moment"""
        moment_file = self.storage_dir / f"{moment_id}.json"
        
        if moment_file.exists():
            moment_file.unlink()
            print(f"🗑️  Moment 已删除: {moment_id}")
        else:
            print(f"⚠️  Moment 不存在: {moment_id}")
    
    def _extract_structured_info(self, messages: List[Dict]) -> Dict:
        """
        从对话中提取结构化信息（用于精准检索）
        
        Args:
            messages: 对话消息列表
        
        Returns:
            Dict: 结构化信息 {people, places, time_markers, numbers, events}
        """
        # 构建对话文本（只提取用户消息，不包含Agent回复）
        # ⚠️ 重要：entities应该只从用户的实际输入中提取，不应该从Agent的回复中提取
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        conversation = ""
        for msg in user_messages:
            conversation += f"用户: {msg['content']}\n"
        
        # 使用 LLM 提取结构化信息
        try:
            from openai import OpenAI
            from config.api_config import APIConfig
            
            client = OpenAI(
                api_key=APIConfig.QWEN_API_KEY,
                base_url=APIConfig.QWEN_BASE_URL
            )
            
            prompt = f"""从以下用户消息中提取关键实体信息，用于后续精准检索。

⚠️ **极其重要**：
- **只从用户消息中提取**，不要从Agent回复中提取
- **只提取用户明确提到的内容**，不要推测或编造
- **如果用户没有提到，就不要提取**

用户消息：
{conversation}

⚠️ **关键要求：提取完整、精确的信息，包含所有修饰词和属性**

请提取以下信息，以 JSON 格式返回：
{{
  "people": {{
    "人名1": {{"role": "关系/身份", "attributes": ["特征1", "特征2"]}},
    "人名2": {{"role": "关系/身份", "attributes": []}}
  }},
  "places": {{
    "地点1": {{"type": "类型", "position": "具体位置"}},
    "地点2": {{"type": "类型", "position": ""}}
  }},
  "time_info": {{
    "daily_routines": ["完整时间表达1", "完整时间表达2"],  // 日常习惯时间（如"周二早上五点多起床"）
    "time_markers": ["时间1", "时间2"]  // 其他时间（如"昨天"、"20分钟"）
  }},
  "objects": {{
    "物品1": {{"color": "颜色", "type": "类型", "description": "完整描述（包含所有细节）"}},
    "物品2": {{"color": "", "type": "类型", "description": ""}}
  }},
  "habits": ["习惯1", "习惯2"],  // 用户的日常习惯（如"给刘叔多加汤"）
  "events": ["事件1", "事件2"]  // 关键事件
}}

**提取规则（极其重要）：**

1. **时间信息必须完整**：
   - ✅ "周二早上五点多起床" （不要拆成"周二"+"五点"）
   - ✅ "周三下午" 
   - ❌ "周二" （太模糊）

2. **物品必须包含颜色/材质等属性，description要包含完整信息**：
   - ✅ {{"保温杯": {{"color": "蓝色", "type": "保温杯", "description": "蓝色保温杯，喝热水用"}}}}
   - ✅ {{"方案": {{"color": "", "type": "设计方案", "description": "亮橙色配灰底"}}}}
   - ✅ {{"咖啡": {{"color": "", "type": "饮料", "description": "桂花拿铁，甜到皱眉"}}}}
   - ❌ {{"保温杯": {{"type": "保温杯"}}}} （缺少颜色和描述）

3. **设计/方案类信息要完整提取**：
   - 如果提到"配色"、"方案"、"设计"，必须在objects中记录
   - description要包含完整的配色信息，如"亮橙色配灰底"
   - ✅ {{"方案": {{"type": "设计方案", "description": "亮橙色配灰底"}}}}
   - ✅ {{"配色": {{"type": "配色方案", "description": "亮橙色配灰底"}}}}

4. **食物/饮料类信息要完整提取**：
   - 如果提到"咖啡"、"拿铁"、"饮料"，必须在objects中记录
   - description要包含完整的名称和特征，如"桂花拿铁，甜到皱眉"
   - ✅ {{"咖啡": {{"type": "饮料", "description": "桂花拿铁"}}}}
   - ✅ {{"拿铁": {{"type": "咖啡", "description": "桂花拿铁，甜到皱眉"}}}}

5. **地点必须包含位置信息（极其重要）**：
   - ✅ {{"二食堂": {{"type": "食堂", "position": "学校"}}}} （完整地点）
   - ✅ {{"图书馆": {{"type": "学习地点", "position": "三楼靠窗的位置"}}}} （具体位置）
   - ✅ {{"刘叔的座位": {{"type": "座位", "position": "靠窗那张"}}}}
   - ❌ {{"食堂": {{"type": "食堂"}}}} （缺少具体位置，应该是"二食堂"）
   - ❌ {{"座位": {{"type": "座位"}}}} （缺少位置）

6. **食物/饮料类信息要完整提取（重要）**：
   - 如果提到"面"、"饭"、"咖啡"、"饮料"等，必须在objects中记录
   - description要包含完整的名称和特征
   - ✅ {{"番茄牛腩面": {{"type": "食物", "description": "一整碗番茄牛腩面"}}}}
   - ✅ {{"拿铁": {{"type": "咖啡", "description": "桂花拿铁，甜到皱眉"}}}}
   - ❌ {{"面": {{"type": "食物"}}}} （缺少完整名称，应该是"番茄牛腩面"）

7. **衣服类信息要完整提取（重要）**：
   - 如果提到"衣服"、"卫衣"、"T恤"等，必须在objects中记录
   - color和description都要包含完整信息
   - ✅ {{"白色卫衣": {{"color": "白色", "type": "衣服", "description": "白色卫衣"}}}}
   - ✅ {{"红色T恤": {{"color": "红色", "type": "衣服", "description": "红色T恤"}}}}
   - ❌ {{"卫衣": {{"type": "衣服"}}}} （缺少颜色，应该是"白色卫衣"）

8. **人物必须包含关系**：
   - ✅ {{"刘叔": {{"role": "常客", "attributes": ["坐靠窗", "总来吃面"]}}}}
   - ❌ {{"刘叔": {{"role": "顾客"}}}} （太模糊）

9. **日常习惯要完整记录**：
   - ✅ "给刘叔多加汤"
   - ✅ "周二早上五点多起床"
   - ✅ "擦台面三遍"

10. **只提取明确出现的内容，不推测**

11. **如果某类信息没有，返回空对象{{}}或空列表[]**

12. **只返回 JSON，不要任何其他文字**

⚠️ **特别强调**：
- **地点**：必须提取完整地点名称（如"二食堂"、"图书馆三楼"），不要只提取"食堂"、"图书馆"
- **食物**：必须提取完整食物名称（如"番茄牛腩面"、"桂花拿铁"），不要只提取"面"、"咖啡"
- **衣服**：必须包含颜色和完整名称（如"白色卫衣"），不要只提取"卫衣"
- **物品**：必须包含颜色和完整描述（如"红色U盘"），不要只提取"U盘"

例子1：
对话："周二早上五点多就起了，后厨有点冷，我用那个蓝色保温杯喝了两口热水"
返回：
{{
  "people": {{}},
  "places": {{"后厨": {{"type": "工作地点", "position": ""}}}},
  "time_info": {{
    "daily_routines": ["周二早上五点多起床"],
    "time_markers": []
  }},
  "objects": {{
    "保温杯": {{"color": "蓝色", "type": "保温杯", "description": "蓝色保温杯，喝热水用"}}
  }},
  "habits": [],
  "events": ["起床"]
}}

例子2：
对话："今天在公司第一次自己提方案，用的是亮橙色配灰底，被主管当场点名夸了一句"
返回：
{{
  "people": {{}},
  "places": {{"公司": {{"type": "工作地点", "position": ""}}}},
  "time_info": {{
    "daily_routines": [],
    "time_markers": []
  }},
  "objects": {{
    "方案": {{"type": "设计方案", "description": "亮橙色配灰底"}}
  }},
  "habits": [],
  "events": ["提方案", "被夸"]
}}

例子3：
对话："下班路上我还去买了杯桂花拿铁，结果忘了跟老板说少糖，甜到我一路皱眉喝完"
返回：
{{
  "people": {{}},
  "places": {{}},
  "time_info": {{
    "daily_routines": [],
    "time_markers": []
  }},
  "objects": {{
    "拿铁": {{"type": "咖啡", "description": "桂花拿铁，甜到皱眉"}}
  }},
  "habits": [],
  "events": ["买咖啡"]
}}

例子4（重要：地点+食物+衣服）：
对话："中午在学校二食堂，我把一整碗番茄牛腩面直接洒在自己白色卫衣上，当场裂开。"
返回：
{{
  "people": {{}},
  "places": {{
    "二食堂": {{"type": "食堂", "position": "学校"}}
  }},
  "time_info": {{
    "daily_routines": [],
    "time_markers": ["中午"]
  }},
  "objects": {{
    "番茄牛腩面": {{"type": "食物", "description": "一整碗番茄牛腩面"}},
    "白色卫衣": {{"color": "白色", "type": "衣服", "description": "白色卫衣"}}
  }},
  "habits": [],
  "events": ["洒面", "社死"]
}}

例子5（地点+物品）：
对话："今天下午我还去图书馆三楼靠窗的位置自习，结果把红色的U盘落在那儿了"
返回：
{{
  "people": {{}},
  "places": {{
    "图书馆": {{"type": "学习地点", "position": "三楼靠窗的位置"}}
  }},
  "time_info": {{
    "daily_routines": [],
    "time_markers": ["今天下午"]
  }},
  "objects": {{
    "U盘": {{"color": "红色", "type": "物品", "description": "红色U盘"}}
  }},
  "habits": [],
  "events": ["自习", "落东西"]
}}"""

            response = client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # 低温度，减少创造性
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 调试：打印原始结果
            print(f"   📊 LLM返回原始结果（前200字符）: {result_text[:200]}")
            
            # 移除可能的 markdown 标记
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
            except json.JSONDecodeError as e:
                print(f"   ⚠️  JSON解析失败: {e}")
                print(f"   尝试解析的文本: {result_text[:500]}")
                # 尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        entities = json.loads(json_match.group())
                        print(f"   ✅ 从文本中提取JSON成功")
                    except:
                        raise e
                else:
                    raise e
            
            # 确保所有字段存在
            default_entities = {
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
            
            # 深度合并
            for key in default_entities:
                if key in entities:
                    if isinstance(default_entities[key], dict):
                        default_entities[key].update(entities[key])
                    elif isinstance(default_entities[key], list):
                        default_entities[key] = entities[key]
            
            return default_entities
            
        except Exception as e:
            print(f"   ⚠️  结构化信息提取失败: {e}")
            # 返回空结构
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



# ============================================================
# 测试代码
# ============================================================

def test_moment_manager():
    """测试 Moment Manager"""
    
    print("\n" + "="*60)
    print("🧪 测试 Moment Manager")
    print("="*60 + "\n")
    
    manager = MomentManager()
    
    # 测试1: 创建第一个 Moment
    print("📝 测试1: 创建 Moment 1")
    manager.start_new_moment()
    manager.add_message("user", "我有个很难的 project，不知道能不能做成", "worry")
    manager.add_message("assistant", "听起来是个很有挑战的项目。能跟我说说具体是什么样的 project 吗？", "neutral")
    manager.add_message("user", "是一个 AI Agent 项目，技术栈很复杂", "neutral")
    manager.add_message("assistant", "嗯，AI Agent 确实挺复杂的。不过我相信你能搞定的。", "supportive")
    moment1 = manager.end_moment()
    
    # 测试2: 创建第二个 Moment
    print("📝 测试2: 创建 Moment 2")
    manager.start_new_moment()
    manager.add_message("user", "今天心情不太好", "sadness")
    manager.add_message("assistant", "发生什么事了吗？", "neutral")
    moment2 = manager.end_moment()
    
    # 测试3: 加载 Moment
    print("📝 测试3: 加载 Moment")
    loaded = manager.load_moment(moment1['moment_id'])
    print(f"   加载成功: {loaded['moment_id']}")
    print(f"   消息数: {loaded['message_count']}")
    
    # 测试4: 获取所有 Moments
    print("\n📝 测试4: 获取所有 Moments")
    all_moments = manager.get_all_moments()
    print(f"   共 {len(all_moments)} 个 Moments:")
    for m in all_moments:
        print(f"   - {m['moment_id']}: {m['message_count']} 条消息")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_moment_manager()