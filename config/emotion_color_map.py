"""
情绪-颜色映射配置
负责：定义情绪对应的颜色和 emoji
用于：Moment Card 标签、3D 星空渲染
"""

# 情绪分类和对应的视觉元素
EMOTION_COLOR_MAP = {
    # 积极情绪
    "开心": {
        "color": "#FFD700",      # 金黄色
        "emoji": "😊",
        "nebula_color": (255, 215, 0),  # RGB for 3D
        "description": "快乐、愉悦"
    },
    "兴奋": {
        "color": "#FF6B6B",      # 亮红色
        "emoji": "🎉",
        "nebula_color": (255, 107, 107),
        "description": "激动、狂喜"
    },
    "平静": {
        "color": "#87CEEB",      # 天蓝色
        "emoji": "😌",
        "nebula_color": (135, 206, 235),
        "description": "宁静、放松"
    },
    "感动": {
        "color": "#FFB6C1",      # 粉色
        "emoji": "🥺",
        "nebula_color": (255, 182, 193),
        "description": "温暖、触动"
    },
    
    # 消极情绪
    "难过": {
        "color": "#4682B4",      # 深蓝色
        "emoji": "😢",
        "nebula_color": (70, 130, 180),
        "description": "伤心、失落"
    },
    "焦虑": {
        "color": "#9370DB",      # 紫色
        "emoji": "😰",
        "nebula_color": (147, 112, 219),
        "description": "不安、紧张"
    },
    "疲惫": {
        "color": "#808080",      # 灰色
        "emoji": "😔",
        "nebula_color": (128, 128, 128),
        "description": "累、倦怠"
    },
    "愤怒": {
        "color": "#DC143C",      # 深红色
        "emoji": "😠",
        "nebula_color": (220, 20, 60),
        "description": "生气、不满"
    },
    
    # 中性/复杂情绪
    "困惑": {
        "color": "#DAA520",      # 金棕色
        "emoji": "🤔",
        "nebula_color": (218, 165, 32),
        "description": "迷茫、不确定"
    },
    "期待": {
        "color": "#00CED1",      # 青色
        "emoji": "✨",
        "nebula_color": (0, 206, 209),
        "description": "希望、憧憬"
    },
    "平淡": {
        "color": "#D3D3D3",      # 浅灰色
        "emoji": "😐",
        "nebula_color": (211, 211, 211),
        "description": "无特殊感觉"
    }
}

# 默认情绪（识别失败时使用）
DEFAULT_EMOTION = "平淡"

def get_emotion_info(emotion: str) -> dict:
    """
    获取情绪的完整信息
    
    Args:
        emotion: 情绪名称
        
    Returns:
        包含颜色、emoji 等信息的字典
    """
    return EMOTION_COLOR_MAP.get(emotion, EMOTION_COLOR_MAP[DEFAULT_EMOTION])

def get_all_emotions() -> list:
    """获取所有支持的情绪列表"""
    return list(EMOTION_COLOR_MAP.keys())