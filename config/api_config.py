"""
API 配置管理
负责：加载和验证所有 API Keys
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class APIConfig:
    """API Keys 配置类"""
    
    # 通义千问 API（主要 LLM）
    QWEN_API_KEY = os.getenv("ALIYUN_QWEN_KEY", "")
    QWEN_MODEL = "qwen-plus"  # 免费且快速
    QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # Gemini API（备用，已弃用）
    # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # GEMINI_MODEL = "gemini-2.5-flash"
    
    # 阿里云 TTS（暂时预留，Level 2 实现）
    ALIYUN_DASHSCOPE_API_KEY = os.getenv("ALIYUN_DASHSCOPE_API_KEY", "")
    
    @classmethod
    def validate(cls):
        """验证必需的 API Keys 是否存在"""
        errors = []
        
        if not cls.QWEN_API_KEY:
            errors.append("❌ ALIYUN_QWEN_KEY 未设置")
        
        return errors
    
    @classmethod
    def get_status(cls):
        """获取配置状态摘要"""
        status = {
            "通义千问 API": "✅" if cls.QWEN_API_KEY else "❌",
            "TTS API": "✅" if cls.ALIYUN_DASHSCOPE_API_KEY else "⚠️ 未配置"
        }
        return status