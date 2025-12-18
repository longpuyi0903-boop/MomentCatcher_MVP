"""
Style RAG - 风格学习
分析用户对话风格，让 Agent 逐渐模仿
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from collections import Counter


class StyleRAG:
    """
    用户风格学习系统
    
    功能：
    1. 统计用户常用词汇
    2. 分析句子长度偏好
    3. 检测中英混合程度
    4. 识别 emoji 使用习惯
    5. 提取常用短语
    6. 多用户数据隔离
    """
    
    def __init__(self, user_id: str = None, base_storage_path: str = "storage/user_data"):
        """
        初始化 Style RAG
        
        Args:
            user_id: 用户唯一标识
            base_storage_path: 基础存储路径
        """
        self.user_id = user_id or "default_user"
        self.base_storage_path = Path(base_storage_path)
        
        # 用户专属文件
        self.storage_path = self.base_storage_path / f"{self.user_id}_style.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有风格数据
        self.style_data = self._load_style()
    
    def set_user_id(self, user_name: str, agent_name: str):
        """
        设置用户 ID
        
        Args:
            user_name: 用户名
            agent_name: Agent 名
        """
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        self.storage_path = self.base_storage_path / f"{self.user_id}_style.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 重新加载该用户的风格数据
        self.style_data = self._load_style()
    
    def _load_style(self) -> Dict:
        """加载风格数据"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "vocabulary": {},  # 词频统计
                "sentence_lengths": [],
                "english_ratio": 0.0,
                "emoji_usage": {},
                "common_phrases": {},
                "total_messages": 0
            }
    
    def _save_style(self):
        """保存风格数据"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.style_data, f, ensure_ascii=False, indent=2)
    
    def learn_from_message(self, message: str):
        """
        从单条消息中学习风格
        
        Args:
            message: 用户消息
        """
        
        # 1. 统计词频
        words = self._tokenize(message)
        for word in words:
            self.style_data['vocabulary'][word] = \
                self.style_data['vocabulary'].get(word, 0) + 1
        
        # 2. 记录句子长度
        self.style_data['sentence_lengths'].append(len(message))
        
        # 3. 计算英文比例
        english_chars = len(re.findall(r'[a-zA-Z]', message))
        total_chars = len(message)
        if total_chars > 0:
            current_ratio = english_chars / total_chars
            # 移动平均
            old_ratio = self.style_data['english_ratio']
            total_msgs = self.style_data['total_messages']
            new_ratio = (old_ratio * total_msgs + current_ratio) / (total_msgs + 1)
            self.style_data['english_ratio'] = new_ratio
        
        # 4. 统计 emoji
        emojis = re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', message)
        for emoji in emojis:
            self.style_data['emoji_usage'][emoji] = \
                self.style_data['emoji_usage'].get(emoji, 0) + 1
        
        # 5. 提取常用短语（2-3 个字的组合）
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2])
            if len(phrase) > 2:  # 过滤太短的
                self.style_data['common_phrases'][phrase] = \
                    self.style_data['common_phrases'].get(phrase, 0) + 1
        
        # 更新消息计数
        self.style_data['total_messages'] += 1
        
        # 保存
        self._save_style()
    
    def learn_from_messages(self, messages: List[str]):
        """从多条消息中学习"""
        for msg in messages:
            self.learn_from_message(msg)
    
    def get_style_profile(self) -> Dict:
        """
        获取用户风格画像
        
        Returns:
            Dict: 风格特征
        """
        
        # 统计平均句长
        avg_length = (
            sum(self.style_data['sentence_lengths']) / 
            len(self.style_data['sentence_lengths'])
            if self.style_data['sentence_lengths'] else 0
        )
        
        # 提取高频词（前 20）
        vocab_counter = Counter(self.style_data['vocabulary'])
        top_words = [word for word, _ in vocab_counter.most_common(20)]
        
        # 提取常用短语（前 10）
        phrase_counter = Counter(self.style_data['common_phrases'])
        top_phrases = [phrase for phrase, _ in phrase_counter.most_common(10)]
        
        # 提取常用 emoji（前 5）
        emoji_counter = Counter(self.style_data['emoji_usage'])
        top_emojis = [emoji for emoji, _ in emoji_counter.most_common(5)]
        
        profile = {
            "avg_sentence_length": round(avg_length, 1),
            "english_ratio": round(self.style_data['english_ratio'], 2),
            "top_words": top_words,
            "top_phrases": top_phrases,
            "top_emojis": top_emojis,
            "total_messages": self.style_data['total_messages'],
            "style_description": self._generate_description()
        }
        
        return profile
    
    def _generate_description(self) -> str:
        """生成风格描述"""
        
        avg_length = (
            sum(self.style_data['sentence_lengths']) / 
            len(self.style_data['sentence_lengths'])
            if self.style_data['sentence_lengths'] else 0
        )
        
        english_ratio = self.style_data['english_ratio']
        
        descriptions = []
        
        # 句长描述
        if avg_length < 15:
            descriptions.append("简洁")
        elif avg_length < 30:
            descriptions.append("适中")
        else:
            descriptions.append("详细")
        
        # 中英混合描述
        if english_ratio > 0.3:
            descriptions.append("中英混合")
        elif english_ratio > 0.1:
            descriptions.append("偶尔英文")
        else:
            descriptions.append("纯中文")
        
        # Emoji 描述
        emoji_count = sum(self.style_data['emoji_usage'].values())
        if emoji_count > self.style_data['total_messages'] * 0.5:
            descriptions.append("爱用 emoji")
        elif emoji_count > 0:
            descriptions.append("偶尔 emoji")
        else:
            descriptions.append("少用 emoji")
        
        return "、".join(descriptions)
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词（中英文）"""
        # 移除标点和 emoji
        text = re.sub(r'[^\w\s]', ' ', text)
        # 分词
        words = text.split()
        # 过滤停用词和单字符
        stopwords = {'的', '了', '是', '在', '我', '你', '他', '她', '它', 
                     'a', 'the', 'is', 'am', 'are', 'to', 'of'}
        words = [w for w in words if len(w) > 1 and w.lower() not in stopwords]
        return words
    
    def get_style_prompt(self) -> str:
        """
        生成风格提示（用于注入到 LLM prompt）
        
        Returns:
            str: 风格提示文本
        """
        
        if self.style_data['total_messages'] < 5:
            return ""  # 样本太少，不生成提示
        
        profile = self.get_style_profile()
        
        prompt = f"""
用户风格特征：
- 句子长度：{profile['avg_sentence_length']} 字左右
- 语言风格：{profile['style_description']}
"""
        
        if profile['top_words']:
            top_words_str = '、'.join(profile['top_words'][:5])
            prompt += f"- 常用词汇：{top_words_str}\n"
        
        if profile['top_phrases']:
            top_phrases_str = '、'.join(profile['top_phrases'][:3])
            prompt += f"- 常用短语：{top_phrases_str}\n"
        
        if profile['top_emojis']:
            prompt += f"- 常用 emoji：{''.join(profile['top_emojis'])}\n"
        
        prompt += "\n请在回复时适度模仿用户的语言风格，让对话更自然。"
        
        return prompt.strip()


# ============================================================
# 测试代码
# ============================================================

def test_style_rag():
    """测试 Style RAG"""
    
    print("\n" + "="*60)
    print("🧪 测试 Style RAG")
    print("="*60 + "\n")
    
    style = StyleRAG()
    
    # 模拟用户消息
    test_messages = [
        "我有个很难的 project，不知道能不能做成",
        "是一个 AI Agent 项目，技术栈很复杂",
        "我担心搞不定，毕竟 deadline 很紧",
        "今天又遇到 bug 了，超级烦 😤",
        "finally 解决了！开心 😊",
        "下次要 early start，不能再拖了"
    ]
    
    print("📝 学习用户风格...")
    style.learn_from_messages(test_messages)
    
    print("\n📊 风格画像：")
    profile = style.get_style_profile()
    for key, value in profile.items():
        print(f"   {key}: {value}")
    
    print("\n💬 风格提示：")
    print(style.get_style_prompt())
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_style_rag()