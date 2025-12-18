"""
Gradio App v3 - 带 Landing Page
新增功能:
1. Landing Page（启动时输入名字）
2. 名字持久化存储
"""

import os
import json
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

# 导入后端模块
from backend.agent.reply_generator import generate_reply
from backend.audio.tts_engine import text_to_speech
from backend.memory.moment_manager import MomentManager
from backend.memory.moment_card import generate_moment_card
from backend.memory.style_rag import StyleRAG
from backend.memory.context_rag import ContextRAG
from config.persona_config import get_system_prompt

# 加载环境变量
load_dotenv()

# 初始化管理器
moment_manager = MomentManager()
style_rag = StyleRAG()
context_rag = ContextRAG()

# 全局状态
current_moment_active = False
user_name = "Traveler"
agent_name = "Kay"

# 名字存储路径
NAMES_FILE = Path("storage/user_data/names.json")


def load_saved_names():
    """加载保存的名字"""
    if NAMES_FILE.exists():
        with open(NAMES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('user_name', 'Traveler'), data.get('agent_name', 'Kay')
    return 'Traveler', 'Kay'


def save_names(user, agent):
    """保存名字到文件"""
    NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(NAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'user_name': user,
            'agent_name': agent
        }, f, ensure_ascii=False, indent=2)


def initiate_link(traveler_name, companion_name):
    """
    Landing Page: 初始化连接
    
    Returns:
        tuple: (main_interface_visible, landing_page_visible, chatbot_with_greeting, status, markdown_title, audio_label)
    """
    global user_name, agent_name
    
    # 验证输入
    if not traveler_name.strip():
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            gr.update(),
            "⚠️ Please enter your Traveler ID",
            gr.update(),
            gr.update()
        )
    
    if not companion_name.strip():
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            gr.update(),
            "⚠️ Please enter your Companion ID",
            gr.update(),
            gr.update()
        )
    
    # 更新全局变量
    user_name = traveler_name.strip()
    agent_name = companion_name.strip()
    
    # 设置用户 ID 到各个管理器（实现数据隔离）
    moment_manager.set_user_id(user_name, agent_name)
    style_rag.set_user_id(user_name, agent_name)
    context_rag.set_user_id(user_name, agent_name)  # Context RAG 也需要设置
    
    # 保存到文件
    save_names(user_name, agent_name)
    
    # 生成问候语
    from config.persona_config import get_greeting
    greeting = get_greeting(user_name, agent_name)
    
    # 初始对话历史（问候语）
    initial_history = [
        {"role": "assistant", "content": greeting}
    ]
    
    # 状态消息
    status_msg = f"✨ Link Initiated\n\nTraveler: {user_name}\nCompanion: {agent_name}\n\n💡 点击「开始新 Moment」开始记录"
    
    # 更新界面标签
    title_update = gr.update(value=f"### 与 {agent_name} 对话")
    audio_label_update = gr.update(label=f"{agent_name} 的回复（语音）")
    
    return (
        gr.update(visible=True),      # main_interface
        gr.update(visible=False),     # landing_page
        initial_history,              # chatbot with greeting
        status_msg,                   # status_box
        title_update,                 # conversation title
        audio_label_update            # audio label
    )


def start_new_moment():
    """开始新的 Moment"""
    global current_moment_active
    
    moment_manager.start_new_moment()
    current_moment_active = True
    
    # 生成新问候语
    from config.persona_config import get_greeting
    greeting = get_greeting(user_name, agent_name)
    
    # 返回带问候语的对话历史
    initial_history = [
        {"role": "assistant", "content": greeting}
    ]
    
    # 返回：对话历史, 状态提示, 清空音频
    return initial_history, "✨ 已开始新 Moment，可以开始对话了", None


def chat_with_rag(user_message, history):
    """带 RAG 的对话函数"""
    global current_moment_active
    
    if not user_message.strip():
        return history, None, "⚠️ 请输入消息"
    
    # 如果没有活跃的 Moment，自动开始一个
    if not current_moment_active:
        moment_manager.start_new_moment()
        current_moment_active = True
    
    # 1. 学习用户风格
    style_rag.learn_from_message(user_message)
    
    # 2. 检索相关历史上下文
    context_prompt = context_rag.generate_context_prompt(user_message, max_context=2)
    
    # 3. 获取风格提示
    style_prompt = style_rag.get_style_prompt()
    
    # 4. 构建完整 prompt
    system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)
    
    # 添加 RAG 上下文
    if context_prompt:
        system_prompt += f"\n\n{context_prompt}"
    
    if style_prompt:
        system_prompt += f"\n\n{style_prompt}"
    
    # 5. 生成回复
    from data_model.user_session import UserSession
    
    # 创建临时 session（包含对话历史）
    temp_session = UserSession(user_name=user_name, kay_name=agent_name)
    
    # 将 history 转换为 session.messages 格式
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        temp_session.add_message(role, content, "neutral")
    
    # 调用 generate_reply（传入包含RAG上下文的system_prompt）
    assistant_reply, detected_emotion = generate_reply(
        user_message=user_message,
        session=temp_session,
        system_prompt=system_prompt
    )
    
    # 6. 保存到当前 Moment
    moment_manager.add_message("user", user_message, emotion="neutral")
    moment_manager.add_message("assistant", assistant_reply, emotion="neutral")
    
    # 7. 生成语音
    audio_path = None
    try:
        audio_path = text_to_speech(assistant_reply)
    except Exception as e:
        print(f"⚠️ TTS 生成失败: {e}")
    
    # 8. 更新历史（新版 Gradio 格式）
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_reply})
    
    status = f"💬 已添加到当前 Moment（共 {len(moment_manager.current_messages)} 条消息）"
    
    return history, audio_path, status


def save_current_moment():
    """保存当前 Moment 并生成 Moment Card"""
    global current_moment_active
    
    if not current_moment_active:
        return "⚠️ 当前没有活跃的 Moment"
    
    if len(moment_manager.current_messages) == 0:
        return "⚠️ 当前 Moment 没有对话，无法保存"
    
    try:
        # 1. 结束 Moment
        moment_data = moment_manager.end_moment()
        current_moment_active = False
        
        # 2. 生成 Moment Card
        card = generate_moment_card(moment_data)
        
        # 3. 更新 Moment 数据（添加 Card 信息）
        moment_manager.update_moment(moment_data['moment_id'], {
            'summary': card.summary,
            'emotion_tag': card.emotion,
            'title': card.title,
            'color': card.color,
            'card_generated': True
        })
        
        # 4. 返回结果
        result = f"""
✅ Moment 已保存！

📇 Moment Card
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {card.timestamp[:10]}
🎭 {card.emotion.upper()}

✨ {card.title}

{card.summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 Moment ID: {card.moment_id}
💬 消息数: {card.message_count}

💡 切换到「📚 Memories」Tab 查看所有 Moments
        """
        
        return result
        
    except Exception as e:
        current_moment_active = False
        return f"❌ 保存失败: {e}"


def view_all_memories():
    """查看所有 Memories"""
    
    moments = moment_manager.get_all_moments()
    
    if not moments:
        return "📭 还没有任何 Moments\n\n点击「开始新 Moment」并开始对话吧！"
    
    # Step 1: 反转列表，让最早的在前（用于编号）
    moments_for_numbering = list(reversed(moments))
    
    # Step 2: 给每个 Moment 分配编号（Moment 1 = 最早的）
    numbered_moments = []
    for i, moment in enumerate(moments_for_numbering, 1):
        moment['display_number'] = i
        numbered_moments.append(moment)
    
    # Step 3: 反转回来用于显示（最新的在上）
    display_moments = list(reversed(numbered_moments))
    
    result = f"📚 Memories ({len(moments)} fragments found)\n\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Step 4: 显示（最新的 Moment 4 在最上面）
    for moment in display_moments:
        # 提取信息
        number = moment['display_number']
        timestamp = moment.get('timestamp', '')[:10]
        emotion = moment.get('emotion_tag') or 'neutral'
        emotion = emotion.upper() if emotion else 'NEUTRAL'
        title = moment.get('title', f"Moment {number}")
        summary = moment.get('summary', '（未生成 Moment Card）')
        message_count = moment.get('message_count', 0)
        
        result += f"📇 Moment {number}\n"
        result += f"📅 {timestamp}  🎭 {emotion}\n\n"
        result += f"✨ {title}\n\n"
        result += f"{summary}\n\n"
        result += f"💬 {message_count} 条消息\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    return result


def reset_names(new_user_name, new_agent_name):
    """
    更新名字
    
    Returns:
        tuple: (status, title_update, audio_label_update)
    """
    global user_name, agent_name
    
    if new_user_name.strip():
        user_name = new_user_name.strip()
    
    if new_agent_name.strip():
        agent_name = new_agent_name.strip()
    
    # 保存
    save_names(user_name, agent_name)
    
    # 更新用户 ID
    moment_manager.set_user_id(user_name, agent_name)
    style_rag.set_user_id(user_name, agent_name)
    context_rag.set_user_id(user_name, agent_name)
    
    # 更新界面标签
    title_update = gr.update(value=f"### 与 {agent_name} 对话")
    audio_label_update = gr.update(label=f"{agent_name} 的回复（语音）")
    
    status = f"✅ 已更新：你是 {user_name}，Agent 是 {agent_name}\n\n💡 名字已同步到界面"
    
    return status, title_update, audio_label_update


# ============================================================
# Gradio 界面
# ============================================================

# 加载保存的名字
saved_user, saved_agent = load_saved_names()

# 自定义 CSS
custom_css = """
.landing-page {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.landing-title {
    font-family: 'Courier New', monospace;
    font-size: 3em;
    letter-spacing: 0.3em;
    text-align: center;
    color: #e0e0e0;
    margin-bottom: 2em;
}

.landing-input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #e0e0e0 !important;
    font-family: 'Courier New', monospace !important;
}

.initiate-btn {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    font-family: 'Courier New', monospace !important;
    letter-spacing: 0.2em !important;
}
"""

with gr.Blocks(title="Moment Catcher", css=custom_css) as app:
    
    # ========================================
    # Landing Page
    # ========================================
    
    with gr.Group(visible=True) as landing_page:
        gr.Markdown("# MOMENT CATCHER", elem_classes="landing-title")
        
        with gr.Column():
            gr.Markdown("### TRAVELER ID")
            traveler_input = gr.Textbox(
                placeholder="Your Name",  # placeholder 虚值
                show_label=False,
                elem_classes="landing-input"
            )
            
            gr.Markdown("### COMPANION ID")
            companion_input = gr.Textbox(
                placeholder="AI Name",  # placeholder 虚值
                show_label=False,
                elem_classes="landing-input"
            )
            
            initiate_btn = gr.Button(
                "INITIATE LINK",
                variant="primary",
                elem_classes="initiate-btn"
            )
    
    # ========================================
    # 主界面
    # ========================================
    
    with gr.Group(visible=False) as main_interface:
        
        gr.Markdown("# 🌟 Moment Catcher")
        gr.Markdown("*带 RAG 记忆系统的 AI 陪伴 Agent*")
        
        with gr.Tab("💬 对话"):
            
            conversation_title = gr.Markdown("### 与 Kay 对话")  # 动态标题
            
            status_box = gr.Textbox(
                label="状态",
                value="💡 点击「开始新 Moment」开始记录",
                interactive=False
            )
            
            chatbot = gr.Chatbot(
                label="对话历史",
                height=400
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    label="你的消息",
                    placeholder="输入消息...",
                    scale=4
                )
                send_btn = gr.Button("发送", variant="primary", scale=1)
            
            audio_output = gr.Audio(
                label="Kay 的回复（语音）",  # 默认值，会被动态更新
                autoplay=True,
                type="filepath"
            )
            
            with gr.Row():
                start_moment_btn = gr.Button("✨ 开始新 Moment", variant="secondary")
                save_moment_btn = gr.Button("💾 保存 Moment", variant="primary")
            
            # 按钮事件
            start_moment_btn.click(
                fn=start_new_moment,
                outputs=[chatbot, status_box, audio_output]  # 顺序：对话框, 状态, 音频
            )
            
            send_btn.click(
                fn=chat_with_rag,
                inputs=[user_input, chatbot],
                outputs=[chatbot, audio_output, status_box]
            ).then(
                fn=lambda: "",
                outputs=user_input
            )
            
            user_input.submit(
                fn=chat_with_rag,
                inputs=[user_input, chatbot],
                outputs=[chatbot, audio_output, status_box]
            ).then(
                fn=lambda: "",
                outputs=user_input
            )
            
            save_moment_btn.click(
                fn=save_current_moment,
                outputs=status_box
            )
        
        with gr.Tab("📚 Memories"):
            
            gr.Markdown("### 你的 Moment 记忆")
            
            memories_display = gr.Textbox(
                label="所有 Moments",
                lines=20,
                interactive=False
            )
            
            refresh_btn = gr.Button("🔄 刷新", variant="primary")
            
            refresh_btn.click(
                fn=view_all_memories,
                outputs=memories_display
            )
        
        with gr.Tab("⚙️ 设置"):
            
            gr.Markdown("### 自定义名字")
            
            with gr.Row():
                user_name_input = gr.Textbox(
                    label="你的名字",
                    value=saved_user,
                    placeholder="Traveler"
                )
                agent_name_input = gr.Textbox(
                    label="Agent 名字",
                    value=saved_agent,
                    placeholder="Kay"
                )
            
            update_names_btn = gr.Button("✅ 更新名字", variant="primary")
            
            names_status = gr.Textbox(
                label="状态",
                interactive=False
            )
            
            update_names_btn.click(
                fn=reset_names,
                inputs=[user_name_input, agent_name_input],
                outputs=[names_status, conversation_title, audio_output]
            )
            
            gr.Markdown("---")
            gr.Markdown("### 风格画像")
            
            style_display = gr.Textbox(
                label="你的语言风格",
                lines=10,
                interactive=False
            )
            
            def show_style_profile():
                profile = style_rag.get_style_profile()
                
                if profile['total_messages'] == 0:
                    return "📭 还没有学习到你的风格\n\n多聊几句，我就能学会你的说话方式了！"
                
                result = f"""
📊 你的语言风格画像

总消息数: {profile['total_messages']}
平均句长: {profile['avg_sentence_length']} 字
英文比例: {profile['english_ratio'] * 100:.1f}%
风格描述: {profile['style_description']}

常用词汇:
{', '.join(profile['top_words'][:10])}

常用短语:
{', '.join(profile['top_phrases'][:5])}
"""
                
                if profile['top_emojis']:
                    result += f"\n常用 emoji:\n{''.join(profile['top_emojis'])}"
                
                return result
            
            show_style_btn = gr.Button("🔍 查看风格画像")
            
            show_style_btn.click(
                fn=show_style_profile,
                outputs=style_display
            )
    
    # ========================================
    # Landing Page 事件
    # ========================================
    
    initiate_btn.click(
        fn=initiate_link,
        inputs=[traveler_input, companion_input],
        outputs=[
            main_interface,      # 主界面可见性
            landing_page,        # Landing Page 可见性
            chatbot,             # 对话历史（带问候语）
            status_box,          # 状态栏
            conversation_title,  # 对话标题（动态 Agent 名）
            audio_output         # 音频标签（动态 Agent 名）
        ]
    )


# ============================================================
# 启动应用
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌟 Moment Catcher - MVP v3")
    print("="*60)
    print("📝 新功能:")
    print("   ✅ Landing Page（名字输入）")
    print("   ✅ Moment 会话管理")
    print("   ✅ 保存 Moment 并生成 Moment Card")
    print("   ✅ 查看所有 Memories")
    print("   ✅ RAG 上下文注入")
    print("   ✅ 风格学习")
    print("="*60 + "\n")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )