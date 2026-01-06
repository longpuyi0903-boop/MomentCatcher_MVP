"""
快速测试 MiniMax 语音克隆
直接使用 audio_samples/companion_voice.m4a
"""

from minimax_voice_clone import clone_voice_from_file
from pathlib import Path

# 音频文件路径
audio_file = Path("audio_samples/companion_voice.m4a")

if not audio_file.exists():
    print(f"❌ 音频文件不存在: {audio_file}")
    print(f"   当前工作目录: {Path.cwd()}")
    print(f"   请确认文件路径是否正确")
else:
    print(f"✅ 找到音频文件: {audio_file}")
    print(f"📏 文件大小: {audio_file.stat().st_size / 1024:.2f} KB\n")
    
    # 执行克隆
    voice_id = clone_voice_from_file(
        str(audio_file),
        voice_name="companion_voice"
    )
    
    if voice_id:
        print("\n" + "="*60)
        print("✅ 克隆成功！")
        print("="*60)
        print(f"🎵 Voice ID: {voice_id}")
        print("\n💡 提示：")
        print("   TTS 引擎会自动加载这个音色 ID")
        print("   重启应用后即可使用克隆的音色")
        print("="*60 + "\n")
    else:
        print("\n❌ 克隆失败，请查看上方错误信息")

