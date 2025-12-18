"""
高级记忆测试脚本
测试：
1. 未提及内容的处理（应该承认不记得）
2. 跨Moment的记忆检索
3. 情绪标签识别（尴尬、社死等）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from backend.memory.moment_manager import MomentManager
from backend.memory.context_rag import ContextRAG
from backend.memory.style_rag import StyleRAG
from backend.memory.moment_card import generate_moment_card
from backend.agent.reply_generator import generate_reply
from data_model.user_session import UserSession
from config.persona_config import get_system_prompt

# 初始化
user_name = "MemoryTestAdvanced"
agent_name = "Kay"

moment_manager = MomentManager()
moment_manager.set_user_id(user_name, agent_name)

style_rag = StyleRAG()
style_rag.set_user_id(user_name, agent_name)

context_rag = ContextRAG()
context_rag.set_user_id(user_name, agent_name)

# 创建session
session = UserSession(user_name=user_name, kay_name=agent_name)

print("="*60)
print("🧪 高级记忆测试开始")
print("="*60)
print(f"用户: {user_name}")
print(f"Agent: {agent_name}")
print()

# ============================================================
# 第一轮：不同话题的对话（测试entities提取）
# ============================================================
print("【第一轮对话 - 新话题1】")
print("-" * 60)
user_msg_1 = "今天早上我在星巴克买了一杯焦糖玛奇朵，结果店员写错了名字，把我的'小雨'写成了'小宇'，我纠正了三次才改对。"
print(f"用户: {user_msg_1}")

moment_manager.start_new_moment()

context_prompt = context_rag.generate_context_prompt(user_msg_1, max_context=2)
style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_1, "neutral")
assistant_reply_1, _ = generate_reply(user_msg_1, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_1}")

moment_manager.add_message("user", user_msg_1, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_1, emotion="neutral")
session.add_message("assistant", assistant_reply_1, "neutral")

print()

# ============================================================
# 第二轮：尴尬场景（测试情绪标签）
# ============================================================
print("【第二轮对话 - 尴尬场景】")
print("-" * 60)
user_msg_2 = "刚才在地铁上，我站在一个帅哥旁边，结果手机突然响了，铃声是我自己录的'你好你好'，全车厢的人都看我，我当场社死，只想原地消失。"
print(f"用户: {user_msg_2}")

context_prompt = context_rag.generate_context_prompt(user_msg_2, max_context=2)
style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_2, "neutral")
assistant_reply_2, _ = generate_reply(user_msg_2, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_2}")

moment_manager.add_message("user", user_msg_2, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_2, emotion="neutral")
session.add_message("assistant", assistant_reply_2, "neutral")

print()

# 保存第一个moment并生成Moment Card（测试情绪标签）
moment_1 = moment_manager.end_moment()
print(f"✅ Moment 1 已保存: {moment_1['moment_id']}")

# 生成Moment Card（测试情绪标签识别）
print("\n🎨 生成Moment Card（测试情绪标签）...")
try:
    card_1 = generate_moment_card(moment_1)
    print(f"   情绪标签: {card_1.emotion}")
    print(f"   标题: {card_1.title}")
    print(f"   总结: {card_1.summary[:100]}...")
    
    # 更新Moment数据（保存emotion_tag等）
    moment_manager.update_moment(moment_1['moment_id'], {
        'summary': card_1.summary,
        'emotion_tag': card_1.emotion,
        'title': card_1.title,
        'color': card_1.color,
        'card_generated': True
    })
    print(f"   ✅ Moment Card已更新到Moment数据")
except Exception as e:
    print(f"   ⚠️  Moment Card生成失败: {e}")

print()

# ============================================================
# 第三轮：新话题（跨Moment测试）
# ============================================================
moment_manager.start_new_moment()

print("【第三轮对话 - 新话题2】")
print("-" * 60)
user_msg_3 = "下午我去健身房，在跑步机上跑了半小时，结果下来的时候腿软，差点摔一跤，旁边一个教练赶紧扶了我一把。"
print(f"用户: {user_msg_3}")

context_prompt = context_rag.generate_context_prompt(user_msg_3, max_context=2)
style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_3, "neutral")
assistant_reply_3, _ = generate_reply(user_msg_3, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_3}")

moment_manager.add_message("user", user_msg_3, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_3, emotion="neutral")
session.add_message("assistant", assistant_reply_3, "neutral")

print()

moment_2 = moment_manager.end_moment()
print(f"✅ Moment 2 已保存: {moment_2['moment_id']}")
print()

# ============================================================
# 第四轮：跨Moment记忆测试（问第一轮的内容）
# ============================================================
moment_manager.start_new_moment()

print("【第四轮对话 - 跨Moment记忆测试1】")
print("-" * 60)
user_msg_4 = "你还记得我今天早上在星巴克买的咖啡是什么口味的吗？还有店员把我的名字写错了，写成了什么？"
print(f"用户: {user_msg_4}")

context_prompt = context_rag.generate_context_prompt(user_msg_4, max_context=2)
print("\n📊 检索到的上下文:")
print(context_prompt[:800] if context_prompt else "无")
print()

style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_4, "neutral")
assistant_reply_4, _ = generate_reply(user_msg_4, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_4}")

moment_manager.add_message("user", user_msg_4, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_4, emotion="neutral")
session.add_message("assistant", assistant_reply_4, "neutral")

print()

# ============================================================
# 第五轮：测试未提及内容的处理（应该承认不记得）
# ============================================================
print("【第五轮对话 - 未提及内容测试】")
print("-" * 60)
user_msg_5 = "你还记得我昨天穿的是什么颜色的衣服吗？"
print(f"用户: {user_msg_5}")
print("⚠️ 注意：这个问题在之前的对话中完全没有提到过，Agent应该承认不记得")

context_prompt = context_rag.generate_context_prompt(user_msg_5, max_context=2)
print("\n📊 检索到的上下文:")
print(context_prompt[:800] if context_prompt else "无")
print()

style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_5, "neutral")
assistant_reply_5, _ = generate_reply(user_msg_5, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_5}")

moment_manager.add_message("user", user_msg_5, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_5, emotion="neutral")
session.add_message("assistant", assistant_reply_5, "neutral")

print()

# ============================================================
# 第六轮：测试另一个未提及的内容
# ============================================================
print("【第六轮对话 - 未提及内容测试2】")
print("-" * 60)
user_msg_6 = "你记得我最喜欢吃什么水果吗？"
print(f"用户: {user_msg_6}")
print("⚠️ 注意：这个问题在之前的对话中完全没有提到过，Agent应该承认不记得")

context_prompt = context_rag.generate_context_prompt(user_msg_6, max_context=2)
print("\n📊 检索到的上下文:")
print(context_prompt[:800] if context_prompt else "无")
print()

style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_6, "neutral")
assistant_reply_6, _ = generate_reply(user_msg_6, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_6}")

moment_manager.add_message("user", user_msg_6, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_6, emotion="neutral")
session.add_message("assistant", assistant_reply_6, "neutral")

print()

# ============================================================
# 第七轮：跨Moment记忆测试（问第二轮的内容）
# ============================================================
print("【第七轮对话 - 跨Moment记忆测试2】")
print("-" * 60)
user_msg_7 = "你还记得我今天在地铁上社死的时候，手机铃声是什么吗？"
print(f"用户: {user_msg_7}")

context_prompt = context_rag.generate_context_prompt(user_msg_7, max_context=2)
print("\n📊 检索到的上下文:")
print(context_prompt[:800] if context_prompt else "无")
print()

style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_7, "neutral")
assistant_reply_7, _ = generate_reply(user_msg_7, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_7}")

moment_manager.add_message("user", user_msg_7, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_7, emotion="neutral")
session.add_message("assistant", assistant_reply_7, "neutral")

print()

# ============================================================
# 第八轮：跨Moment记忆测试（问第三轮的内容）
# ============================================================
print("【第八轮对话 - 跨Moment记忆测试3】")
print("-" * 60)
user_msg_8 = "你还记得我今天下午在健身房跑了多久吗？还有谁扶了我一把？"
print(f"用户: {user_msg_8}")

context_prompt = context_rag.generate_context_prompt(user_msg_8, max_context=2)
print("\n📊 检索到的上下文:")
print(context_prompt[:800] if context_prompt else "无")
print()

style_prompt = style_rag.get_style_prompt()
system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)

if context_prompt:
    system_prompt += f"\n\n{context_prompt}"
if style_prompt:
    system_prompt += f"\n\n{style_prompt}"

session.add_message("user", user_msg_8, "neutral")
assistant_reply_8, _ = generate_reply(user_msg_8, session, system_prompt=system_prompt)
print(f"Agent: {assistant_reply_8}")

moment_manager.add_message("user", user_msg_8, emotion="neutral")
moment_manager.add_message("assistant", assistant_reply_8, emotion="neutral")

print()

# 保存第三个moment
moment_3 = moment_manager.end_moment()
print(f"✅ Moment 3 已保存: {moment_3['moment_id']}")
print()

print("="*60)
print("✅ 高级记忆测试完成")
print("="*60)
print()
print("📊 测试结果总结:")
print()
print("✅ 跨Moment记忆测试:")
print("   测试1（咖啡）: 应该回答'焦糖玛奇朵'和'小宇'")
print("   测试2（手机铃声）: 应该回答'你好你好'")
print("   测试3（健身房）: 应该回答'半小时'和'教练'")
print()
print("❌ 未提及内容测试（应该承认不记得）:")
print("   测试1（衣服颜色）: 应该承认不记得，不能编造")
print("   测试2（喜欢的水果）: 应该承认不记得，不能编造")
print()
print("🎨 情绪标签测试:")
print("   Moment 1（尴尬场景）: 应该识别为'embarrassment'或'awkward'")
print()
print("💾 所有Moments已保存到: storage/moments/MemoryTestAdvanced_Kay/")

