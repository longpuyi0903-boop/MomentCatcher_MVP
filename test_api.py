"""
简单的 API 测试脚本
用于验证 FastAPI 后端是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")
    return response.status_code == 200

def test_init():
    """测试初始化"""
    print("🔍 测试初始化...")
    data = {
        "user_name": "TestUser",
        "agent_name": "TestAgent"
    }
    response = requests.post(f"{BASE_URL}/api/init", json=data)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")
    return response.json() if response.status_code == 200 else None

def test_start_moment(user_id):
    """测试开始新 Moment"""
    print("🔍 测试开始新 Moment...")
    data = {"user_id": user_id}
    response = requests.post(f"{BASE_URL}/api/moments/start", json=data)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")
    return response.json() if response.status_code == 200 else None

def test_chat(user_id, message, history=None):
    """测试聊天"""
    print(f"🔍 测试聊天: {message}")
    data = {
        "user_id": user_id,
        "message": message,
        "history": history or []
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=data)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   回复: {result.get('reply', 'N/A')[:100]}...")
    print(f"   情绪: {result.get('emotion', 'N/A')}")
    print(f"   消息数: {result.get('message_count', 0)}\n")
    return result if response.status_code == 200 else None

def test_save_moment(user_id):
    """测试保存 Moment"""
    print("🔍 测试保存 Moment...")
    data = {"user_id": user_id}
    response = requests.post(f"{BASE_URL}/api/moments/save", json=data)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   Moment ID: {result.get('moment_id', 'N/A')}")
        print(f"   标题: {result.get('card', {}).get('title', 'N/A')}")
        print(f"   情绪: {result.get('card', {}).get('emotion', 'N/A')}\n")
        return result
    else:
        print(f"   错误: {response.text}\n")
        return None

def test_get_moments(user_id):
    """测试获取所有 Moments"""
    print("🔍 测试获取所有 Moments...")
    response = requests.get(f"{BASE_URL}/api/moments", params={"user_id": user_id})
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   总数: {result.get('total', 0)}")
        print(f"   Moments: {len(result.get('moments', []))}\n")
        return result
    else:
        print(f"   错误: {response.text}\n")
        return None

def test_style_profile(user_id):
    """测试获取风格画像"""
    print("🔍 测试获取风格画像...")
    response = requests.get(f"{BASE_URL}/api/style/profile", params={"user_id": user_id})
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        profile = result.get('profile', {})
        print(f"   总消息数: {profile.get('total_messages', 0)}")
        print(f"   平均句长: {profile.get('avg_sentence_length', 0)}\n")
        return result
    else:
        print(f"   错误: {response.text}\n")
        return None

def main():
    """主测试流程"""
    print("="*60)
    print("🧪 Moment Catcher API 测试")
    print("="*60 + "\n")
    
    # 检查服务器是否运行
    try:
        if not test_health():
            print("❌ 服务器未运行或无法访问")
            print("💡 请先运行: python run_api.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请先运行: python run_api.py")
        return
    
    # 测试流程
    print("\n" + "="*60)
    print("📝 开始测试流程")
    print("="*60 + "\n")
    
    # 1. 初始化
    init_result = test_init()
    if not init_result:
        print("❌ 初始化失败")
        return
    
    user_id = init_result.get("user_id")
    
    # 2. 开始新 Moment
    start_result = test_start_moment(user_id)
    if not start_result:
        print("❌ 开始 Moment 失败")
        return
    
    # 3. 发送几条消息
    history = []
    for msg in ["你好", "今天天气不错", "我想聊聊"]:
        chat_result = test_chat(user_id, msg, history)
        if chat_result:
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": chat_result.get("reply", "")})
    
    # 4. 保存 Moment
    save_result = test_save_moment(user_id)
    
    # 5. 获取所有 Moments
    moments_result = test_get_moments(user_id)
    
    # 6. 获取风格画像
    style_result = test_style_profile(user_id)
    
    print("="*60)
    print("✅ 测试完成！")
    print("="*60)
    print("\n💡 提示:")
    print("   - 访问 http://localhost:8000/docs 查看完整 API 文档")
    print("   - 访问 http://localhost:8000/redoc 查看 ReDoc 文档")

if __name__ == "__main__":
    main()


