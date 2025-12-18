"""
声音复刻 - 简化版
直接使用项目中的音频文件
"""

import os
import shutil
import dashscope
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    raise EnvironmentError("ALIYUN_QWEN_KEY not found in .env")

dashscope.api_key = DASHSCOPE_API_KEY


def clone_voice_from_local():
    """
    使用本地音频文件创建音色
    
    重要提示：
    阿里云声音复刻 API 要求音频文件必须通过公网 URL 访问
    
    你需要：
    1. 将 companion_voice.m4a 上传到阿里云 OSS
    2. 设置为公开读权限
    3. 获取公网 URL
    4. 粘贴到下方
    """
    
    print("\n" + "="*60)
    print("🎤 CosyVoice 声音复刻")
    print("="*60)
    print("📁 音频文件: companion_voice.m4a (23.62秒)")
    print("🎯 目标模型: cosyvoice-v3-plus")
    print("="*60 + "\n")
    
    # 检查本地文件
    local_file = Path("audio_samples/companion_voice.m4a")
    if not local_file.exists():
        print("⚠️  本地文件不存在，正在从上传目录复制...")
        local_file.parent.mkdir(exist_ok=True)
        # 这里假设文件已经在项目中
        print("💡 请手动将 companion_voice.m4a 放到 audio_samples/ 目录")
        return None
    
    print("✅ 找到本地音频文件\n")
    
    # 提示用户输入 OSS URL
    print("⚠️  重要：阿里云复刻 API 需要公网可访问的音频 URL\n")
    print("📝 步骤：")
    print("   1. 登录阿里云 OSS 控制台")
    print("   2. 创建 Bucket（如果没有）")
    print("   3. 上传 companion_voice.m4a")
    print("   4. 设置文件为「公共读」")
    print("   5. 复制文件的公网 URL\n")
    print("💡 URL 格式示例：")
    print("   https://your-bucket.oss-cn-beijing.aliyuncs.com/companion_voice.m4a\n")
    
    audio_url = input("请粘贴音频文件的 OSS URL: ").strip()
    
    if not audio_url:
        print("❌ 未提供 URL，退出")
        return None
    
    # 调用复刻 API
    try:
        from dashscope.audio.tts_v2 import VoiceEnrollmentService
        
        service = VoiceEnrollmentService()
        
        print("\n📤 正在创建音色...")
        print("⏳ 预计需要 10-30 秒...\n")
        
        voice_id = service.create_voice(
            target_model='cosyvoice-v3-plus',
            prefix='companion',
            url=audio_url
        )
        
        print("\n" + "="*60)
        print("🎉 声音复刻成功！")
        print("="*60)
        print(f"🎵 Voice ID: {voice_id}")
        print(f"📋 Request ID: {service.get_last_request_id()}")
        print("="*60 + "\n")
        
        # 保存 Voice ID
        voice_id_file = Path("voice_id.txt")
        with open(voice_id_file, 'w') as f:
            f.write(voice_id)
        
        print(f"💾 已保存到: {voice_id_file}\n")
        
        # 测试生成语音
        test = input("是否测试复刻的音色？(y/n): ").strip().lower()
        if test == 'y':
            test_voice(voice_id)
        
        return voice_id
        
    except Exception as e:
        print(f"\n❌ 复刻失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_voice(voice_id: str):
    """测试复刻的音色"""
    
    test_text = "好累啊。要不先躺一会儿？我陪你眯个眼。"
    
    print(f"\n🎤 测试文本: {test_text}")
    print("📤 正在生成语音...\n")
    
    try:
        from dashscope.audio.tts_v2 import SpeechSynthesizer
        
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v3-plus',
            voice=voice_id
        )
        
        audio = synthesizer.call(test_text)
        
        output_file = Path("audio_outputs/cloned_test.mp3")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'wb') as f:
            f.write(audio)
        
        print(f"✅ 测试音频: {output_file}")
        print("💡 请播放此文件检查效果\n")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    
    print("\n" + "🎤 "*30)
    print("声音复刻工具 - 简化版")
    print("🎤 "*30 + "\n")
    
    voice_id = clone_voice_from_local()
    
    if voice_id:
        print("\n" + "="*60)
        print("✅ 完成！")
        print("="*60)
        print("📝 下一步：")
        print(f"   1. Voice ID: {voice_id}")
        print("   2. 更新 tts_engine.py:")
        print(f"      voice = '{voice_id}'")
        print("   3. 重启 Gradio")
        print("="*60 + "\n")