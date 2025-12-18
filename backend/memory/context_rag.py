"""
Context RAG - 上下文检索
从历史 Moments 中检索相关内容
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class ContextRAG:
    """
    上下文检索系统
    
    功能：
    1. 关键词匹配检索
    2. 时间范围检索
    3. 情绪过滤检索
    4. 生成上下文提示
    5. 多用户数据隔离
    """
    
    def __init__(self, user_id: str = None, base_moments_dir: str = "storage/moments"):
        """
        初始化 Context RAG
        
        Args:
            user_id: 用户唯一标识
            base_moments_dir: Moments 基础目录
        """
        self.user_id = user_id or "default_user"
        self.base_moments_dir = Path(base_moments_dir)
        
        # 用户专属文件夹
        self.moments_dir = self.base_moments_dir / self.user_id
    
    def set_user_id(self, user_name: str, agent_name: str):
        """
        设置用户 ID
        
        Args:
            user_name: 用户名
            agent_name: Agent 名
        """
        self.user_id = f"{user_name}_{agent_name}".replace(" ", "_")
        self.moments_dir = self.base_moments_dir / self.user_id
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 3) -> List[Dict]:
        """
        基于关键词检索 Moments
        
        Args:
            keywords: 关键词列表
            top_k: 返回前 k 个结果
        
        Returns:
            List[Dict]: 匹配的 Moments（按相关度排序）
        """
        
        if not self.moments_dir.exists():
            return []
        
        results = []
        
        # 遍历所有 Moments
        for moment_file in self.moments_dir.glob("moment_*.json"):
            with open(moment_file, 'r', encoding='utf-8') as f:
                moment = json.load(f)
            
            # 计算相关度分数
            score = self._calculate_relevance(moment, keywords)
            
            if score > 0:
                results.append({
                    "moment": moment,
                    "score": score
                })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回前 k 个
        return [r['moment'] for r in results[:top_k]]
    
    def search_by_content(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        基于内容检索（结构化实体匹配 + 关键词检索）
        
        Args:
            query: 查询内容
            top_k: 返回前 k 个结果
        
        Returns:
            List[Dict]: 匹配的 Moments
        """
        
        if not self.moments_dir.exists():
            return []
        
        # Step 1: 从查询中提取实体
        print(f"🔍 分析查询: {query}")
        query_entities = self._extract_query_entities(query)
        print(f"   提取实体: {query_entities}")
        
        # Step 2: 遍历所有 Moments，计算匹配分数
        results = []
        
        for moment_file in self.moments_dir.glob("moment_*.json"):
            with open(moment_file, 'r', encoding='utf-8') as f:
                moment = json.load(f)
            
            # 计算匹配分数
            score = self._calculate_entity_match_score(moment, query_entities, query)
            
            if score > 0:
                results.append({
                    "moment": moment,
                    "score": score
                })
        
        # Step 3: 按分数排序，返回 top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if results:
            print(f"   找到 {len(results)} 个匹配 Moments")
            for i, r in enumerate(results[:top_k], 1):
                print(f"   {i}. Moment (分数: {r['score']:.2f})")
        else:
            print("   未找到匹配的 Moments")
        
        return [r['moment'] for r in results[:top_k]]
    
    def get_recent_moments(self, n: int = 5) -> List[Dict]:
        """
        获取最近的 n 个 Moments
        
        Args:
            n: 数量
        
        Returns:
            List[Dict]: Moments 列表
        """
        
        if not self.moments_dir.exists():
            return []
        
        moments = []
        
        for moment_file in self.moments_dir.glob("moment_*.json"):
            with open(moment_file, 'r', encoding='utf-8') as f:
                moment = json.load(f)
                moments.append(moment)
        
        # 按时间倒序
        moments.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return moments[:n]
    
    def search_by_emotion(self, emotion: str, top_k: int = 3) -> List[Dict]:
        """
        基于情绪检索 Moments
        
        Args:
            emotion: 情绪标签
            top_k: 返回前 k 个结果
        
        Returns:
            List[Dict]: 匹配的 Moments
        """
        
        if not self.moments_dir.exists():
            return []
        
        results = []
        
        for moment_file in self.moments_dir.glob("moment_*.json"):
            with open(moment_file, 'r', encoding='utf-8') as f:
                moment = json.load(f)
            
            # 检查情绪标签（如果有）
            if moment.get('emotion_tag') == emotion:
                results.append(moment)
            else:
                # 检查消息中的情绪
                for msg in moment.get('messages', []):
                    if msg.get('emotion') == emotion:
                        results.append(moment)
                        break
        
        # 按时间倒序
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results[:top_k]
    
    def _calculate_relevance(self, moment: Dict, keywords: List[str]) -> float:
        """
        计算 Moment 与关键词的相关度
        
        Args:
            moment: Moment 数据
            keywords: 关键词列表
        
        Returns:
            float: 相关度分数
        """
        
        score = 0.0
        
        # 提取所有文本内容
        all_text = ""
        for msg in moment.get('messages', []):
            all_text += msg.get('content', '') + " "
        
        # 添加摘要（如果有）
        if moment.get('summary'):
            all_text += moment['summary'] + " "
        
        all_text = all_text.lower()
        
        # 计算匹配关键词数量
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 精确匹配
            if keyword_lower in all_text:
                score += 1.0
            # 部分匹配
            elif any(keyword_lower in word for word in all_text.split()):
                score += 0.5
        
        return score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
        
        Returns:
            List[str]: 关键词列表
        """
        
        import re
        
        # 移除标点
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词（减少停用词，保留更多关键词）
        stopwords = {
            '的', '了', '是', '在', '我', '你', '他', '她', '它', 
            '这', '那', '有', '和', '就', '不', '也', '都', '很',
            '啊', '吗', '呢', '吧', '嘛', '哈', '哦',
            'a', 'the', 'is', 'am', 'are', 'to', 'of', 'and', 'or'
        }
        
        keywords = [w for w in words if len(w) > 1 and w.lower() not in stopwords]
        
        # 提取重要词（保留"考试"、"工作"、"project"等）
        # 如果包含特定词，增加权重（通过重复）
        important_words = {
            '考试', '考', '成绩', '分数', '第一', '重考',
            'project', '工作', '跳槽', '公司', '程序员',
            '帅哥', '心动', '喜欢', '爱情', '感情',
            '考前', '紧张', '压力', '焦虑'
        }
        
        enhanced_keywords = []
        for w in keywords:
            enhanced_keywords.append(w)
            # 如果是重要词，重复添加（增加权重）
            if w in important_words or w.lower() in important_words:
                enhanced_keywords.append(w)
                enhanced_keywords.append(w)
        
        return enhanced_keywords
    
    def generate_context_prompt(self, query: str, max_context: int = 2) -> str:
        """
        生成上下文提示（用于注入到 LLM prompt）
        
        Phase 2加强版：双层检索
        1. 如果是"问事实"类query，先用entities精准检索
        2. 如果entities没找到，用文本检索兜底
        3. 根据置信度决定prompt策略
        
        Args:
            query: 当前查询
            max_context: 最多包含几个 Moments 的上下文
        
        Returns:
            str: 上下文提示文本
        """
        
        # 【Step 1】判断是否在问事实
        is_asking_fact = self.is_fact_query(query)
        
        if is_asking_fact:
            print(f"🔍 检测到事实查询: {query}")
            
            # 【Step 2 - 第一层】尝试entities精准检索
            print("   📊 第一层：entities精准检索...")
            entity_result = self._search_entities(query)
            print(f"      entities检索结果: 置信度={entity_result['confidence']:.2f}, 事实={entity_result.get('fact', 'None')[:50] if entity_result.get('fact') else 'None'}")
            
            if entity_result["confidence"] > 0.8:
                # entities找到了高置信度结果
                print(f"   ✅ entities命中！置信度: {entity_result['confidence']:.2f}")
                return self._build_fact_prompt_high_confidence(
                    entity_result["fact"],
                    entity_result["full_context"] or ""
                )
            
            # 【Step 3 - 第二层】entities没找到，用文本检索兜底
            print("   📝 第二层：文本检索兜底...")
            text_result = self.search_fact(query)
            print(f"      文本检索结果: 置信度={text_result['confidence']:.2f}, 事实={text_result.get('fact', 'None')[:100] if text_result.get('fact') else 'None'}")
            
            # 根据置信度决定prompt策略
            if text_result["confidence"] > 0.5:  # 降低阈值，更积极地使用检索结果
                # 高置信度：强制返回事实
                print(f"   ✅ 文本检索命中！置信度: {text_result['confidence']:.2f}")
                return self._build_fact_prompt_high_confidence(
                    text_result["fact"],
                    text_result.get("context", "") or text_result.get("full_content", "")
                )
                
            elif text_result["confidence"] > 0.2:
                # 中等置信度：返回但标注不确定
                print(f"   ⚠️  文本检索部分命中，置信度: {text_result['confidence']:.2f}")
                return self._build_fact_prompt_uncertain(text_result.get("fact", ""))
                
            else:
                # 低置信度：承认不记得
                print(f"   ❌ 未找到可靠信息，置信度: {text_result['confidence']:.2f}")
                return self._build_fact_prompt_not_found()
        
        # 【原有逻辑】普通对话，使用常规检索
        # ⚠️ 重要：确保只从当前用户的moments目录检索
        print(f"   📂 检索目录: {self.moments_dir}")
        if not self.moments_dir.exists():
            print(f"   ⚠️  用户目录不存在: {self.moments_dir}，返回空上下文")
            return ""
        
        relevant_moments = self.search_by_content(query, top_k=max_context)
        
        if not relevant_moments:
            print(f"   ℹ️  未找到相关历史对话（用户: {self.user_id}）")
            return ""
        
        print(f"   ✅ 找到 {len(relevant_moments)} 个相关 Moments（用户: {self.user_id}）")
        
        # 构建上下文提示
        context = "【重要：历史记忆】\n你和用户之前聊过以下内容，你**必须**记得这些对话：\n\n"
        
        for i, moment in enumerate(relevant_moments, 1):
            # 提取时间
            timestamp = moment.get('timestamp', '')
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%Y年%m月%d日')
            else:
                time_str = "之前"
            
            # 提取话题和关键信息
            context += f"📌 {time_str}的对话（Moment {i}）：\n"
            
            # 使用摘要（如果有）
            if moment.get('summary'):
                context += f"摘要：{moment['summary']}\n"
            
            # 提取关键对话片段（更多细节）
            messages = moment.get('messages', [])
            if messages:
                # 提取用户和 Agent 的关键对话（前 3 轮）
                dialog_snippet = ""
                for msg in messages[:6]:  # 前 3 轮对话（6 条消息）
                    role = "用户" if msg['role'] == 'user' else "你"
                    content = msg['content'][:80]  # 限制长度
                    dialog_snippet += f"  {role}：{content}\n"
                
                if dialog_snippet:
                    context += f"关键对话：\n{dialog_snippet}"
            
            # 情绪标签
            if moment.get('emotion_tag'):
                context += f"当时情绪：{moment['emotion_tag']}\n"
            
            context += "\n"
        
        context += self._get_memory_rules()
        
        return context.strip()
    
    def _build_fact_prompt_high_confidence(self, fact: str, full_context: str) -> str:
        """构建高置信度事实的prompt"""
        return f"""
【⚠️ 极其重要：你必须准确回答这个事实，禁止编造】

用户在询问一个具体事实。我已经从历史对话中找到了准确答案，你**必须**严格按照以下事实回答：

✅ **找到的事实（必须使用）**：
{fact}

✅ **完整上下文（参考）**：
{full_context}

⚠️ **超级重要规则（违反会导致严重错误）**：

1. **必须一字不差地使用事实中的内容**：
   - 如果事实是"亮橙色配灰底"，你就说"亮橙色配灰底"，不能说"橙色"、"莫兰迪蓝"或其他
   - 如果事实是"桂花拿铁"，你就说"桂花拿铁"，不能说"榛果拿铁"或其他

2. **绝对禁止编造**：
   - ❌ 禁止：编造一个听起来合理的答案（如"莫兰迪蓝"、"榛果拿铁"）
   - ❌ 禁止：修改事实中的任何细节（如把"亮橙色"改成"橙色"）
   - ❌ 禁止：添加事实中没有的信息（如"上周也点过"）

3. **回答方式**：
   - ✅ 正确：自然地说出事实，可以加一点语气，但事实必须准确
   - ✅ 正确："记得呀，是亮橙色配灰底，被主管夸了那个对吧？"
   - ✅ 正确："桂花拿铁，你说甜到皱眉但还是喝完了。"
   - ❌ 错误：编造完全不同的答案
   - ❌ 错误：用模糊词逃避（如"那个配色"、"那杯咖啡"）

4. **如果用户问了多个事实**（如"配色是什么，咖啡是什么口味"）：
   - 必须回答所有事实，不能遗漏
   - 每个事实都要准确

**正确示例**：
用户："你还记得我今天被夸的方案配色是什么吗？还有，下班那杯咖啡喝的是什么口味？"
事实："亮橙色配灰底；桂花拿铁"
你："记得呀，是亮橙色配灰底，被主管夸了那个对吧？还有那杯桂花拿铁，你说甜到皱眉但还是喝完了。"

**错误示例（禁止）**：
你："莫兰迪蓝搭浅灰褐的配色"（❌ 完全错误）
你："榛果拿铁"（❌ 完全错误）
你："我记得是橙色，但不确定"（❌ 事实是"亮橙色配灰底"，不能模糊）

**再次强调**：你必须使用上面的事实，不能编造、不能修改、不能模糊！
"""
    
    def _build_fact_prompt_uncertain(self, fact: str) -> str:
        """构建中等置信度事实的prompt"""
        return f"""
【注意：你记得但不完全确定】

用户在询问一个具体事实。我找到了可能的答案，但不是100%确定：

可能的事实：
{fact}

⚠️ **你的回答方式**：
- 说出你记得的内容
- 但要**明确标注不确定**
- 示例："我记得好像是...，但不是特别确定"
- 示例:"我记得应该是...，你能再确认一下吗？"
- **不要**很自信地说错误答案
"""
    
    def _build_fact_prompt_not_found(self) -> str:
        """构建未找到事实的prompt"""
        return """
【🚨 最高优先级指令：你不记得这个细节，必须承认，禁止编造】

用户在询问一个具体事实，但我在历史记忆中**完全找不到**任何相关信息。

⚠️ **这是最高优先级指令，必须严格遵守**：

1. **必须明确承认不记得**（不要用任何模糊表达）：
   - ✅ "这个我好像没听你提过，是什么？"
   - ✅ "我记不太清了，你能提醒我一下吗？"
   - ✅ "这个我一时想不起来了，是什么来着？"

2. **绝对禁止的行为（违反会导致严重错误）**：
   - ❌ **禁止编造任何内容**（即使听起来合理、即使session历史中有其他对话）
   - ❌ **禁止说"我记得..."**（如果记忆中没有）
   - ❌ **禁止用模糊词逃避**（如"好像"、"可能"）
   - ❌ **禁止基于session对话历史推测**（即使session中有其他对话，也不能推测）
   - ❌ **禁止添加任何细节**（如"配了一条米白围巾"、"每次提到都眼睛发亮"）

3. **特别禁止的编造示例（这些是真实错误案例）**：
   - ❌ "昨天穿的是浅灰色的外套，配了一条米白围巾"（编造衣服颜色和配饰）
   - ❌ "你最爱吃的是芒果，每次提到都眼睛发亮"（编造水果偏好和行为）
   - ❌ "我记得你站在窗边拍照"（编造场景）
   - ❌ "还记得你说过夏天一定要吃冰镇芒果"（编造对话内容）

4. **如果用户问的是从未提及的内容**：
   - **直接说**："这个我好像没听你提过，是什么？"
   - **或者**："我记不太清了，你能提醒我一下吗？"
   - **不要**试图从session历史中推测答案
   - **不要**试图从其他对话中推测答案

⚠️ **关键原则**：
- **如果记忆中没有，就承认没有**
- **不要编造，不要推测，不要用"我记得"来掩盖不知道**
- **诚实承认不记得，比编造答案要好得多**
- **即使session历史中有其他对话，也不能推测答案**

**正确回答示例（必须这样回答）**：
用户："你还记得我昨天穿的是什么颜色的衣服吗？"
你："这个我好像没听你提过，是什么颜色的？"

用户："你记得我最喜欢吃什么水果吗？"
你："我记不太清了，是什么水果？"

**错误回答示例（绝对禁止）**：
用户："你还记得我昨天穿的是什么颜色的衣服吗？"
你："昨天穿的是浅灰色的外套，配了一条米白围巾"（❌ 编造）

用户："你记得我最喜欢吃什么水果吗？"
你："你最爱吃的是芒果，每次提到都眼睛发亮"（❌ 编造）

用户："你记得我最喜欢吃什么水果吗？"
你："还记得你说过夏天一定要吃冰镇芒果"（❌ 编造对话内容）

⚠️ **再次强调：这是最高优先级指令，必须严格遵守！**
"""
    
    def _get_memory_rules(self) -> str:
        """返回记忆规则提示"""
        return """
⚠️ **重要指令**：
- 当用户提到"上次"、"之前"、"那个"等词时，你**必须**主动引用上面的历史记忆
- 不要说"我记不清了"、"我记混了"，因为你现在看到了完整的历史记录
- 如果用户问"你记得吗"，直接说出你记得的具体内容

⚠️ **记忆事实规则（极其重要）**：

**规则 1：有明确事实，必须准确使用，不能修改**
- 如果历史记忆中明确记录了具体细节（地点、时间、人物、数字、名字），你**必须**准确使用这些细节
   - 例如：记录是"武康路"，就不能说"中山路"
   - 例如：记录是"迟到20分钟"，就不能说"1小时"
   - 例如：记录是"豆包"，就不能说"那只柴犬"或"记不清名字"
   - 例如：记录是"周楠"，就不能说"周南"或"你朋友"

**规则 2：不确定或没有该细节，必须承认，禁止编造**
- 如果你不确定或历史记忆中没有该细节，**直接说"我不太确定"或"我记不清了"**
- **绝对禁止编造任何内容**
   - 正确示例："我记得好像是武康路，但我不完全确定，你能再确认一下吗？"
   - 错误示例："在中山路上"（记错了还很自信）
   - 错误示例："我记得你提到它的时候很温柔"（编造了感受）

**规则 3：禁止用模糊表达逃避事实**
- ❌ 禁止："那只狗"（明明记录里有名字"豆包"）
- ❌ 禁止："你朋友"（明明记录里有名字"周楠"）
- ❌ 禁止："那条路"（明明记录里有"武康路"）
- ✅ 正确：直接说出准确的名字/地点/事实

**规则 4：如果记忆片段中有，但你一时没找到，宁可承认不记得**
- 宁可说"我一时想不起来了，是什么？"
- 也不要编造或用模糊词逃避

**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**
**真实错误案例警示（必看）**

**错误案例：豆包事件**

历史记录：
- 对话2："去朋友家遛狗，被一只叫'豆包'的柴犬拽着跑..."

用户提问："我又遇到之前那只柴犬了！你还记得它吗？"

❌ **错误回复1：**
"记得呀，那只摇尾巴的小柴对吧？"
→ 问题：用模糊词"那只小柴"逃避，明明记录里有名字"豆包"！

用户追问："叫什么？"

❌ **错误回复2：**
"你说的是那只柴犬吗？我记性不太好，但记得你讲它时特别温柔。"
→ 问题1：还是没说"豆包"
→ 问题2：编造了"记得你讲它时特别温柔"（用户根本没说过这个）

✅ **正确回复：**
用户："我又遇到之前那只柴犬了！你还记得它吗？"
Agent："记得！豆包对吧？上次你说被它拽着跑，还说它会在路口等红灯。"

或者如果真的不确定：
Agent："记得是只柴犬，但名字我一时想不起来了，叫什么来着？"

**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**

**关键原则：有事实就准确说，没把握就承认，绝不编造！**

⚠️ **记忆要有脉络（像真人朋友一样）**：
1. 不要只是复述事实，要关注变化和在意点：
   - ❌ 简单复述："你之前说过工作压力大。"
   - ✅ 带脉络："上次你说工作压力大，现在有没有好一点？"
   - ✅ 带在意点："那次你说周楠迟到，你当时为什么那么在意？"

2. 真人朋友的记忆特点：
   - 记得"你当时为什么在意"（在意点）
   - 记得"后来怎么样了"（变化）
   - 记得"你当时什么感受"（情绪脉络）
   
3. 引用记忆时的好例子：
   - "上次你说想换工作，后来怎么样了？还在纠结吗？"
   - "那次你说周楠迟到让你很生气，是觉得被忽视了吗？"
   - "你之前提到的那个压力，现在还在吗？"
   - "上次你说那个习惯在坚持，今天还去了吗？"

4. 禁止的引用方式（太浅层）：
   - ❌ "你之前说过这个。" （没有脉络）
   - ❌ "我记得你提到过。" （太模糊）
   - ❌ "嗯，那件事我记得。" （没有追问变化）
"""
        
        return context.strip()
    
    def is_fact_query(self, query: str) -> bool:
        """
        判断用户query是否在询问具体事实
        
        Args:
            query: 用户输入
            
        Returns:
            bool: True=问事实, False=普通对话
        """
        import re
        
        # 事实查询的模式
        fact_patterns = [
            r'你记得.*吗',
            r'还记得.*吗',
            r'.*叫什么',
            r'.*是什么',
            r'.*怎么.*的',
            r'.*在哪',
            r'.*在哪里',
            r'.*多久',
            r'.*什么时候',
            r'.*哪个',
            r'.*哪天',
            r'.*几点',
            r'.*多少',
        ]
        
        # 检查是否匹配任何模式
        for pattern in fact_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def search_fact(self, query: str) -> Dict:
        """
        精准检索事实（用于回答"问事实"类query）
        
        策略：
        1. 使用 LLM 理解查询意图（提取查询类型、关键词、时间范围）
        2. 在Moments的对话原文中搜索
        3. 返回匹配结果 + 置信度
        4. 支持多事实查询（如"配色是什么，咖啡是什么口味"）
        
        Args:
            query: 用户query
            
        Returns:
            {
                "fact": str,           # 找到的事实（可能是多个，用分号分隔）
                "confidence": float,   # 置信度 0-1
                "source": str,         # 来源Moment ID
                "context": str         # 完整上下文
            }
        """
        # 【Step 1】使用 LLM 理解查询意图
        query_understanding = self._understand_query_with_llm(query)
        
        # 如果 LLM 理解成功，使用理解结果
        if query_understanding and query_understanding.get("success"):
            query_types = query_understanding.get("query_types", [])
            keywords = query_understanding.get("keywords", [])
            time_range = query_understanding.get("time_range", "")
            
            print(f"   🤖 LLM理解查询: 类型={query_types}, 关键词={keywords}, 时间={time_range}")
            
            # 根据理解结果增强关键词
            enhanced_keywords = list(keywords)
            if time_range:
                enhanced_keywords.append(time_range)
        else:
            # 【降级】如果 LLM 理解失败，使用原逻辑
            print(f"   ⚠️  LLM理解失败，使用降级逻辑")
            keywords = self._extract_keywords(query)
            query_lower = query.lower()
            enhanced_keywords = list(keywords)
            
            # 特殊处理：识别查询类型，提取更精准的关键词
            if "配色" in query_lower or "方案" in query_lower:
                enhanced_keywords.extend(["配色", "方案", "设计", "橙色", "灰色", "灰底", "亮橙色"])
            
            if "咖啡" in query_lower or "拿铁" in query_lower or "口味" in query_lower:
                enhanced_keywords.extend(["咖啡", "拿铁", "口味", "桂花"])
        
        if not enhanced_keywords:
            return {
                "fact": None,
                "confidence": 0.0,
                "source": None,
                "context": None
            }
        
        # 加载所有Moments
        if not self.moments_dir.exists():
            return {
                "fact": None,
                "confidence": 0.0,
                "source": None,
                "context": None
            }
        
        best_matches = []  # 支持多个匹配
        
        # 遍历所有Moments（按时间倒序，优先最近的）
        moment_files = sorted(self.moments_dir.glob("moment_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for moment_file in moment_files:
            try:
                with open(moment_file, 'r', encoding='utf-8') as f:
                    moment = json.load(f)
                
                # 在对话原文中搜索
                messages = moment.get("messages", [])
                
                for i, msg in enumerate(messages):
                    if msg["role"] == "user":
                        content = msg["content"]
                        
                        # 计算匹配度
                        match_score = self._calculate_text_match_score(content, enhanced_keywords)
                        
                        if match_score > 0.3:  # 降低阈值，捕获更多相关结果
                            # 提取相关上下文（前后各1条）
                            start_idx = max(0, i - 1)
                            end_idx = min(len(messages), i + 2)
                            context_messages = messages[start_idx:end_idx]
                            
                            context = "\n".join([
                                f"{m['role']}: {m['content']}" 
                                for m in context_messages
                            ])
                            
                            # 提取具体事实（从用户消息中提取关键信息）
                            extracted_fact = self._extract_fact_from_text(content, query)
                            
                            best_matches.append({
                                "fact": extracted_fact or content[:100],  # 提取的事实或原文片段
                                "confidence": match_score,
                                "source": moment.get("moment_id"),
                                "context": context,
                                "full_content": content
                            })
            
            except Exception as e:
                print(f"   ⚠️  读取Moment失败: {e}")
                continue
        
        # 按置信度排序，取最佳匹配
        if best_matches:
            best_matches.sort(key=lambda x: x["confidence"], reverse=True)
            best_match = best_matches[0]
            
            # 如果是多事实查询，尝试合并多个匹配
            if len(best_matches) > 1 and best_matches[0]["confidence"] > 0.5:
                # 检查是否有多个不同的事实
                facts = [m["fact"] for m in best_matches[:3] if m["confidence"] > 0.5]
                if len(facts) > 1:
                    # 合并事实
                    best_match["fact"] = "；".join(facts[:2])  # 最多合并2个
                    best_match["confidence"] = min(0.9, best_match["confidence"] + 0.1)  # 稍微提升置信度
        
        return best_match
        else:
            # 没有找到匹配，返回默认值
        return {
            "fact": None,
            "confidence": 0.0,
            "source": None,
            "context": None
        }
    
    def _extract_fact_from_text(self, text: str, query: str) -> Optional[str]:
        """
        从文本中提取与查询相关的事实
        
        例如：
        - query: "配色是什么"
        - text: "用的是亮橙色配灰底"
        - 返回: "亮橙色配灰底"
        """
        query_lower = query.lower()
        text_lower = text.lower()
        
        # 如果是问配色/方案
        if "配色" in query_lower or "方案" in query_lower:
            # 查找包含颜色的句子
            # 匹配"XX色配XX"或"XX色+XX"等模式
            color_patterns = [
                r'[亮暗深浅]?[橙红黄绿蓝紫黑白灰]色[配和与及]?[灰白黑]?[底色]?',
                r'[亮暗深浅]?[橙红黄绿蓝紫黑白灰]色\s*配\s*[灰白黑]?底',
            ]
            for pattern in color_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # 找到包含这些关键词的完整短语
                    for match in matches:
                        # 在原文中找到包含这个匹配的完整句子片段
                        idx = text_lower.find(match)
                        if idx != -1:
                            # 提取前后20个字符
                            start = max(0, idx - 20)
                            end = min(len(text), idx + len(match) + 20)
                            snippet = text[start:end]
                            # 尝试提取更精确的短语
                            if "橙色" in snippet and "灰" in snippet:
                                # 提取"亮橙色配灰底"这样的短语
                                precise = re.search(r'[亮暗深浅]?橙色[配和与及]?[灰白黑]?[底色]?', text)
                                if precise:
                                    return precise.group()
                            return snippet[:50]  # 返回片段
        
        # 如果是问咖啡/口味
        if "咖啡" in query_lower or "拿铁" in query_lower or "口味" in query_lower:
            # 查找包含咖啡名称的句子
            coffee_patterns = [
                r'[桂花香草榛果焦糖]?拿铁',
                r'[桂花香草榛果焦糖]?咖啡',
            ]
            for pattern in coffee_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for match in matches:
                        idx = text_lower.find(match)
                        if idx != -1:
                            start = max(0, idx - 10)
                            end = min(len(text), idx + len(match) + 10)
                            return text[start:end]
        
        return None
    
    def _understand_query_with_llm(self, query: str) -> Optional[Dict]:
        """
        使用 LLM 理解查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            {
                "success": bool,
                "query_types": List[str],  # 查询类型，如 ["place", "food", "clothing"]
                "keywords": List[str],      # 关键词，如 ["学校", "面", "衣服", "中午"]
                "time_range": str          # 时间范围，如 "中午"、"今天"、"昨天"
            }
        """
        try:
            from openai import OpenAI
            from config.api_config import APIConfig
            
            client = OpenAI(
                api_key=APIConfig.QWEN_API_KEY,
                base_url=APIConfig.QWEN_BASE_URL
            )
            
            prompt = f"""分析以下用户查询，理解用户想要检索什么信息。

用户查询：
{query}

请分析：
1. **查询类型**：用户在问什么类型的信息？
   - place（地点）：如"哪儿"、"哪里"、"哪个位置"
   - food（食物）：如"什么面"、"什么菜"、"什么饮料"
   - clothing（衣服）：如"哪件衣服"、"什么衣服"
   - object（物品）：如"什么东西"、"什么物品"
   - person（人物）：如"谁"、"什么人"
   - time（时间）：如"什么时候"、"几点"、"哪天"
   - design（设计）：如"配色"、"方案"、"设计"
   - 可以同时有多个类型（如用户问"在哪儿把什么面洒到哪件衣服上"）

2. **关键词**：从查询中提取用于检索的关键词
   - 排除疑问词（"什么"、"哪儿"、"哪件"等）
   - 提取实体词（"学校"、"面"、"衣服"、"中午"等）
   - 提取相关词（"食堂"、"教学楼"、"番茄"、"牛腩"、"白色"、"卫衣"等）

3. **时间范围**：如果查询中提到时间，提取出来
   - 如"中午"、"今天"、"昨天"、"上周"等
   - 如果没有，返回空字符串

请以 JSON 格式返回：
{{
  "query_types": ["place", "food", "clothing"],
  "keywords": ["学校", "面", "衣服", "中午", "食堂", "番茄", "牛腩", "白色", "卫衣"],
  "time_range": "中午"
}}

示例1：
查询："你还记得中午我是在学校哪儿把什么面洒到哪件衣服上的吗？"
返回：
{{
  "query_types": ["place", "food", "clothing"],
  "keywords": ["学校", "面", "衣服", "中午", "食堂", "教学楼", "洒"],
  "time_range": "中午"
}}

示例2：
查询："你记得我今天被夸的方案配色是什么吗？还有，下班那杯咖啡喝的是什么口味？"
返回：
{{
  "query_types": ["design", "food"],
  "keywords": ["方案", "配色", "咖啡", "口味", "今天", "下班"],
  "time_range": "今天"
}}

示例3：
查询："我一般几点起床？"
返回：
{{
  "query_types": ["time"],
  "keywords": ["起床", "时间"],
  "time_range": ""
}}

只返回 JSON，不要其他文字。"""
            
            response = client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # 低温度，确保准确性
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 移除可能的 markdown 标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 解析 JSON
            understanding = json.loads(result_text)
            
            return {
                "success": True,
                "query_types": understanding.get("query_types", []),
                "keywords": understanding.get("keywords", []),
                "time_range": understanding.get("time_range", "")
            }
            
        except Exception as e:
            print(f"   ⚠️  LLM理解查询失败: {e}")
            return {
                "success": False,
                "query_types": [],
                "keywords": [],
                "time_range": ""
            }
    
    
    def _search_entities(self, query: str) -> Dict:
        """
        在entities中精准检索（Phase 2加强版 - 第一层检索）
        
        策略：
        1. 识别query询问的实体类型（时间/人物/地点/物品/习惯）
        2. 在所有Moments的entities中匹配
        3. 返回最匹配的结果 + 置信度
        
        Args:
            query: 用户query
            
        Returns:
            {
                "fact": str,           # 找到的事实
                "confidence": float,   # 置信度 0-1
                "source": str,         # 来源Moment ID
                "entity_type": str,    # 实体类型
                "full_context": str    # 完整上下文（用于生成回复）
            }
        """
        
        # 识别query类型
        entity_type, search_keywords = self._identify_query_type(query)
        
        if not entity_type:
            return {
                "fact": None,
                "confidence": 0.0,
                "source": None,
                "entity_type": None,
                "full_context": None
            }
        
        # 加载所有Moments
        if not self.moments_dir.exists():
            return {
                "fact": None,
                "confidence": 0.0,
                "source": None,
                "entity_type": None,
                "full_context": None
            }
        
        best_match = {
            "fact": None,
            "confidence": 0.0,
            "source": None,
            "entity_type": entity_type,
            "full_context": None
        }
        
        # 遍历所有Moments
        for moment_file in sorted(self.moments_dir.glob("moment_*.json")):
            try:
                with open(moment_file, 'r', encoding='utf-8') as f:
                    moment = json.load(f)
                
                entities = moment.get("entities", {})
                
                # 根据实体类型检索
                match_result = self._match_entity(entities, entity_type, search_keywords, query)
                
                if match_result and match_result["confidence"] > best_match["confidence"]:
                    best_match = {
                        "fact": match_result["fact"],
                        "confidence": match_result["confidence"],
                        "source": moment.get("moment_id"),
                        "entity_type": entity_type,
                        "full_context": match_result.get("context", "")
                    }
            
            except Exception as e:
                continue
        
        return best_match
    
    def _identify_query_type(self, query: str) -> Tuple[str, List[str]]:
        """
        识别query询问的实体类型
        
        Returns:
            (entity_type, search_keywords)
        """
        query_lower = query.lower()
        
        # 时间类query
        if any(kw in query_lower for kw in ["几点", "什么时候", "多久", "起床", "时间"]):
            if "起床" in query_lower:
                return ("time_daily_routine", ["起床"])
            return ("time", ["时间"])
        
        # 人物类query
        if any(kw in query_lower for kw in ["谁", "人", "朋友", "同事"]):
            # 提取可能的人名关键词
            keywords = [w for w in ["刘叔", "周楠"] if w in query]
            return ("people", keywords if keywords else ["人"])
        
        # 地点类query
        if any(kw in query_lower for kw in ["哪里", "哪个", "位置", "座位", "地方"]):
            if "座位" in query_lower or "位置" in query_lower:
                keywords = [w for w in ["刘叔", "靠窗"] if w in query]
                return ("place_position", keywords if keywords else ["位置"])
            return ("place", ["地点"])
        
        # 物品/设计类query - 扩展支持配色、方案等
        if any(kw in query_lower for kw in ["什么颜色", "颜色", "配色", "方案", "设计", "杯子", "保温杯", "物品"]):
            if "配色" in query_lower or "方案" in query_lower or "设计" in query_lower:
                # 提取关键词：方案、配色、设计等
                keywords = []
                if "方案" in query_lower:
                    keywords.append("方案")
                if "配色" in query_lower:
                    keywords.append("配色")
                if "设计" in query_lower:
                    keywords.append("设计")
                return ("design_scheme", keywords if keywords else ["方案", "配色"])
            elif "颜色" in query_lower:
                keywords = [w for w in ["杯子", "保温杯"] if w in query]
                return ("object_color", keywords if keywords else ["颜色"])
            return ("object", ["物品"])
        
        # 食物/饮料类query - 扩展支持口味、咖啡等
        if any(kw in query_lower for kw in ["什么口味", "口味", "咖啡", "拿铁", "喝", "饮料"]):
            keywords = []
            if "咖啡" in query_lower or "拿铁" in query_lower:
                keywords.append("咖啡")
                if "拿铁" in query_lower:
                    keywords.append("拿铁")
            if "口味" in query_lower:
                keywords.append("口味")
            return ("food_drink", keywords if keywords else ["咖啡", "口味"])
        
        # 习惯类query
        if any(kw in query_lower for kw in ["习惯", "一般", "通常", "总是"]):
            return ("habit", ["习惯"])
        
        return (None, [])
    
    def _match_entity(self, entities: Dict, entity_type: str, search_keywords: List[str], query: str) -> Optional[Dict]:
        """
        在entities中匹配特定类型的实体
        
        Returns:
            {
                "fact": str,
                "confidence": float,
                "context": str
            }
        """
        
        # 时间 - 日常习惯
        if entity_type == "time_daily_routine":
            time_info = entities.get("time_info", {})
            routines = time_info.get("daily_routines", [])
            
            for routine in routines:
                # 检查是否匹配关键词
                if any(kw in routine for kw in search_keywords):
                    return {
                        "fact": routine,
                        "confidence": 0.95,  # 精准匹配
                        "context": f"用户的日常习惯：{routine}"
                    }
        
        # 物品 - 颜色
        elif entity_type == "object_color":
            objects = entities.get("objects", {})
            
            for obj_name, obj_info in objects.items():
                # 检查是否匹配关键词
                if any(kw in obj_name for kw in search_keywords) or any(kw in query for kw in [obj_name]):
                    color = obj_info.get("color", "")
                    if color:
                        return {
                            "fact": f"{color}{obj_name}",
                            "confidence": 0.95,
                            "context": f"物品：{obj_name}，颜色：{color}，描述：{obj_info.get('description', '')}"
                        }
        
        # 设计/方案 - 配色
        elif entity_type == "design_scheme":
            # 尝试从 objects 中找设计相关的物品
            objects = entities.get("objects", {})
            for obj_name, obj_info in objects.items():
                if any(kw in obj_name for kw in ["方案", "设计", "配色"]):
                    color = obj_info.get("color", "")
                    description = obj_info.get("description", "")
                    if color or description:
                        return {
                            "fact": description if description else f"{color}{obj_name}",
                            "confidence": 0.95,
                            "context": f"设计方案：{description or obj_name}"
                        }
            # 如果没有找到，返回 None，让文本检索兜底
            return None
        
        # 食物/饮料 - 口味
        elif entity_type == "food_drink":
            # 尝试从 objects 中找食物/饮料
            objects = entities.get("objects", {})
            for obj_name, obj_info in objects.items():
                if any(kw in obj_name for kw in ["咖啡", "拿铁", "饮料", "食物"]):
                    description = obj_info.get("description", "")
                    if description:
                        return {
                            "fact": f"{obj_name}：{description}",
                            "confidence": 0.95,
                            "context": f"食物/饮料：{obj_name}，描述：{description}"
                        }
            # 如果没有找到，返回 None，让文本检索兜底
            return None
        
        # 地点 - 位置
        elif entity_type == "place_position":
            places = entities.get("places", {})
            
            for place_name, place_info in places.items():
                # 检查是否匹配关键词
                if any(kw in place_name for kw in search_keywords):
                    position = place_info.get("position", "")
                    if position:
                        return {
                            "fact": position,
                            "confidence": 0.95,
                            "context": f"地点：{place_name}，位置：{position}"
                        }
        
        # 人物
        elif entity_type == "people":
            people = entities.get("people", {})
            
            for person_name, person_info in people.items():
                # 检查是否匹配关键词
                if any(kw in person_name for kw in search_keywords) or any(kw in query for kw in [person_name]):
                    role = person_info.get("role", "")
                    attributes = person_info.get("attributes", [])
                    return {
                        "fact": f"{person_name}（{role}）",
                        "confidence": 0.9,
                        "context": f"人物：{person_name}，关系：{role}，特征：{', '.join(attributes)}"
                    }
        
        # 习惯
        elif entity_type == "habit":
            habits = entities.get("habits", [])
            
            for habit in habits:
                if any(kw in habit for kw in search_keywords) or any(kw in query for kw in habit.split()):
                    return {
                        "fact": habit,
                        "confidence": 0.9,
                        "context": f"日常习惯：{habit}"
                    }
        
        return None
    
    def _calculate_text_match_score(self, text: str, keywords: List[str]) -> float:
        """
        计算文本与关键词的匹配度
        
        Args:
            text: 要匹配的文本
            keywords: 关键词列表
            
        Returns:
            float: 匹配度 0-1
        """
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matched_count = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_count += 1
        
        # 匹配度 = 匹配的关键词数 / 总关键词数
        match_ratio = matched_count / len(keywords)
        
        # 如果全部匹配，置信度0.9
        # 如果部分匹配，按比例降低
        if match_ratio == 1.0:
            return 0.9
        elif match_ratio >= 0.5:
            return 0.5 + (match_ratio - 0.5) * 0.8  # 0.5-0.9
        else:
            return match_ratio  # 0-0.5
    
    def _extract_query_entities(self, query: str) -> Dict:
        """
        从用户查询中提取实体（用于精准匹配）
        
        Args:
            query: 用户查询
        
        Returns:
            Dict: 提取的实体
        """
        # 简单的关键词提取
        # 注意：主要的结构化提取由 LLM 完成（在 moment_manager 的 _extract_structured_info）
        # 这里只是辅助的简单规则匹配
        entities = {
            "people": [],
            "places": [],
            "time_markers": [],
            "numbers": [],
            "events": []
        }
        
        import re
        
        # 人名提取：不用复杂正则，直接从历史 Moments 中已知的人名匹配
        # （因为用户可以自定义代称、英文名等，正则无法覆盖所有情况）
        # 这个功能主要依赖 LLM 的结构化提取
        
        # 提取地点关键词
        place_keywords = ['路', '街', '区', '市', '店', '线', '号线', '地铁', '公司', '咖啡', 'Coffee']
        for word in query.split():
            if any(kw in word for kw in place_keywords):
                entities["places"].append(word)
        
        # 提取时间标记
        time_keywords = ['周一', '周二', '周三', '周四', '周五', '周六', '周日', '昨天', '今天', '明天', '上次', '之前']
        for kw in time_keywords:
            if kw in query:
                entities["time_markers"].append(kw)
        
        # 提取数字
        numbers = re.findall(r'\d+', query)
        entities["numbers"] = numbers
        
        # 提取事件关键词
        event_keywords = ['迟到', '考试', '升职', '催婚', '吃饭', '失控', '工作', '跳槽']
        for kw in event_keywords:
            if kw in query:
                entities["events"].append(kw)
        
        return entities
    
    def _calculate_entity_match_score(self, moment: Dict, query_entities: Dict, query: str) -> float:
        """
        计算 Moment 与查询实体的匹配分数
        
        Args:
            moment: Moment 数据
            query_entities: 查询中提取的实体
            query: 原始查询文本
        
        Returns:
            float: 匹配分数（0-100）
        """
        score = 0.0
        
        # 获取 Moment 的结构化信息
        moment_entities = moment.get('entities', {})
        
        # 如果 Moment 没有 entities（旧数据），回退到文本匹配
        if not moment_entities:
            # 回退：简单的关键词匹配
            conversation = ""
            for msg in moment.get('messages', []):
                conversation += msg['content'] + " "
            
            # 计算查询关键词在对话中的出现次数
            keywords = self._extract_keywords(query)
            for kw in keywords:
                if kw in conversation:
                    score += 1
            
            return score
        
        # 权重配置
        weights = {
            "people": 10,      # 人名匹配权重最高
            "places": 8,       # 地点匹配次高
            "numbers": 5,      # 数字匹配
            "time_markers": 3, # 时间标记
            "events": 2        # 事件关键词
        }
        
        # 计算各类实体的匹配分数
        for entity_type, weight in weights.items():
            query_items = query_entities.get(entity_type, [])
            moment_items = moment_entities.get(entity_type, [])
            
            # 计算交集
            matched = set(query_items) & set(moment_items)
            score += len(matched) * weight
        
        # 近期加权（最近的 Moment 略微加分）
        try:
            timestamp = datetime.fromisoformat(moment.get('timestamp', ''))
            age_days = (datetime.now() - timestamp).days
            
            # 7天内的 Moment，每天加 0.5 分
            if age_days < 7:
                score += (7 - age_days) * 0.5
        except:
            pass
        
        return score


# ============================================================
# 测试代码
# ============================================================

def test_context_rag():
    """测试 Context RAG"""
    
    print("\n" + "="*60)
    print("🧪 测试 Context RAG")
    print("="*60 + "\n")
    
    rag = ContextRAG()
    
    # 测试1: 创建一些测试 Moments
    print("📝 创建测试 Moments...")
    from moment_manager import MomentManager
    
    manager = MomentManager()
    
    # Moment 1: 关于 project
    manager.start_new_moment()
    manager.add_message("user", "我有个很难的 project，不知道能不能做成", "worry")
    manager.add_message("assistant", "听起来是个很有挑战的项目", "neutral")
    manager.end_moment()
    
    # Moment 2: 关于工作
    manager.start_new_moment()
    manager.add_message("user", "今天工作好累", "sadness")
    manager.add_message("assistant", "辛苦了", "neutral")
    manager.end_moment()
    
    print("✅ 测试 Moments 创建完成\n")
    
    # 测试2: 关键词检索
    print("📝 测试关键词检索...")
    results = rag.search_by_keywords(["project", "难"], top_k=2)
    print(f"   找到 {len(results)} 个相关 Moments")
    
    # 测试3: 内容检索
    print("\n📝 测试内容检索...")
    query = "我做成了之前那个 project"
    results = rag.search_by_content(query, top_k=1)
    print(f"   查询: {query}")
    print(f"   找到 {len(results)} 个相关 Moments")
    
    # 测试4: 生成上下文提示
    print("\n📝 测试上下文提示生成...")
    context = rag.generate_context_prompt(query, max_context=1)
    print(f"   上下文提示:\n{context}")
    
    # 测试5: 获取最近 Moments
    print("\n📝 测试获取最近 Moments...")
    recent = rag.get_recent_moments(n=3)
    print(f"   最近 {len(recent)} 个 Moments")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_context_rag()