"""
MiniMax 语音克隆工具 (修正版)
完全按照 MiniMax 官方 API 文档实现
官方文档: https://platform.minimax.io/docs/guides/speech-voice-clone

正确流程:
1. 上传源音频文件到 /v1/files/upload (purpose: voice_clone) -> 获取 file_id
2. (可选) 上传示例音频到 /v1/files/upload (purpose: prompt_audio) -> 获取 prompt_file_id
3. 调用 /v1/voice_clone API 进行克隆
"""

import os
import json
import requests
import time
import random
import string
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple

# 加载环境变量
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

if not MINIMAX_API_KEY:
    # 尝试从多种可能的 .env 文件加载
    from pathlib import Path
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

# MiniMax API 端点
# 注意: MiniMax 有多个区域的 API 端点，API Key 必须与 Host 匹配！
# - 国际版: https://api.minimax.io 或 https://api.minimaxi.chat
# - 中国大陆版: https://api.minimax.chat (没有 i)
# 
# 可以通过环境变量 MINIMAX_API_HOST 来配置

MINIMAX_API_HOST = os.getenv("MINIMAX_API_HOST", "https://api.minimax.chat")  # 默认中国大陆版
MINIMAX_FILE_UPLOAD_URL = f"{MINIMAX_API_HOST}/v1/files/upload"
MINIMAX_VOICE_CLONE_URL = f"{MINIMAX_API_HOST}/v1/voice_clone"


def generate_voice_id(prefix: str = "cloned") -> str:
    """
    生成符合 MiniMax 规范的 voice_id
    
    规则:
    - 长度范围: [8, 256]
    - 必须以英文字母开头
    - 可包含字母、数字、'-' 和 '_'
    - 不能以 '-' 或 '_' 结尾
    - 不能与已存在的 voice_id 重复
    """
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    voice_id = f"{prefix}-voice-{timestamp}-{random_suffix}"
    return voice_id


def upload_audio_file(audio_file_path: str, purpose: str = "voice_clone") -> Optional[int]:
    """
    上传音频文件到 MiniMax，获取 file_id
    
    Args:
        audio_file_path: 音频文件路径
        purpose: 上传目的 ("voice_clone" 或 "prompt_audio")
    
    Returns:
        int: file_id，失败返回 None
    """
    audio_path = Path(audio_file_path)
    
    if not audio_path.exists():
        print(f"❌ 音频文件不存在: {audio_file_path}")
        return None
    
    # 检查文件格式
    valid_extensions = ['.mp3', '.m4a', '.wav']
    if audio_path.suffix.lower() not in valid_extensions:
        print(f"❌ 不支持的音频格式: {audio_path.suffix}")
        print(f"   支持的格式: {', '.join(valid_extensions)}")
        return None
    
    # 检查文件大小 (最大 20MB)
    file_size = audio_path.stat().st_size
    if file_size > 20 * 1024 * 1024:
        print(f"❌ 文件太大: {file_size / 1024 / 1024:.2f}MB (最大 20MB)")
        return None
    
    print(f"📤 正在上传音频文件...")
    print(f"   文件: {audio_path.name}")
    print(f"   大小: {file_size / 1024:.2f} KB")
    print(f"   用途: {purpose}")
    
    try:
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}"
        }
        
        # 根据文件扩展名确定 MIME 类型
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav'
        }
        mime_type = mime_types.get(audio_path.suffix.lower(), 'audio/mpeg')
        
        with open(audio_path, 'rb') as f:
            files = {
                "file": (audio_path.name, f, mime_type)
            }
            data = {
                "purpose": purpose
            }
            
            response = requests.post(
                MINIMAX_FILE_UPLOAD_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=120
            )
        
        # 检查响应
        if response.status_code != 200:
            print(f"❌ 上传失败: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   错误详情: {error_detail}")
            except:
                print(f"   响应: {response.text[:500]}")
            return None
        
        result = response.json()
        
        # 检查 API 错误
        if "base_resp" in result:
            status_code = result["base_resp"].get("status_code", 0)
            if status_code != 0:
                error_msg = result["base_resp"].get("status_msg", "未知错误")
                print(f"❌ API 错误: {status_code} - {error_msg}")
                return None
        
        # 提取 file_id
        file_id = result.get("file", {}).get("file_id")
        
        if not file_id:
            print(f"❌ 无法从响应中获取 file_id")
            print(f"   响应: {result}")
            return None
        
        print(f"✅ 上传成功! file_id: {file_id}")
        return file_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def clone_voice(
    file_id: int,
    voice_id: str,
    prompt_file_id: Optional[int] = None,
    prompt_text: Optional[str] = None,
    preview_text: Optional[str] = None,
    model: str = "speech-2.6-hd",
    need_noise_reduction: bool = True,
    need_volume_normalization: bool = True,
    language_boost: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    调用 MiniMax 语音克隆 API
    
    Args:
        file_id: 源音频的 file_id
        voice_id: 自定义的 voice_id (需符合命名规则)
        prompt_file_id: 示例音频的 file_id (可选，用于提高克隆质量)
        prompt_text: 示例音频对应的文字 (可选，需与 prompt_file_id 配合使用)
        preview_text: 预览文本 (可选，用于生成试听音频)
        model: 语音合成模型 (speech-2.6-hd, speech-2.6-turbo, speech-02-hd, speech-02-turbo)
        need_noise_reduction: 是否启用降噪
        need_volume_normalization: 是否启用音量归一化
        language_boost: 语言增强 (Chinese, English, auto 等)
    
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (是否成功, voice_id, demo_audio_url)
    """
    print(f"\n🎤 正在克隆语音...")
    print(f"   file_id: {file_id}")
    print(f"   voice_id: {voice_id}")
    print(f"   model: {model}")
    
    try:
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "file_id": file_id,
            "voice_id": voice_id,
            "need_noise_reduction": need_noise_reduction,
            "need_volumn_normalization": need_volume_normalization  # 注意: API 拼写是 volumn
        }
        
        # 添加示例音频 (可选，用于提高克隆质量)
        if prompt_file_id and prompt_text:
            payload["clone_prompt"] = {
                "prompt_audio": prompt_file_id,
                "prompt_text": prompt_text
            }
            print(f"   使用示例音频: file_id={prompt_file_id}")
        
        # 添加预览文本 (可选，用于生成试听音频)
        if preview_text:
            payload["text"] = preview_text
            payload["model"] = model
            print(f"   预览文本: {preview_text[:50]}...")
        
        # 添加语言增强 (可选)
        if language_boost:
            payload["language_boost"] = language_boost
            print(f"   语言增强: {language_boost}")
        
        print("\n⏳ 正在处理，请稍候...")
        
        response = requests.post(
            MINIMAX_VOICE_CLONE_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        # 检查响应
        if response.status_code != 200:
            print(f"❌ 克隆失败: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   错误详情: {error_detail}")
            except:
                print(f"   响应: {response.text[:500]}")
            return False, None, None
        
        result = response.json()
        
        # 检查 API 错误
        if "base_resp" in result:
            status_code = result["base_resp"].get("status_code", 0)
            status_msg = result["base_resp"].get("status_msg", "")
            
            if status_code != 0:
                print(f"❌ API 错误: {status_code} - {status_msg}")
                
                # 常见错误提示
                error_hints = {
                    1004: "认证失败，请检查 API Key",
                    2013: "输入格式无效，请检查参数",
                    2038: "没有克隆权限，请检查账户认证状态",
                    1002: "请求频率限制，请稍后再试",
                }
                if status_code in error_hints:
                    print(f"💡 提示: {error_hints[status_code]}")
                
                return False, None, None
        
        # 检查内容安全
        if result.get("input_sensitive"):
            sensitive_type = result.get("input_sensitive_type", 0)
            if sensitive_type != 0:
                sensitive_types = {
                    1: "严重违规",
                    2: "色情内容",
                    3: "广告内容",
                    4: "违禁内容",
                    5: "辱骂内容",
                    6: "恐怖/暴力",
                    7: "其他"
                }
                print(f"⚠️  内容安全警告: {sensitive_types.get(sensitive_type, '未知')}")
        
        # 获取预览音频 URL (如果有)
        demo_audio_url = result.get("demo_audio", "")
        
        print("\n" + "="*60)
        print("🎉 语音克隆成功!")
        print("="*60)
        print(f"🎵 Voice ID: {voice_id}")
        if demo_audio_url:
            print(f"🔊 预览音频: {demo_audio_url}")
        print("="*60)
        
        return True, voice_id, demo_audio_url if demo_audio_url else None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False, None, None
    except Exception as e:
        print(f"❌ 克隆失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def clone_voice_from_file(
    audio_file_path: str,
    voice_name: str = None,
    preview_text: str = "你好，这是我克隆后的声音测试。",
    model: str = "speech-2.6-hd",
    language_boost: str = "Chinese"
) -> Optional[str]:
    """
    从本地音频文件克隆语音 (完整流程)
    
    Args:
        audio_file_path: 音频文件路径 (支持 mp3, m4a, wav，10秒-5分钟)
        voice_name: 自定义音色名称前缀 (可选)
        preview_text: 预览文本 (可选)
        model: 语音合成模型
        language_boost: 语言增强
    
    Returns:
        str: 克隆后的 voice_id，失败返回 None
    """
    audio_path = Path(audio_file_path)
    
    if not audio_path.exists():
        print(f"❌ 音频文件不存在: {audio_file_path}")
        return None
    
    # 检查文件大小
    file_size = audio_path.stat().st_size
    
    print("\n" + "="*60)
    print("🎤 MiniMax 语音克隆工具")
    print("="*60)
    print(f"📁 音频文件: {audio_path}")
    print(f"📏 文件大小: {file_size / 1024:.2f} KB")
    print(f"🎯 模型: {model}")
    print(f"🌐 API Host: {MINIMAX_API_HOST}")
    print("="*60 + "\n")
    
    # 步骤 1: 上传源音频
    print("📌 步骤 1/2: 上传源音频")
    file_id = upload_audio_file(str(audio_path), purpose="voice_clone")
    
    if not file_id:
        print("❌ 上传源音频失败")
        return None
    
    # 步骤 2: 克隆语音
    print("\n📌 步骤 2/2: 克隆语音")
    
    # 生成 voice_id
    prefix = voice_name if voice_name else "custom"
    voice_id = generate_voice_id(prefix)
    
    success, cloned_voice_id, demo_audio_url = clone_voice(
        file_id=file_id,
        voice_id=voice_id,
        preview_text=preview_text,
        model=model,
        language_boost=language_boost
    )
    
    if not success:
        print("❌ 克隆语音失败")
        return None
    
    # 保存 voice_id 到文件
    voice_id_file = Path("minimax_voice_id.txt")
    voice_data = {
        "voice_id": cloned_voice_id,
        "voice_name": voice_name or "custom",
        "audio_file": str(audio_path),
        "model": model,
        "demo_audio_url": demo_audio_url,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(voice_id_file, 'w', encoding='utf-8') as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Voice ID 已保存到: {voice_id_file}")
    
    # 下载预览音频 (如果有)
    if demo_audio_url:
        try:
            print(f"\n📥 正在下载预览音频...")
            demo_response = requests.get(demo_audio_url, timeout=60)
            if demo_response.status_code == 200:
                demo_path = Path("cloned_voice_preview.mp3")
                with open(demo_path, 'wb') as f:
                    f.write(demo_response.content)
                print(f"✅ 预览音频已保存: {demo_path}")
        except Exception as e:
            print(f"⚠️  下载预览音频失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 克隆完成!")
    print("="*60)
    print(f"🎵 Voice ID: {cloned_voice_id}")
    print(f"\n📝 使用方法:")
    print(f"   在 tts_engine.py 中设置:")
    print(f"   DEFAULT_VOICE_ID = \"{cloned_voice_id}\"")
    print(f"\n   或在调用时传入:")
    print(f"   text_to_speech(text, voice=\"{cloned_voice_id}\")")
    print("="*60 + "\n")
    
    return cloned_voice_id


def clone_voice_with_prompt(
    source_audio_path: str,
    prompt_audio_path: str,
    prompt_text: str,
    voice_name: str = None,
    preview_text: str = None,
    model: str = "speech-2.6-hd",
    language_boost: str = "Chinese"
) -> Optional[str]:
    """
    使用示例音频进行高质量语音克隆 (完整流程)
    
    Args:
        source_audio_path: 源音频文件路径 (10秒-5分钟)
        prompt_audio_path: 示例音频文件路径 (小于8秒)
        prompt_text: 示例音频对应的文字 (必须与音频内容匹配)
        voice_name: 自定义音色名称前缀 (可选)
        preview_text: 预览文本 (可选)
        model: 语音合成模型
        language_boost: 语言增强
    
    Returns:
        str: 克隆后的 voice_id，失败返回 None
    """
    source_path = Path(source_audio_path)
    prompt_path = Path(prompt_audio_path)
    
    if not source_path.exists():
        print(f"❌ 源音频文件不存在: {source_audio_path}")
        return None
    
    if not prompt_path.exists():
        print(f"❌ 示例音频文件不存在: {prompt_audio_path}")
        return None
    
    print("\n" + "="*60)
    print("🎤 MiniMax 高质量语音克隆工具")
    print("="*60)
    print(f"📁 源音频: {source_path}")
    print(f"📁 示例音频: {prompt_path}")
    print(f"📝 示例文本: {prompt_text}")
    print(f"🎯 模型: {model}")
    print("="*60 + "\n")
    
    # 步骤 1: 上传源音频
    print("📌 步骤 1/3: 上传源音频")
    file_id = upload_audio_file(str(source_path), purpose="voice_clone")
    if not file_id:
        return None
    
    # 步骤 2: 上传示例音频
    print("\n📌 步骤 2/3: 上传示例音频")
    prompt_file_id = upload_audio_file(str(prompt_path), purpose="prompt_audio")
    if not prompt_file_id:
        return None
    
    # 步骤 3: 克隆语音
    print("\n📌 步骤 3/3: 克隆语音")
    
    prefix = voice_name if voice_name else "custom"
    voice_id = generate_voice_id(prefix)
    
    success, cloned_voice_id, demo_audio_url = clone_voice(
        file_id=file_id,
        voice_id=voice_id,
        prompt_file_id=prompt_file_id,
        prompt_text=prompt_text,
        preview_text=preview_text,
        model=model,
        language_boost=language_boost
    )
    
    if not success:
        return None
    
    # 保存结果
    voice_id_file = Path("minimax_voice_id.txt")
    voice_data = {
        "voice_id": cloned_voice_id,
        "voice_name": voice_name or "custom",
        "source_audio": str(source_path),
        "prompt_audio": str(prompt_path),
        "prompt_text": prompt_text,
        "model": model,
        "demo_audio_url": demo_audio_url,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(voice_id_file, 'w', encoding='utf-8') as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Voice ID 已保存到: {voice_id_file}")
    
    return cloned_voice_id


def load_cloned_voice_id() -> Optional[str]:
    """从保存的文件中加载克隆的 voice_id"""
    voice_id_file = Path("minimax_voice_id.txt")
    if voice_id_file.exists():
        try:
            with open(voice_id_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("voice_id")
        except:
            pass
    return None


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("\n" + "🎤 "*20)
    print("MiniMax 语音克隆工具 (官方 API 版)")
    print("🎤 "*20 + "\n")
    
    print("请选择克隆方式:")
    print("1. 简单克隆 (只需源音频)")
    print("2. 高质量克隆 (源音频 + 示例音频)")
    print("3. 直接使用默认音频文件")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        audio_file = input("请输入音频文件路径: ").strip()
        # 移除可能的引号
        audio_file = audio_file.strip('"').strip("'")
        
        voice_name = input("请输入音色名称 (可选，直接回车使用默认): ").strip() or None
        preview_text = input("请输入预览文本 (可选，直接回车使用默认): ").strip() or "你好，这是我克隆后的声音测试。"
        
        voice_id = clone_voice_from_file(
            audio_file,
            voice_name=voice_name,
            preview_text=preview_text
        )
        
    elif choice == "2":
        source_audio = input("请输入源音频文件路径 (10秒-5分钟): ").strip().strip('"').strip("'")
        prompt_audio = input("请输入示例音频文件路径 (小于8秒): ").strip().strip('"').strip("'")
        prompt_text = input("请输入示例音频对应的文字: ").strip()
        voice_name = input("请输入音色名称 (可选): ").strip() or None
        preview_text = input("请输入预览文本 (可选): ").strip() or None
        
        voice_id = clone_voice_with_prompt(
            source_audio,
            prompt_audio,
            prompt_text,
            voice_name=voice_name,
            preview_text=preview_text
        )
        
    elif choice == "3":
        # 使用默认路径
        default_audio = r"D:\D盘\AI Agent\MomentCatcher_MVP\audio_samples\companion_voice.m4a"
        print(f"\n使用默认音频文件: {default_audio}")
        
        voice_id = clone_voice_from_file(
            default_audio,
            voice_name="companion",
            preview_text="你好，这是我克隆后的声音测试。今天过得怎么样？"
        )
    else:
        print("❌ 无效选择")
        voice_id = None
    
    if voice_id:
        print("\n" + "="*60)
        print("🎉 全部完成!")
        print("="*60)
        print(f"\n现在你可以:")
        print(f"1. 更新 tts_engine.py 中的 DEFAULT_VOICE_ID")
        print(f"2. 或在调用 text_to_speech() 时传入 voice=\"{voice_id}\"")
        print("="*60 + "\n")
