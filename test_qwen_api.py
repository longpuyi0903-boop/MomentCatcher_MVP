"""
通义千问 API 连通性测试
测试目标：验证 DashScope API Key 是否有效
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 获取 API Key
QWEN_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
MODEL_NAME = "qwen-turbo"  # 免费且快速的模型
TEST_PROMPT = "你是一个情绪捕捉助手 Kay，用一句话问候用户 Irene。记住：极度简短，不超过2句话，口语化。"

print("=" * 50)
print("🚀 通义千问 API 连通性测试")
print("=" * 50)

if not QWEN_API_KEY:
    print("❌ 错误：ALIYUN_QWEN_KEY 环境变量未设置。")
    print("请检查 .env 文件是否包含：")
    print("  ALIYUN_QWEN_KEY=你的API_Key")
else:
    try:
        # 初始化客户端（通义千问兼容 OpenAI SDK）
        client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print(f"✅ 客户端初始化成功")
        print(f"✅ 正在调用模型: {MODEL_NAME}")
        print()
        
        # 调用 API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是 Kay，一个高情商、调皮、口语化的陪伴型 AI。"},
                {"role": "user", "content": TEST_PROMPT}
            ],
            temperature=0.8,
            max_tokens=100
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        print("✅ 通义千问 API 调用成功！")
        print(f"📝 Kay 的回复: {reply}")
        print()
        
        # 测试情绪识别
        print("=" * 50)
        print("🧪 测试情绪识别功能")
        print("=" * 50)
        
        emotion_test = "今天拿到 offer 了，超级开心！"
        emotion_prompt = f"""
请识别以下用户消息的主要情绪，只返回一个情绪词。

可选情绪：开心、兴奋、平静、感动、难过、焦虑、疲惫、愤怒、困惑、期待、平淡

用户消息："{emotion_test}"

只返回一个情绪词，不要有任何其他内容。

情绪：
"""
        
        response2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": emotion_prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        emotion = response2.choices[0].message.content.strip()
        
        print(f"✅ 情绪识别成功！")
        print(f"📝 测试消息: {emotion_test}")
        print(f"📝 识别到的情绪: {emotion}")
        
        print()
        print("=" * 50)
        print("🎉 所有测试通过！通义千问 API 工作正常")
        print("=" * 50)
        print()
        print("💡 推荐模型：")
        print("  - qwen-turbo (当前使用): 免费，快速")
        print("  - qwen-plus: 更聪明，免费")
        print("  - qwen-max: 最强，少量免费")
        
    except Exception as e:
        print(f"❌ 通义千问 API 调用失败！")
        print(f"详细错误: {e}")
        print()
        print("可能的原因：")
        print("1. API Key 不正确")
        print("2. 网络连接问题")
        print("3. DashScope 服务未开通")

print("=" * 50)