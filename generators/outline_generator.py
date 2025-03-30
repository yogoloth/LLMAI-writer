import json
from models.ai_model import AIModel

class OutlineGenerator:
    """小说大纲生成器"""

    def __init__(self, ai_model: AIModel, config_manager):
        """
        初始化大纲生成器

        Args:
            ai_model: AI模型实例
            config_manager: 配置管理器实例
        """
        self.ai_model = ai_model
        self.config_manager = config_manager

    async def generate_outline(self, title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, protagonist_count, important_count, supporting_count, minor_count, callback=None):
        """
        生成小说大纲

        Args:
            title: 小说标题
            genre: 小说类型
            theme: 小说主题
            style: 小说风格
            synopsis: 小说简介
            volume_count: 卷数
            chapters_per_volume: 每卷章节数
            words_per_chapter: 每章字数
            protagonist_count: 主角数量
            important_count: 重要角色数量
            supporting_count: 配角数量
            minor_count: 龙套数量
            callback: 回调函数，用于接收流式生成的内容

        Returns:
            生成的大纲（JSON格式）
        """
        prompt = self._create_outline_prompt(title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, protagonist_count, important_count, supporting_count, minor_count)
        max_tokens = None
        temperature = None

        if callback:
            # 流式生成
            full_response = ""
            async for chunk in self.ai_model.generate_stream(prompt, callback):
                full_response += chunk
            return self._parse_outline(full_response)
        else:
            # 非流式生成
            response = await self.ai_model.generate(prompt)
            return self._parse_outline(response)

    async def optimize_outline(self, outline, callback=None):
        """
        优化小说大纲

        Args:
            outline: 初步大纲（JSON格式）
            callback: 回调函数，用于接收流式生成的内容

        Returns:
            优化后的大纲（JSON格式）
        """
        prompt = self._create_optimization_prompt(outline)
        max_tokens = None
        temperature = None

        if callback:
            # 流式生成
            full_response = ""
            async for chunk in self.ai_model.generate_stream(prompt, callback):
                full_response += chunk
            return self._parse_outline(full_response)
        else:
            # 非流式生成
            response = await self.ai_model.generate(prompt)
            return self._parse_outline(response)

    async def expand_chapters(self, outline, callback=None):
        """
        扩展章节列表

        Args:
            outline: 小说大纲（JSON格式）
            callback: 回调函数，用于接收流式生成的内容

        Returns:
            扩展后的大纲（JSON格式）
        """
        prompt = self._create_chapter_expansion_prompt(outline)
        max_tokens = None
        temperature = None

        if callback:
            # 流式生成
            full_response = ""
            async for chunk in self.ai_model.generate_stream(prompt, callback):
                full_response += chunk
            return self._parse_outline(full_response)
        else:
            # 非流式生成
            response = await self.ai_model.generate(prompt)
            return self._parse_outline(response)

    def _create_outline_prompt(self, title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, protagonist_count, important_count, supporting_count, minor_count):
        """创建大纲生成的提示词"""
        # 构建提示词基础部分
        prompt = f"""
        请为我创建一部小说的详细大纲，以JSON格式返回。小说信息如下：
        """

        # 根据用户输入添加相应信息
        if title:
            prompt += f"""
        小说标题：{title}"""

        if genre:
            prompt += f"""
        小说类型：{genre}"""

        if theme:
            prompt += f"""
        主题：{theme}"""

        if style:
            prompt += f"""
        风格：{style}"""

        if synopsis:
            prompt += f"""
        简介：{synopsis}"""

        # 添加结构信息
        prompt += f"""
        卷数：{volume_count} 卷
        每卷章节数：{chapters_per_volume} 章
        每章字数：{words_per_chapter} 字
        总字数：约 {volume_count * chapters_per_volume * words_per_chapter // 10000} 万字

        人物设置：
        主角数量：{protagonist_count} 个
        重要角色数量：{important_count} 个
        配角数量：{supporting_count} 个
        龙套数量：{minor_count} 个

        请生成以下内容：
        1. 小说标题
        2. 核心主题
        3. 主要人物（包括姓名、身份、性格特点和背景故事）
        4. 故事梗概
        5. 分卷结构（每卷包含标题、简介和具体章节）
        6. 世界观设定

        特别要求：
        1. 卷标题必须包含卷号，如“第一卷：卷标题”
        2. 章节标题必须包含章节号，如“第一章：章节标题”

        请确保大纲结构完整、逻辑合理，并以下面的JSON格式返回：

        ```json
        {{
            "title": "小说标题",
            "theme": "核心主题",
            "characters": [
                {{
                    "name": "角色名",
                    "identity": "身份",
                    "personality": "性格特点",
                    "background": "背景故事"
                }}
            ],
            "synopsis": "故事梗概",
            "volumes": [
                {{
                    "title": "卷标题",
                    "description": "卷简介",
                    "chapters": [
                        {{
                            "title": "章节标题",
                            "summary": "章节摘要"
                        }}
                    ]
                }}
            ],
            "worldbuilding": "世界观设定"
        }}
        ```

        请只返回JSON格式的内容，不要包含其他解释或说明。
        """

        return prompt

    def _create_optimization_prompt(self, outline):
        """创建大纲优化的提示词"""
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)

        return f"""
        请优化以下小说大纲，使其更加完善：

        {outline_json}

        请进行以下优化：
        1. 完善角色背景和动机
        2. 增强情节的起伏和转折
        3. 丰富世界观设定的细节
        4. 确保各章节和卷之间的逻辑连贯

        请保持原有的JSON格式，只返回优化后的JSON内容，不要包含其他解释或说明。
        """

    def _create_chapter_expansion_prompt(self, outline):
        """创建章节扩展的提示词"""
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)

        return f"""
        请基于以下小说大纲，将简略的章节扩展为更详细的章节列表：

        {outline_json}

        请进行以下扩展：
        1. 可以保持原有章节不变，只添加详细内容
        2. 也可以将原有章节扩展为更多的章节
        3. 每个章节都应包含标题和详细摘要

        请保持原有的JSON格式，只返回扩展后的JSON内容，不要包含其他解释或说明。
        """

    def _parse_outline(self, response):
        """解析AI生成的大纲响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                json_start = response.find('```json')
                if json_start != -1:
                    json_start += 7  # 跳过```json
                else:
                    json_start = response.find('{')

                json_end = response.rfind('```')
                if json_end != -1 and json_end > json_start:
                    json_text = response[json_start:json_end].strip()
                else:
                    json_end = response.rfind('}')
                    json_text = response[json_start:json_end+1].strip()

                return json.loads(json_text)
            except (json.JSONDecodeError, ValueError):
                # 如果仍然失败，返回原始响应
                return {"error": "无法解析响应", "raw_response": response}
