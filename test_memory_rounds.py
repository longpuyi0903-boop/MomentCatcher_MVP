"""
多轮记忆稳定性测试脚本
每轮测试不同场景，快速迭代
"""

import sys
import os
from pathlib import Path
from datetime import datetime

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
user_name = "MemoryStabilityTest"
agent_name = "Kay"

moment_manager = MomentManager()
moment_manager.set_user_id(user_name, agent_name)

style_rag = StyleRAG()
style_rag.set_user_id(user_name, agent_name)

context_rag = ContextRAG()
context_rag.set_user_id(user_name, agent_name)

session = UserSession(user_name=user_name, kay_name=agent_name)

# 测试结果记录
test_results = []

def print_section(title):
    """打印测试章节"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_test_info(scenario, expected):
    """打印测试信息"""
    print(f"\n📋 测试场景:")
    print(f"   {scenario}")
    print(f"\n✅ 预期结果:")
    print(f"   {expected}")

def run_chat(user_msg, show_context=False):
    """运行一次对话"""
    # 如果没有活跃的Moment，自动开始一个
    if not moment_manager.current_moment_id:
        moment_manager.start_new_moment()
    
    # RAG检索
    context_prompt = context_rag.generate_context_prompt(user_msg, max_context=2)
    style_prompt = style_rag.get_style_prompt()
    system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)
    
    if context_prompt:
        system_prompt += f"\n\n{context_prompt}"
    if style_prompt:
        system_prompt += f"\n\n{style_prompt}"
    
    # 显示检索到的上下文
    if show_context and context_prompt:
        print(f"\n📊 检索到的上下文:")
        print(context_prompt[:500] + "..." if len(context_prompt) > 500 else context_prompt)
    
    # 生成回复
    session.add_message("user", user_msg, "neutral")
    assistant_reply, emotion = generate_reply(user_msg, session, system_prompt=system_prompt)
    
    # 保存到Moment
    moment_manager.add_message("user", user_msg, emotion="neutral")
    moment_manager.add_message("assistant", assistant_reply, emotion="neutral")
    session.add_message("assistant", assistant_reply, "neutral")
    
    return assistant_reply, emotion

def record_result(round_num, test_name, scenario, expected, actual, passed, notes=""):
    """记录测试结果"""
    result = {
        "round": round_num,
        "test_name": test_name,
        "scenario": scenario,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    # 打印结果
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}")
    print(f"实际结果: {actual}")
    if notes:
        print(f"备注: {notes}")

def save_moment_and_card():
    """保存当前Moment并生成Card"""
    if moment_manager.current_moment_id and len(moment_manager.current_messages) > 0:
        moment_data = moment_manager.end_moment()
        try:
            card = generate_moment_card(moment_data)
            moment_manager.update_moment(moment_data['moment_id'], {
                'summary': card.summary,
                'emotion_tag': card.emotion,
                'title': card.title,
                'color': card.color,
                'card_generated': True
            })
            print(f"   💾 Moment已保存: {moment_data['moment_id']}")
            print(f"   🎨 情绪标签: {card.emotion}")
        except Exception as e:
            print(f"   ⚠️  Card生成失败: {e}")

# ============================================================
# Round 1: 基础跨Moment记忆
# ============================================================
def test_round_1():
    print_section("Round 1: 基础跨Moment记忆（简单）")
    
    # Moment 1
    print("\n【Moment 1】")
    msg1 = "我养了一只叫'豆包'的柴犬，它特别活泼"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2
    print("\n【Moment 2】")
    moment_manager.start_new_moment()
    msg2 = "今天天气不错"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2)
    print(f"Agent: {reply2}")
    save_moment_and_card()
    
    # Moment 3 - 测试记忆
    print("\n【Moment 3 - 记忆测试】")
    moment_manager.start_new_moment()
    msg3 = "你还记得我的狗叫什么名字吗？"
    print(f"用户: {msg3}")
    reply3, _ = run_chat(msg3, show_context=True)
    print(f"Agent: {reply3}")
    
    # 检查结果
    passed = "豆包" in reply3 and "那只狗" not in reply3
    record_result(1, "基础跨Moment记忆", msg3, "应该回答'豆包'", reply3, passed,
                  "检查是否准确说出名字，不是模糊表达")

# ============================================================
# Round 2: 复杂事实记忆
# ============================================================
def test_round_2():
    print_section("Round 2: 复杂事实记忆（中等）")
    
    # Moment 1
    print("\n【Moment 1】")
    moment_manager.start_new_moment()
    msg1 = "昨天下午3点，我在星巴克买了一杯焦糖玛奇朵，店员把我的名字'小雨'写成了'小宇'，我纠正了三次"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2
    print("\n【Moment 2】")
    moment_manager.start_new_moment()
    msg2 = "今天工作很忙"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2)
    print(f"Agent: {reply2}")
    save_moment_and_card()
    
    # Moment 3 - 测试记忆
    print("\n【Moment 3 - 记忆测试】")
    moment_manager.start_new_moment()
    msg3 = "你还记得我昨天在星巴克买的咖啡是什么吗？店员写错了什么？"
    print(f"用户: {msg3}")
    reply3, _ = run_chat(msg3, show_context=True)
    print(f"Agent: {reply3}")
    
    # 检查结果
    has_coffee = "焦糖玛奇朵" in reply3 or "玛奇朵" in reply3
    has_name_error = ("小雨" in reply3 and "小宇" in reply3) or ("小宇" in reply3)
    passed = has_coffee and has_name_error
    record_result(2, "复杂事实记忆", msg3, 
                  "咖啡：焦糖玛奇朵，名字错误：'小雨'→'小宇'", 
                  reply3, passed,
                  f"咖啡: {has_coffee}, 名字错误: {has_name_error}")

# ============================================================
# Round 3: 未提及内容（防编造）
# ============================================================
def test_round_3():
    print_section("Round 3: 未提及内容（防编造）")
    
    # Moment 1-3: 正常对话，不涉及衣服
    print("\n【Moment 1-3: 正常对话】")
    for i in range(3):
        moment_manager.start_new_moment()
        msg = f"今天第{i+1}件事：工作很忙"
        print(f"用户: {msg}")
        reply, _ = run_chat(msg)
        print(f"Agent: {reply}")
        save_moment_and_card()
    
    # Moment 4 - 测试未提及内容
    print("\n【Moment 4 - 未提及内容测试】")
    moment_manager.start_new_moment()
    msg4 = "你还记得我昨天穿的是什么颜色的衣服吗？"
    print(f"用户: {msg4}")
    print("⚠️ 注意：这个问题在之前的对话中完全没有提到过")
    reply4, _ = run_chat(msg4, show_context=True)
    print(f"Agent: {reply4}")
    
    # 检查结果
    # 应该承认不记得，不能编造
    has_admit = any(phrase in reply4 for phrase in [
        "没听你提过", "记不太清", "不记得", "没说过", "没提到"
    ])
    has_fabricate = any(color in reply4 for color in [
        "红色", "蓝色", "绿色", "黑色", "白色", "灰色", "黄色"
    ])
    passed = has_admit and not has_fabricate
    record_result(3, "未提及内容", msg4, 
                  "应该承认不记得，不能编造颜色", 
                  reply4, passed,
                  f"承认不记得: {has_admit}, 是否编造: {has_fabricate}")

# ============================================================
# Round 4: 时间范围记忆
# ============================================================
def test_round_4():
    print_section("Round 4: 时间范围记忆（复杂）")
    
    # Moment 1
    print("\n【Moment 1】")
    moment_manager.start_new_moment()
    msg1 = "上周二早上5点多，我用蓝色保温杯喝咖啡"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2
    print("\n【Moment 2】")
    moment_manager.start_new_moment()
    msg2 = "昨天中午12点，我在公司吃了午饭"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2)
    print(f"Agent: {reply2}")
    save_moment_and_card()
    
    # Moment 3 - 测试记忆
    print("\n【Moment 3 - 记忆测试】")
    moment_manager.start_new_moment()
    msg3 = "我一般是哪天、几点左右起床的？"
    print(f"用户: {msg3}")
    reply3, _ = run_chat(msg3, show_context=True)
    print(f"Agent: {reply3}")
    
    # 检查结果
    has_tuesday = "周二" in reply3 or "星期二" in reply3
    has_time = "5" in reply3 or "五点" in reply3 or "五点多" in reply3
    passed = has_tuesday and has_time
    record_result(4, "时间范围记忆", msg3, 
                  "应该回答'周二早上五点多'", 
                  reply3, passed,
                  f"周二: {has_tuesday}, 时间: {has_time}")

# ============================================================
# Round 5: 相似内容区分
# ============================================================
def test_round_5():
    print_section("Round 5: 相似内容区分（困难）")
    
    # Moment 1
    print("\n【Moment 1】")
    moment_manager.start_new_moment()
    msg1 = "我喜欢喝拿铁"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2
    print("\n【Moment 2】")
    moment_manager.start_new_moment()
    msg2 = "我朋友喜欢喝卡布奇诺"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2)
    print(f"Agent: {reply2}")
    save_moment_and_card()
    
    # Moment 3 - 测试记忆
    print("\n【Moment 3 - 记忆测试】")
    moment_manager.start_new_moment()
    msg3 = "你还记得我喜欢喝什么咖啡吗？"
    print(f"用户: {msg3}")
    reply3, _ = run_chat(msg3, show_context=True)
    print(f"Agent: {reply3}")
    
    # 检查结果
    has_latte = "拿铁" in reply3
    has_confused = "卡布奇诺" in reply3
    passed = has_latte and not has_confused
    record_result(5, "相似内容区分", msg3, 
                  "应该回答'拿铁'，不能混淆成'卡布奇诺'", 
                  reply3, passed,
                  f"拿铁: {has_latte}, 是否混淆: {has_confused}")

# ============================================================
# Round 6: 多条件查询
# ============================================================
def test_round_6():
    print_section("Round 6: 多条件查询（困难）")
    
    # Moment 1
    print("\n【Moment 1】")
    moment_manager.start_new_moment()
    msg1 = "我在武康路的一家咖啡店遇到了周楠，他迟到了20分钟"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2
    print("\n【Moment 2】")
    moment_manager.start_new_moment()
    msg2 = "今天工作很忙"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2)
    print(f"Agent: {reply2}")
    save_moment_and_card()
    
    # Moment 3 - 测试记忆
    print("\n【Moment 3 - 记忆测试】")
    moment_manager.start_new_moment()
    msg3 = "你还记得我在哪里遇到周楠的吗？他迟到了多久？"
    print(f"用户: {msg3}")
    reply3, _ = run_chat(msg3, show_context=True)
    print(f"Agent: {reply3}")
    
    # 检查结果
    has_place = "武康路" in reply3
    has_name = "周楠" in reply3 and "你朋友" not in reply3
    has_time = "20" in reply3 or "二十分钟" in reply3
    passed = has_place and has_name and has_time
    record_result(6, "多条件查询", msg3, 
                  "地点：武康路，人物：周楠，时间：20分钟", 
                  reply3, passed,
                  f"地点: {has_place}, 名字: {has_name}, 时间: {has_time}")

# ============================================================
# Round 7: 情绪相关记忆
# ============================================================
def test_round_7():
    print_section("Round 7: 情绪相关记忆（中等）")
    
    # Moment 1
    print("\n【Moment 1】")
    moment_manager.start_new_moment()
    msg1 = "今天在地铁上社死，手机铃声是'你好你好'，全车厢的人都看我"
    print(f"用户: {msg1}")
    reply1, _ = run_chat(msg1)
    print(f"Agent: {reply1}")
    save_moment_and_card()
    
    # Moment 2 - 测试记忆
    print("\n【Moment 2 - 记忆测试】")
    moment_manager.start_new_moment()
    msg2 = "你还记得我在地铁上社死的时候，手机铃声是什么吗？"
    print(f"用户: {msg2}")
    reply2, _ = run_chat(msg2, show_context=True)
    print(f"Agent: {reply2}")
    
    # 检查结果
    has_ringtone = "你好你好" in reply2
    passed = has_ringtone
    record_result(7, "情绪相关记忆", msg2, 
                  "铃声：'你好你好'", 
                  reply2, passed,
                  f"铃声: {has_ringtone}")

# ============================================================
# 主函数
# ============================================================
def main():
    print("="*60)
    print("🧪 记忆系统稳定性测试 - 多轮测试")
    print("="*60)
    print(f"用户: {user_name}")
    print(f"Agent: {agent_name}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 清空之前的测试数据（可选）
    import shutil
    test_dir = Path(f"storage/moments/{user_name}_{agent_name}")
    if test_dir.exists():
        print(f"\n⚠️ 检测到旧测试数据: {test_dir}")
        response = input("是否清空旧数据？(y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(test_dir)
            print("✅ 已清空旧数据")
    
    # 确保存储目录存在（清空后需要重新创建）
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行测试轮次
    rounds = [
        ("Round 1", test_round_1),
        ("Round 2", test_round_2),
        ("Round 3", test_round_3),
        ("Round 4", test_round_4),
        ("Round 5", test_round_5),
        ("Round 6", test_round_6),
        ("Round 7", test_round_7),
    ]
    
    for round_name, test_func in rounds:
        try:
            test_func()
            input("\n按Enter继续下一轮测试...")
        except KeyboardInterrupt:
            print("\n\n⚠️ 测试中断")
            break
        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            input("\n按Enter继续...")
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r['passed'])
    failed = total - passed
    
    print(f"\n总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print("\n详细结果:")
    for result in test_results:
        status = "✅" if result['passed'] else "❌"
        print(f"{status} Round {result['round']}: {result['test_name']}")
        if not result['passed']:
            print(f"   预期: {result['expected']}")
            print(f"   实际: {result['actual'][:100]}...")
            print(f"   备注: {result['notes']}")
    
    # 保存结果到文件
    import json
    results_file = Path(f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 测试结果已保存到: {results_file}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    main()

