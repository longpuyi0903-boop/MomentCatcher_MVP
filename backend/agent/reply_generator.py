# /backend/agent/reply_generator.py (脆弱感增强版)

import os
import json
import traceback
from http import HTTPStatus
from datetime import datetime
import dashscope
from dashscope import Generation
from config.persona_config import get_system_prompt
from config.emotion_color_map import get_all_emotions, DEFAULT_EMOTION
from data_model.user_session import UserSession
from dotenv import load_dotenv

# 初始化 DashScope Key
# 先尝试从系统环境变量读取（Railway等云平台）
DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
# 调试：打印所有环境变量（仅用于调试）
if not DASHSCOPE_API_KEY:
    print("⚠️ ALIYUN_QWEN_KEY not found in system env, trying .env file...")
    # 打印所有包含 ALIYUN 的环境变量
    aliyun_vars = {k: v for k, v in os.environ.items() if 'ALIYUN' in k.upper()}
    if aliyun_vars:
        print(f"📋 Found ALIYUN-related env vars: {list(aliyun_vars.keys())}")
    load_dotenv()
    DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    # 打印所有环境变量名（用于调试）
    all_env_keys = list(os.environ.keys())
    print(f"❌ ALIYUN_QWEN_KEY not found. Available env vars: {sorted(all_env_keys)[:20]}...")
    raise EnvironmentError("ALIYUN_QWEN_KEY not found. Please check your environment variables or .env file.")
print("✅ ALIYUN_QWEN_KEY loaded successfully")

dashscope.api_key = DASHSCOPE_API_KEY
QWEN_MODEL = "qwen-plus"  # 使用 qwen-plus 模型

def _detect_language(user_message: str, history_messages: list) -> str:
    """
    检测用户消息的语言，并判断是否应该切换回复语言
    
    Args:
        user_message: 当前用户消息
        history_messages: 对话历史
    
    Returns:
        str: "en" 或 "zh"，表示应该使用的回复语言
    """
    import re
    
    # 检测当前消息的语言
    # 计算英文字符比例
    english_chars = len(re.findall(r'[a-zA-Z]', user_message))
    total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', user_message))  # 英文+中文
    
    if total_chars == 0:
        return "zh"  # 默认中文
    
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    
    # 如果当前消息主要是英文（>70%），检查历史对话
    if english_ratio > 0.7:
        # 检查历史中是否有用户消息（排除greeting等assistant消息）
        user_messages_in_history = [msg for msg in history_messages if hasattr(msg, 'role') and msg.role == 'user']
        
        # 如果历史中没有用户消息（这是第一条用户消息），且当前消息是英文，切换到英文
        if len(user_messages_in_history) == 0:
            return "en"
        
        # 如果历史中有用户消息，检查最近2条用户消息的语言
        if len(user_messages_in_history) >= 1:
            # 检查最近2条用户消息的语言
            recent_user_messages = [msg.content for msg in user_messages_in_history[-2:]]
            recent_english_count = 0
            for msg in recent_user_messages:
                msg_english = len(re.findall(r'[a-zA-Z]', msg))
                msg_total = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', msg))
                if msg_total > 0 and msg_english / msg_total > 0.7:
                    recent_english_count += 1
            
            # 如果当前消息和最近1条用户消息都是英文，切换到英文
            if recent_english_count >= 1:
                return "en"
    
    # 默认中文
    return "zh"


def generate_reply(user_message: str, session: UserSession, system_prompt: str = None):
    """
    生成 Kay 的回复（加入时间感知和脆弱感）
    
    Args:
        user_message: 用户消息
        session: 用户会话
        system_prompt: 可选的系统提示词（如果提供，将使用此prompt而不是默认的）
    """
    
    # 默认值（根据语言自适应）
    # 先检测语言，但这里还没有history，所以先用默认中文
    default_reply_zh = "哎呀，我脑子卡壳了一下，能再说一遍吗？"
    default_reply_en = "Oops, my mind went blank for a moment. Could you say that again?"
    reply = default_reply_zh
    emotion = DEFAULT_EMOTION

    try:
        # 获取当前时间，用于深夜模式判断
        current_hour = datetime.now().hour
        
        # 获取对话历史
        history_messages = session.messages if hasattr(session, 'messages') else []
        current_turn = len(history_messages) + 1
        
        # 检测语言并决定回复语言（在获取历史之后）
        reply_language = _detect_language(user_message, history_messages)
        
        # 准备基础 Prompt（如果未提供，使用默认的）
        if system_prompt is None:
            system_prompt = get_system_prompt(session.user_name, session.kay_name)
        supported_emotions = get_all_emotions()
        emotions_str = "、".join(supported_emotions)
        
        # 构造消息列表
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # 添加历史对话
        for msg in history_messages:
            role = msg.role if hasattr(msg, 'role') else 'user' 
            content = msg.content if hasattr(msg, 'content') else ''
            if role == 'assistant': role = 'assistant'
            messages.append({'role': role, 'content': content})

        # 构建最终的用户 Prompt（加入轻度时间感知）
        time_context = ""
        if 23 <= current_hour or current_hour <= 5:
            # 深夜时轻度提示，不强制要求表达困倦
            time_context = f"【时间提示】：现在是深夜 {current_hour:02d}:00 左右。如果对话自然，可以适度表达一点困倦（不是必须），但依然保持陪伴。\n"
        
        # 根据检测到的语言添加语言指令
        language_instruction = ""
        if reply_language == "en":
            language_instruction = "\n        ⚠️ **语言要求**：用户正在使用英文对话，请**必须用英文回复**。保持温柔自然的英文口语风格。"
        else:
            language_instruction = "\n        ⚠️ **语言要求**：请用中文回复。"
        
        final_user_prompt = f"""
        {time_context}【对话元信息】：这是第 {current_turn} 轮对话。请体现对 {session.user_name} 的熟悉感。

        【重要】大部分时候（90%）正常温柔回复即可，只在特定情境下（10%）适度表达脆弱感（困、不懂、情绪共鸣），且不要连续重复同一种表达。
        {language_instruction}
        
        【用户的最新消息】：{user_message}

        请完成以下任务，并**严格以 JSON 格式输出**：
        1. 判断用户情绪（从以下选一个：{emotions_str}）
        2. 以 {session.kay_name} 的身份回复（2-3句话，口语化，温柔自然）

        输出格式（纯JSON，无其他内容）：
        {{"reply": "Kay的回复", "emotion": "情绪标签"}}
        """
        messages.append({'role': 'user', 'content': final_user_prompt})

        # 调用 Qwen API
        response = Generation.call(
            model=QWEN_MODEL,
            messages=messages,
            result_format='message',
            temperature=0.75,
            top_p=0.8,
            max_tokens=256
        )
        
        if response.status_code != HTTPStatus.OK:
            print(f"DashScope API Error: {response.code} - {response.message}")
            return "信号不好，我正在重连...刚才你说什么？", DEFAULT_EMOTION

        raw_output = response.output.choices[0].message.content.strip()
        
        # 解析 JSON
        try:
            cleaned_output = raw_output.strip('```json').strip('```').strip()
            data = json.loads(cleaned_output)
            
            reply = data.get('reply', raw_output)
            detected_emotion = data.get('emotion', DEFAULT_EMOTION)
            
            if detected_emotion not in supported_emotions:
                detected_emotion = DEFAULT_EMOTION
            
            return reply, detected_emotion

        except json.JSONDecodeError:
            print(f"警告：LLM 未输出标准 JSON。原始输出：{raw_output}")
            # 根据语言设置默认回复
            if reply_language == "en":
                return default_reply_en, DEFAULT_EMOTION
            return raw_output, DEFAULT_EMOTION
            
    except Exception as e:
        print(f"致命异常：{e}")
        print(traceback.format_exc())
        # 根据语言返回对应的默认回复
        if 'reply_language' in locals() and reply_language == "en":
            return default_reply_en, emotion
        return reply, emotion