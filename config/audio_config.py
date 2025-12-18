"""
音频配置
负责：TTS 声线、播放设置（Level 2 实现）
"""

# TTS 配置
TTS_ENABLED = False  # Level 1 暂时禁用

# DashScope TTS 声线配置
VOICE_CONFIG = {
    "default_voice": "zhichu",  # 知性女声（最适合 Kay）
    "backup_voices": ["zhimiao", "zhiyan"],  # 备选声线
    "sample_rate": 16000,
    "format": "mp3",
    "volume": 50
}

# 播放模式
AUTO_PLAY = True  # 是否自动播放（用户可在设置中关闭）

def get_voice_config() -> dict:
    """获取当前声线配置"""
    return VOICE_CONFIG

def is_tts_enabled() -> bool:
    """检查 TTS 是否可用"""
    return TTS_ENABLED