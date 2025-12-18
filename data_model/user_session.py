"""
User Session 数据模型
负责：管理当前会话的状态和历史
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class Message:
    """单条消息"""
    role: str           # "user" 或 "assistant"
    content: str        # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)
    emotion: str = ""   # 如果是用户消息，记录识别到的情绪
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "emotion": self.emotion
        }

@dataclass
class UserSession:
    """
    用户会话数据类
    管理当前对话的所有状态
    """
    
    user_name: str = "Irene"           # 用户昵称
    kay_name: str = "Kay"              # AI 名字
    
    # 对话历史
    messages: List[Message] = field(default_factory=list)
    
    # 会话元数据
    session_start: datetime = field(default_factory=datetime.now)
    turn_count: int = 0                # 对话轮数
    
    # 封存相关
    moments_created: int = 0           # 已封存的 Moment 数量
    
    def add_message(self, role: str, content: str, emotion: str = ""):
        """添加一条消息到历史"""
        msg = Message(role=role, content=content, emotion=emotion)
        self.messages.append(msg)
        
        # 如果是用户消息，增加对话轮数
        if role == "user":
            self.turn_count += 1
    
    def get_recent_messages(self, n: int = 6) -> List[Message]:
        """获取最近的 n 条消息"""
        return self.messages[-n:]
    
    def get_conversation_history(self) -> str:
        """
        获取格式化的对话历史
        用于传递给 LLM
        """
        history = []
        for msg in self.get_recent_messages():
            prefix = self.user_name if msg.role == "user" else self.kay_name
            history.append(f"{prefix}: {msg.content}")
        
        return "\n".join(history)
    
    def should_suggest_moment(self) -> bool:
        """
        判断是否应该弹出"封存"按钮
        规则：至少 3 轮对话后
        """
        return self.turn_count >= 3
    
    def reset_conversation(self):
        """重置对话（但保留用户名等基本信息）"""
        self.messages = []
        self.turn_count = 0
        self.session_start = datetime.now()