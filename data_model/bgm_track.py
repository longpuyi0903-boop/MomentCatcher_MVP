"""
BGM Track 数据模型
负责：定义背景音乐的数据结构（Level 2/4 使用）
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class BGMTrack:
    """
    BGM 音轨数据类
    代表一首背景音乐及其情绪标签
    """
    
    filename: str                      # 文件名（例如：lofi-calm.mp3）
    filepath: str                      # 完整文件路径
    emotion_tag: str                   # 情绪标签（由 AI 学习得出）
    
    # 可选字段
    title: Optional[str] = None        # 音乐标题
    duration: Optional[float] = None   # 时长（秒）
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "emotion_tag": self.emotion_tag,
            "title": self.title,
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BGMTrack':
        """从字典创建实例"""
        return cls(**data)
    
    def __repr__(self) -> str:
        return f"BGMTrack(filename={self.filename}, emotion={self.emotion_tag})"