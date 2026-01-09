# /backend/agent/reply_generator.py (V2 流式输出版)

import os
import json
import traceback
from http import HTTPStatus
from datetime import datetime
from typing import Generator, Tuple
import dashscope
from dashscope import Generation
from config.persona_config import get_system_prompt
from config.emotion_color_map import get_all_emotions, DEFAULT_EMOTION
from data_model.user_session import UserSession
from dotenv import load_dotenv

# 初始化 DashScope Key
DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    print("⚠️ ALIYUN_QWEN_KEY not found in system env, trying .env file...")
    load_dotenv()
    DASHSCOPE_API_KEY = os.getenv("ALIYUN_QWEN_KEY")
if not DASHSCOPE_API_KEY:
    raise EnvironmentError("ALIYUN_QWEN_KEY not found.")
print("✅ ALIYUN_QWEN_KEY loaded successfully")

dashscope.api_key = DASHSCOPE_API_KEY
QWEN_MODEL = "qwen-plus"


def _detect_language(user_message: str, history_messages: list) -> str:
    """检测用户消息的语言"""
    import re
    
    english_chars = len(re.findall(r'[a-zA-Z]', user_message))
    total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', user_message))
    
    if total_chars == 0:
        return "zh"
    
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    
    if english_ratio > 0.7:
        user_messages_in_history = [msg for msg in history_messages if hasattr(msg, 'role') and msg.role == 'user']
        
        if len(user_messages_in_history) == 0:
            return "en"
        
        if len(user_messages_in_history) >= 1:
            recent_user_messages = [msg.content for msg in user_messages_in_history[-2:]]
            recent_english_count = 0
            for msg in recent_user_messages:
                msg_english = len(re.findall(r'[a-zA-Z]', msg))
                msg_total = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', msg))
                if msg_total > 0 and msg_english / msg_total > 0.7:
                    recent_english_count += 1
            
            if recent_english_count >= 1:
                return "en"
    
    return "zh"


def _build_messages(user_message: str, session: UserSession, system_prompt: str = None):
    """构建消息列表"""
    current_hour = datetime.now().hour
    history_messages = session.messages if hasattr(session, 'messages') else []
    current_turn = len(history_messages) + 1
    reply_language = _detect_language(user_message, history_messages)
    
    if system_prompt is None:
        system_prompt = get_system_prompt(session.user_name, session.kay_name)
    
    supported_emotions = get_all_emotions()
    emotions_str = "、".join(supported_emotions)
    
    messages = [{'role': 'system', 'content': system_prompt}]
    
    for msg in history_messages:
        role = msg.role if hasattr(msg, 'role') else 'user'
        content = msg.content if hasattr(msg, 'content') else ''
        messages.append({'role': role, 'content': content})
    
    time_context = ""
    if 23 <= current_hour or current_hour <= 5:
        time_context = f"【时间提示】：现在是深夜 {current_hour:02d}:00 左右。如果对话自然，可以适度表达一点困倦（不是必须），但依然保持陪伴。\n"
    
    language_instruction = ""
    if reply_language == "en":
        language_instruction = "\n⚠️ **语言要求**：用户正在使用英文对话，请**必须用英文回复**。"
    else:
        language_instruction = "\n⚠️ **语言要求**：请用中文回复。"
    
    final_user_prompt = f"""
{time_context}【对话元信息】：这是第 {current_turn} 轮对话。

【重要】大部分时候（90%）正常温柔回复即可，只在特定情境下（10%）适度表达脆弱感。
{language_instruction}

【用户的最新消息】：{user_message}

请完成以下任务，并**严格以 JSON 格式输出**：
1. 判断用户情绪（从以下选一个：{emotions_str}）
2. 以 {session.kay_name} 的身份回复（2-3句话，口语化，温柔自然）

输出格式（纯JSON，无其他内容）：
{{"reply": "Kay的回复", "emotion": "情绪标签"}}
"""
    messages.append({'role': 'user', 'content': final_user_prompt})
    
    return messages, reply_language


def generate_reply(user_message: str, session: UserSession, system_prompt: str = None):
    """
    生成回复（非流式，兼容旧代码）
    """
    default_reply_zh = "哎呀，我脑子卡壳了一下，能再说一遍吗？"
    default_reply_en = "Oops, my mind went blank for a moment. Could you say that again?"
    
    try:
        messages, reply_language = _build_messages(user_message, session, system_prompt)
        
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
        
        try:
            cleaned_output = raw_output.strip('```json').strip('```').strip()
            data = json.loads(cleaned_output)
            
            reply = data.get('reply', raw_output)
            detected_emotion = data.get('emotion', DEFAULT_EMOTION)
            
            supported_emotions = get_all_emotions()
            if detected_emotion not in supported_emotions:
                detected_emotion = DEFAULT_EMOTION
            
            return reply, detected_emotion
            
        except json.JSONDecodeError:
            print(f"警告：LLM 未输出标准 JSON。原始输出：{raw_output}")
            if reply_language == "en":
                return default_reply_en, DEFAULT_EMOTION
            return raw_output, DEFAULT_EMOTION
            
    except Exception as e:
        print(f"致命异常：{e}")
        print(traceback.format_exc())
        return default_reply_zh, DEFAULT_EMOTION


def generate_reply_stream(user_message: str, session: UserSession, 
                          system_prompt: str = None) -> Generator[Tuple[str, str, bool], None, None]:
    """
    流式生成回复
    
    Yields:
        Tuple[str, str, bool]: (文本片段, 情绪, 是否完成)
        - 中间过程: ("文本片段", "", False)
        - 最终结果: ("", "emotion", True)
    """
    try:
        messages, reply_language = _build_messages(user_message, session, system_prompt)
        
        # 流式调用
        responses = Generation.call(
            model=QWEN_MODEL,
            messages=messages,
            result_format='message',
            temperature=0.75,
            top_p=0.8,
            max_tokens=256,
            stream=True,  # 启用流式
            incremental_output=True  # 增量输出
        )
        
        full_response = ""
        
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                chunk = response.output.choices[0].message.content
                if chunk:
                    full_response += chunk
                    
                    # 尝试解析 JSON（可能还不完整）
                    # 先返回文本片段
                    # 注意：因为输出是 JSON 格式，我们需要特殊处理
                    
                    # 检查是否在 "reply": " 之后
                    if '"reply"' in full_response:
                        # 提取 reply 的内容
                        try:
                            # 尝试找到 reply 的值
                            start = full_response.find('"reply"')
                            if start != -1:
                                # 找到 reply 后的第一个引号
                                quote_start = full_response.find('"', start + 8)
                                if quote_start != -1:
                                    # 找到内容
                                    content_start = quote_start + 1
                                    # 尝试找到结束引号（但可能还没到）
                                    content_so_far = full_response[content_start:]
                                    # 移除可能的未完成部分
                                    if '"' in content_so_far:
                                        content_so_far = content_so_far[:content_so_far.find('"')]
                                    
                                    # 只输出新增的部分
                                    if hasattr(generate_reply_stream, '_last_content'):
                                        new_content = content_so_far[len(generate_reply_stream._last_content):]
                                    else:
                                        new_content = content_so_far
                                    
                                    generate_reply_stream._last_content = content_so_far
                                    
                                    if new_content:
                                        yield (new_content, "", False)
                        except:
                            pass
            else:
                print(f"Stream Error: {response.code} - {response.message}")
        
        # 清理状态
        if hasattr(generate_reply_stream, '_last_content'):
            delattr(generate_reply_stream, '_last_content')
        
        # 解析完整响应
        try:
            cleaned = full_response.strip('```json').strip('```').strip()
            data = json.loads(cleaned)
            emotion = data.get('emotion', DEFAULT_EMOTION)
            
            supported_emotions = get_all_emotions()
            if emotion not in supported_emotions:
                emotion = DEFAULT_EMOTION
            
            yield ("", emotion, True)
            
        except json.JSONDecodeError:
            print(f"警告：流式输出 JSON 解析失败：{full_response[:200]}")
            yield ("", DEFAULT_EMOTION, True)
            
    except Exception as e:
        print(f"流式生成异常：{e}")
        traceback.print_exc()
        yield ("出了点小问题，再说一遍？", DEFAULT_EMOTION, True)


# ============================================================
# 简化版流式输出（推荐使用）
# ============================================================

def generate_reply_stream_simple(user_message: str, session: UserSession,
                                  system_prompt: str = None) -> Generator[str, None, Tuple[str, str]]:
    """
    简化版流式生成（直接生成文本，不用 JSON 格式）
    
    Yields:
        str: 文本片段
    
    Returns:
        Tuple[str, str]: (完整回复, 情绪)
    """
    try:
        current_hour = datetime.now().hour
        history_messages = session.messages if hasattr(session, 'messages') else []
        current_turn = len(history_messages) + 1
        reply_language = _detect_language(user_message, history_messages)
        
        if system_prompt is None:
            system_prompt = get_system_prompt(session.user_name, session.kay_name)
        
        messages = [{'role': 'system', 'content': system_prompt}]
        
        for msg in history_messages:
            role = msg.role if hasattr(msg, 'role') else 'user'
            content = msg.content if hasattr(msg, 'content') else ''
            messages.append({'role': role, 'content': content})
        
        time_context = ""
        if 23 <= current_hour or current_hour <= 5:
            time_context = f"现在是深夜，可以适度表达一点困倦。"
        
        language_instruction = "用英文回复" if reply_language == "en" else "用中文回复"
        
        # 简化的 prompt（直接生成文本，不要 JSON）
        final_prompt = f"""
{time_context}
这是第 {current_turn} 轮对话。{language_instruction}。
直接用2-3句话温柔自然地回复，不要任何格式标记。

用户：{user_message}
"""
        messages.append({'role': 'user', 'content': final_prompt})
        
        # 流式调用
        responses = Generation.call(
            model=QWEN_MODEL,
            messages=messages,
            result_format='message',
            temperature=0.75,
            top_p=0.8,
            max_tokens=256,
            stream=True,
            incremental_output=True
        )
        
        full_response = ""
        
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                chunk = response.output.choices[0].message.content
                if chunk:
                    full_response += chunk
                    yield chunk
        
        # 单独调用一次获取情绪
        emotion = _detect_emotion(user_message, full_response)
        
        return full_response, emotion
        
    except Exception as e:
        print(f"流式生成异常：{e}")
        traceback.print_exc()
        yield "出了点小问题，再说一遍？"
        return "出了点小问题，再说一遍？", DEFAULT_EMOTION


def _detect_emotion(user_message: str, agent_reply: str) -> str:
    """检测情绪（单独调用，快速）"""
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        supported_emotions = get_all_emotions()
        
        response = client.chat.completions.create(
            model="qwen-turbo",  # 用快速模型
            messages=[{
                "role": "user",
                "content": f"判断以下对话中用户的情绪，只返回一个词：{', '.join(supported_emotions)}\n\n用户：{user_message}\n回复：{agent_reply}\n\n情绪："
            }],
            temperature=0.1,
            max_tokens=10
        )
        
        emotion = response.choices[0].message.content.strip()
        if emotion in supported_emotions:
            return emotion
        return DEFAULT_EMOTION
        
    except:
        return DEFAULT_EMOTION
