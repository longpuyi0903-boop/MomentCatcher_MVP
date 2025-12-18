"""
Moment Card 数据模型
负责：定义一个"瞬间"的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple

@dataclass
class MomentCard:
    """
    Moment Card 数据类
    代表用户封存的一个情感瞬间
    """
    
    # 基本信息
    text: str                          # 用户的原始对话内容
    emotion: str                       # 识别到的情绪
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 可选字段
    card_id: Optional[str] = None      # 唯一标识符
    custom_title: Optional[str] = None # 用户自定义标题（可选）
    
    # 3D 星空坐标（Level 3 使用）
    nebula_position: Optional[Tuple[float, float, float]] = None
    
    # 元数据
    conversation_context: list = field(default_factory=list)  # 对话上下文（用于 RAG）
    
    def to_dict(self) -> dict:
        """转换为字典格式（用于存储）"""
        return {
            "card_id": self.card_id,
            "text": self.text,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
            "custom_title": self.custom_title,
            "nebula_position": self.nebula_position,
            "conversation_context": self.conversation_context
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MomentCard':
        """从字典创建实例"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def get_display_text(self) -> str:
        """
        获取用于显示的文本
        如果有自定义标题，返回标题；否则返回文本摘要
        """
        if self.custom_title:
            return self.custom_title
        
        # 如果文本太长，截取前50个字符
        if len(self.text) > 50:
            return self.text[:50] + "..."
        
        return self.text
    
    def get_formatted_time(self) -> str:
        """获取格式化的时间字符串"""
        return self.timestamp.strftime("%Y年%m月%d日 %H:%M")