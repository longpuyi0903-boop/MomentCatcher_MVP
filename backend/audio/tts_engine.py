"""
TTS Engine - 文字转语音 (MiniMax Speech-2.6)
使用 MiniMax T2A v2 API (speech-2.6-hd / speech-2.6-turbo)
官方文档: https://platform.minimax.io/docs/api-reference/speech-t2a-http

注意: MiniMax 最新 API 不再需要 GROUP_ID，只需要 API_KEY
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# 加载环境变量
# 先尝试从系统环境变量读取（Railway等云平台）
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

# 如果系统环境变量没有，再尝试从.env文件加载
if not MINIMAX_API_KEY:
    # 尝试从多种可能的 .env 文件加载
    env_files = ['.env', '_env', 'env', '.env.local']
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
            if MINIMAX_API_KEY:
                print(f"✅ 已从 {env_file} 加载环境变量")
                break
    
    # 如果还是没找到，尝试默认加载
    if not MINIMAX_API_KEY:
        load_dotenv()
        MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

if not MINIMAX_API_KEY:
    raise EnvironmentError("MINIMAX_API_KEY not found. Please check your environment variables or .env file.")

# MiniMax API 配置
# 注意: MiniMax 有多个区域的 API 端点，API Key 必须与 Host 匹配！
# - 国际版: https://api.minimax.io 或 https://api.minimaxi.chat
# - 中国大陆版: https://api.minimax.chat (没有 i)
MINIMAX_API_HOST = os.getenv("MINIMAX_API_HOST", "https://api.minimax.chat")  # 默认中国大陆版
MINIMAX_TTS_API_URL = os.getenv("MINIMAX_TTS_API_URL", f"{MINIMAX_API_HOST}/v1/t2a_v2")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "speech-2.6-hd")  # 可选: speech-2.6-hd, speech-2.6-turbo

# 音频输出目录
AUDIO_OUTPUT_DIR = Path("audio_outputs")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)
# 固定的音频文件路径（每次覆盖）
LATEST_AUDIO_PATH = AUDIO_OUTPUT_DIR / "latest_reply.mp3"

# 默认音色 ID
# MiniMax 提供 300+ 预设音色，可以在 API 文档中查看
# 如果使用克隆的音色，可以从 minimax_voice_id.txt 加载
DEFAULT_VOICE_ID = "female-shaonv"  # 少女音色，可根据需要修改

# 尝试加载克隆的音色 ID（如果存在）
def _load_cloned_voice():
    """尝试从文件加载克隆的音色 ID"""
    global DEFAULT_VOICE_ID
    try:
        voice_id_file = Path("minimax_voice_id.txt")
        if voice_id_file.exists():
            with open(voice_id_file, 'r', encoding='utf-8') as f:
                voice_data = json.load(f)
                cloned_voice_id = voice_data.get("voice_id")
                if cloned_voice_id:
                    DEFAULT_VOICE_ID = cloned_voice_id
                    print(f"✅ [MiniMax] 已加载克隆音色: {cloned_voice_id}")
                    return True
    except Exception as e:
        print(f"⚠️  [MiniMax] 加载克隆音色失败: {e}")
    return False

# 初始化时尝试加载克隆音色
_load_cloned_voice()


def text_to_speech(
    text: str, 
    voice: str = None, 
    save_path: str = None, 
    speed: float = 1.0, 
    emotion: str = "auto",
    model: str = None,
    output_format: str = "hex",
    language_boost: str = "Chinese"
) -> Optional[str]:
    """
    将文本转换为语音（使用 MiniMax T2A v2 API）
    
    Args:
        text: 要转换的文本（最多 10000 字符）
        voice: 音色 ID（可选，默认使用默认音色或克隆音色）
        save_path: 保存路径（可选，默认使用固定路径覆盖）
        speed: 语速（0.5-2.0，默认1.0）
        emotion: 情感参数（auto/happy/sad/angry/fearful/surprised/disgust等）
        model: 模型版本（speech-2.6-hd/speech-2.6-turbo，默认使用环境变量配置）
        output_format: 输出格式（hex/url，默认hex）
        language_boost: 语言增强（Chinese/English/auto等）
    
    Returns:
        str: 生成的音频文件路径，失败返回 None
    """
    
    # 使用默认音色
    if voice is None:
        voice = DEFAULT_VOICE_ID
    
    # 使用默认模型
    if model is None:
        model = MINIMAX_MODEL
    
    # 使用固定路径，每次覆盖（节省空间，模拟实时对话）
    if save_path is None:
        save_path = LATEST_AUDIO_PATH
    else:
        save_path = Path(save_path)
    
    # 强制删除旧文件（避免覆盖失败）
    if save_path.exists():
        try:
            save_path.unlink()
        except Exception as e:
            print(f"⚠️  删除旧文件失败: {e}")
    
    try:
        print(f"🎤 [MiniMax] 正在生成语音: {text[:50]}...")
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体 (按照官方 T2A v2 API 格式)
        payload = {
            "model": model,
            "text": text,
            "stream": False,
            "language_boost": language_boost,
            "output_format": output_format,
            "voice_setting": {
                "voice_id": voice,
                "speed": speed,
                "vol": 1,
                "pitch": 0
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }
        
        # 添加情感设置 (如果不是auto)
        if emotion and emotion != "auto":
            payload["voice_setting"]["emotion"] = emotion
        
        # 调用 MiniMax API
        response = requests.post(
            MINIMAX_TTS_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # 检查响应状态
        if response.status_code != 200:
            error_msg = f"API 请求失败: HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text[:500]}"
            print(f"❌ {error_msg}")
            return None
        
        # 解析响应
        try:
            result = response.json()
        except json.JSONDecodeError:
            print(f"❌ [MiniMax] 响应格式无法解析为 JSON")
            return None
        
        # 检查 API 错误
        if "base_resp" in result:
            status_code = result["base_resp"].get("status_code", 0)
            status_msg = result["base_resp"].get("status_msg", "")
            
            if status_code != 0:
                print(f"❌ [MiniMax] API 错误: {status_code} - {status_msg}")
                
                # 常见错误提示
                error_hints = {
                    1004: "认证失败，请检查 API Key",
                    1008: "账户余额不足，请充值",
                    2013: "输入格式无效，请检查参数",
                    1002: "请求频率限制，请稍后再试",
                }
                if status_code in error_hints:
                    print(f"💡 提示: {error_hints[status_code]}")
                
                return None
        
        # 提取音频数据
        audio_data = None
        
        if output_format == "url":
            # 如果返回的是 URL，下载音频
            audio_url = result.get("data", {}).get("audio")
            if audio_url:
                try:
                    audio_response = requests.get(audio_url, timeout=60)
                    if audio_response.status_code == 200:
                        audio_data = audio_response.content
                    else:
                        print(f"❌ [MiniMax] 下载音频失败: {audio_response.status_code}")
                        return None
                except Exception as e:
                    print(f"❌ [MiniMax] 下载音频失败: {e}")
                    return None
        else:
            # 如果返回的是 hex 编码的音频数据
            audio_hex = result.get("data", {}).get("audio")
            if audio_hex:
                try:
                    audio_data = bytes.fromhex(audio_hex)
                except Exception as e:
                    print(f"❌ [MiniMax] 解码音频数据失败: {e}")
                    return None
        
        if not audio_data:
            print(f"❌ [MiniMax] 无法从响应中提取音频数据")
            print(f"   响应: {result}")
            return None
        
        # 验证音频数据有效性
        if len(audio_data) < 100:
            print(f"❌ [MiniMax] 音频数据太短，可能无效")
            return None
        
        # 保存音频数据
        with open(save_path, 'wb') as f:
            f.write(audio_data)
        
        # 输出额外信息
        extra_info = result.get("extra_info", {})
        audio_length = extra_info.get("audio_length", 0)
        usage_chars = extra_info.get("usage_characters", 0)
        
        print(f"✅ [MiniMax] 语音生成成功: {save_path}")
        if audio_length:
            print(f"   时长: {audio_length / 1000:.2f}秒, 字符数: {usage_chars}")
        
        return str(save_path)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ [MiniMax] 网络请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ [MiniMax] TTS 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def reload_cloned_voice() -> bool:
    """重新加载克隆的音色（用于克隆完成后刷新）"""
    return _load_cloned_voice()


def get_current_voice_id() -> str:
    """获取当前使用的音色 ID"""
    return DEFAULT_VOICE_ID


def set_voice_id(voice_id: str):
    """设置音色 ID"""
    global DEFAULT_VOICE_ID
    DEFAULT_VOICE_ID = voice_id
    print(f"✅ [MiniMax] 音色已设置为: {voice_id}")


def test_tts():
    """测试 TTS 功能"""
    test_text = "嘿，今天过得怎么样？我是你的AI伙伴。"
    
    print("\n" + "="*60)
    print("🎤 TTS Engine 测试 (MiniMax T2A v2)")
    print("="*60)
    print(f"📝 测试文本: {test_text}")
    print(f"🎵 音色: {DEFAULT_VOICE_ID}")
    print(f"🎯 模型: {MINIMAX_MODEL}")
    print(f"🔑 API Key: {MINIMAX_API_KEY[:10]}..." if MINIMAX_API_KEY else "❌ API Key 未设置")
    print(f"🌐 API URL: {MINIMAX_TTS_API_URL}")
    print("="*60 + "\n")
    
    audio_path = text_to_speech(test_text)
    
    if audio_path:
        print("\n" + "="*60)
        print("✅ 测试成功！")
        print(f"📁 音频文件: {audio_path}")
        print("💡 你可以用播放器打开这个文件试听")
        print("="*60 + "\n")
        return True
    else:
        print("\n❌ 测试失败")
        print("💡 请检查：")
        print("   1. MINIMAX_API_KEY 是否正确设置")
        print("   2. 网络连接是否正常")
        print("   3. 账户余额是否充足")
        return False


# ============================================================
# 预设音色列表 (部分常用音色)
# ============================================================
PRESET_VOICES = {
    # 中文音色
    "female-shaonv": "少女音色",
    "female-yujie": "御姐音色", 
    "male-qn-qingse": "青涩青年",
    "male-qn-jingying": "精英青年",
    "male-qn-badao": "霸道青年",
    "female-chengshu": "成熟女性",
    "male-chengshu": "成熟男性",
    
    # 英文音色
    "English_expressive_narrator": "表达力强的叙述者",
    "English_Insightful_Speaker": "洞察力演讲者",
    "Wise_Woman": "智慧女性",
    
    # 有声书音色
    "audiobook_male_1": "有声书男声1",
    "audiobook_male_2": "有声书男声2", 
    "audiobook_female_1": "有声书女声1",
    "audiobook_female_2": "有声书女声2",
}


def list_preset_voices():
    """列出预设音色"""
    print("\n" + "="*60)
    print("📋 MiniMax 预设音色列表 (部分)")
    print("="*60)
    for voice_id, desc in PRESET_VOICES.items():
        print(f"  {voice_id}: {desc}")
    print("="*60)
    print("💡 完整音色列表请参考 MiniMax 官方文档")
    print("   https://platform.minimax.io/docs/api-reference/speech-t2a-intro")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_tts()
