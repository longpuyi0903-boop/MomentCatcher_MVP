"""
TTS Engine - 文字转语音 (CosyVoice 复刻音色版)
使用阿里云 DashScope CosyVoice + 复刻音色
"""
import os
from pathlib import Path
from http import HTTPStatus
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from dotenv import load_dotenv
# 加载环境变量
# 先尝试从系统环境变量读取（Railway等云平台）
DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
# 如果系统环境变量没有，再尝试从.env文件加载
if not DASHSCOPE_API_KEY:
    load_dotenv()
    DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    raise EnvironmentError("ALIYUN_QWEN_KEY not found. Please check your environment variables or .env file.")
dashscope.api_key = DASHSCOPE_API_KEY
# 音频输出目录
AUDIO_OUTPUT_DIR = Path("audio_outputs")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)
# 固定的音频文件路径（每次覆盖）
LATEST_AUDIO_PATH = AUDIO_OUTPUT_DIR / "latest_reply.wav"
# 复刻的音色 ID
CLONED_VOICE_ID = "cosyvoice-v3-plus-companion-80f89c9413a2436385742cf16adea562"
def text_to_speech(text: str, voice: str = None, save_path: str = None) -> str:
    """
    将文本转换为语音（使用复刻音色）
    
    Args:
        text: 要转换的文本
        voice: 音色 ID（可选，默认使用复刻音色）
        save_path: 保存路径（可选，默认使用固定路径覆盖）
    
    Returns:
        str: 生成的音频文件路径
    """
    
    # 使用复刻的音色
    if voice is None:
        voice = CLONED_VOICE_ID
    
    # 使用固定路径，每次覆盖（节省空间，模拟实时对话）
    if save_path is None:
        save_path = LATEST_AUDIO_PATH
    else:
        save_path = Path(save_path)
    
    # 强制删除旧文件（避免覆盖失败）
    if save_path.exists():
        try:
            save_path.unlink()
            print(f"🗑️  删除旧音频文件: {save_path}")
        except Exception as e:
            print(f"⚠️  删除旧文件失败: {e}")
    
    try:
        print(f"🎤 正在生成语音: {text[:30]}...")
        
        # 使用 CosyVoice v3 plus + 复刻音色
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v3-plus',  # 必须与复刻时的 target_model 一致
            voice=voice,
            speech_rate=1  # 语速1.2倍（-500到500，100约等于1.2倍）
        )
        
        # 调用合成
        audio = synthesizer.call(text)
        
        # 保存音频数据
        with open(save_path, 'wb') as f:
            f.write(audio)
        
        print(f"✅ 语音生成成功: {save_path}")
        return str(save_path)
        
    except Exception as e:
        print(f"❌ TTS 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None
def test_tts():
    """测试 TTS 功能"""
    test_text = "嘿 Irene，今天过得怎么样？"
    
    print("\n" + "="*60)
    print("🎤 TTS Engine 测试 (CosyVoice 复刻音色)")
    print("="*60)
    print(f"📝 测试文本: {test_text}")
    print(f"🎵 音色: 复刻音色 (companion)")
    print(f"🎯 模型: cosyvoice-v3-plus")
    print("="*60 + "\n")
    
    audio_path = text_to_speech(test_text)
    
    if audio_path:
        print("\n" + "="*60)
        print("✅ 测试成功！")
        print(f"📁 音频文件: {audio_path}")
        print("💡 你可以用播放器打开这个文件试听")
        print("="*60 + "\n")
    else:
        print("\n❌ 测试失败")
if __name__ == "__main__":
    test_tts()