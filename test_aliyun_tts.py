"""
阿里云 DashScope TTS 连通性测试
使用 DashScope SDK（更简单的 API）
"""

import os
from dotenv import load_dotenv
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

# 加载环境变量
load_dotenv()

def test_dashscope_tts():
    """测试 DashScope TTS API"""
    print("=" * 50)
    print("🧪 开始测试阿里云 DashScope TTS API")
    print("=" * 50)
    
    # 1. 检查 API Key
    # DashScope 使用的是独立的 API Key，不是 AccessKey
    # 但我们可以先用 AccessKey Secret 测试（通常也能工作）
    api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
    
    if not api_key:
        print("❌ 错误：未找到 ALIYUN_ACCESS_KEY_SECRET")
        print("\n请检查 .env 文件是否包含：")
        print("  ALIYUN_ACCESS_KEY_SECRET=你的AccessKey_Secret")
        return False
    
    print(f"✅ API Key 已加载（前10位）：{api_key[:10]}...")
    
    # 2. 设置 API Key
    dashscope.api_key = api_key
    
    # 3. 测试语音合成
    try:
        print("\n📡 正在测试语音合成...")
        
        # 测试文本
        test_text = "嘿，我是 Kay，这是一条测试语音。"
        
        # 调用 TTS
        response = SpeechSynthesizer.call(
            model='sambert-zhichu-v1',  # 中文女声模型
            text=test_text,
            sample_rate=16000,
            format='mp3',
            voice='zhichu'  # 知性女声
        )
        
        print(f"📊 状态码：{response.get_response().status_code}")
        
        # 4. 处理响应
        if response.get_response().status_code == 200:
            # 获取音频数据
            audio_data = response.get_audio_data()
            
            if audio_data:
                print("✅ 语音合成成功！")
                print(f"📝 合成文本：{test_text}")
                print(f"🎤 使用声线：zhichu（知性女声）")
                
                # 保存测试音频
                test_audio_file = "test_dashscope_output.mp3"
                
                with open(test_audio_file, "wb") as f:
                    f.write(audio_data)
                
                file_size = len(audio_data) / 1024
                print(f"💾 测试音频已保存：{test_audio_file} ({file_size:.1f} KB)")
                print("   你可以播放这个文件来验证音质")
                
                return True
            else:
                print("❌ 未获取到音频数据")
                return False
        else:
            print(f"❌ 请求失败")
            print(f"   错误信息：{response.get_response().message}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常：{e}")
        print("\n可能的原因：")
        print("1. API Key 不正确或没有 DashScope 权限")
        print("2. 模型名称错误")
        print("3. 网络连接问题")
        return False


def test_voice_options():
    """测试不同声线"""
    print("\n" + "=" * 50)
    print("🎤 测试其他可选声线")
    print("=" * 50)
    
    api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
    dashscope.api_key = api_key
    
    # Kay 适合的声线列表
    voices = [
        ("zhichu", "知性"),
        ("zhimiao", "温柔"),
        ("zhiyan", "亲切"),
        ("zhitian", "甜美")
    ]
    
    print("\n测试结果：")
    for voice, desc in voices:
        try:
            response = SpeechSynthesizer.call(
                model='sambert-zhichu-v1',
                text="测试",
                format='mp3',
                voice=voice
            )
            
            if response.get_response().status_code == 200:
                print(f"  ✅ {voice} ({desc}) - 可用")
            else:
                print(f"  ⚠️ {voice} ({desc}) - 不可用")
                
        except Exception as e:
            print(f"  ❌ {voice} ({desc}) - 测试失败")


if __name__ == "__main__":
    print("📦 确保已安装依赖：")
    print("   pip install dashscope python-dotenv")
    print()
    
    # 运行主测试
    success = test_dashscope_tts()
    
    if success:
        # 测试其他声线
        test_voice_options()
        
        print("\n" + "=" * 50)
        print("🎉 阿里云 DashScope TTS API 测试通过！")
        print("=" * 50)
        print("\n💡 提示：")
        print("  - 测试音频文件：test_dashscope_output.mp3")
        print("  - 推荐声线：zhichu（知性，适合 Kay）")
        print("\n✅ 下一步：")
        print("  1. 播放音频验证音质")
        print("  2. 如果满意，我们开始 Level 1 代码生成")
    else:
        print("\n⚠️ 测试失败")
        print("\n🔧 可能的解决方案：")
        print("1. 确认 .env 中的 ALIYUN_ACCESS_KEY_SECRET 正确")
        print("2. 检查 AccessKey 是否有 DashScope 权限")
        print("3. 访问 https://dashscope.console.aliyun.com/ 确认服务已开通")