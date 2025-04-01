import json
from models.ai_model import AIModel

class ChapterGenerator:
    """小说章节生成器"""

    def __init__(self, ai_model: AIModel, config_manager):
        """
        初始化章节生成器

        Args:
            ai_model: AI模型实例
            config_manager: 配置管理器实例
        """
        self.ai_model = ai_model
        self.config_manager = config_manager

    async def generate_chapter(self, outline, volume_index, chapter_index, callback=None):
        """
        生成章节内容

        Args:
            outline: 小说大纲（JSON格式）
            volume_index: 卷索引
            chapter_index: 章节索引
            callback: 回调函数，用于接收流式生成的内容

        Returns:
            生成的章节内容
        """
        prompt = self._create_chapter_prompt(outline, volume_index, chapter_index)

        if callback:
            # 流式生成
            full_response = ""
            async for chunk in self.ai_model.generate_stream(prompt, callback):
                full_response += chunk
            return full_response
        else:
            # 非流式生成
            return await self.ai_model.generate(prompt)

    def _create_chapter_prompt(self, outline, volume_index, chapter_index):
        """创建章节生成的提示词"""
        # 获取小说基本信息
        title = outline.get("title", "未命名小说")
        theme = outline.get("theme", "")
        worldbuilding = outline.get("worldbuilding", "")

        # 获取主要人物信息
        characters = outline.get("characters", [])
        characters_info = ""
        for char in characters:
            characters_info += f"- {char.get('name', '')}: {char.get('identity', '')}, {char.get('personality', '')}, {char.get('background', '')}\n"

        # 获取当前卷的信息
        volumes = outline.get("volumes", [])
        if volume_index >= len(volumes):
            return f"错误：卷索引 {volume_index} 超出范围"

        current_volume = volumes[volume_index]
        volume_title = current_volume.get("title", f"第{volume_index+1}卷")
        volume_description = current_volume.get("description", "")

        # 获取当前章节的信息
        chapters = current_volume.get("chapters", [])
        if chapter_index >= len(chapters):
            return f"错误：章节索引 {chapter_index} 超出范围"

        current_chapter = chapters[chapter_index]
        chapter_title = current_chapter.get("title", f"第{chapter_index+1}章")
        chapter_summary = current_chapter.get("summary", "")

        # 获取前一章节的信息（如果有）
        previous_chapter_summary = ""
        if chapter_index > 0:
            previous_chapter = chapters[chapter_index - 1]
            previous_chapter_summary = previous_chapter.get("summary", "")

        # 获取后一章节的信息（如果有）
        next_chapter_summary = ""
        if chapter_index < len(chapters) - 1:
            next_chapter = chapters[chapter_index + 1]
            next_chapter_summary = next_chapter.get("summary", "")

        return f"""
        请为以下小说生成一个完整的章节内容：

        小说标题：{title}
        核心主题：{theme}
        世界观设定：{worldbuilding}

        主要人物：
        {characters_info}

        当前卷：{volume_title}
        卷简介：{volume_description}

        当前章节：{chapter_title}
        章节摘要：{chapter_summary}

        {"前一章节摘要：" + previous_chapter_summary if previous_chapter_summary else ""}
        {"后一章节摘要：" + next_chapter_summary if next_chapter_summary else ""}

        请根据以上信息，创作一个完整、连贯、生动的章节内容。内容应该：
        1. 符合章节摘要的描述
        2. 与前后章节保持连贯
        3. 展现人物性格和发展
        4. 符合小说的整体风格和主题
        5. 包含丰富的对话、描写和情节发展

        请直接返回章节内容，不要包含其他解释或说明。
        """
