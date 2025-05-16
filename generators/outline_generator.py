import json
import logging # 导入logging模块，方便记录日志！
import re # 导入re模块，用正则表达式更精准地找到JSON！
from models.ai_model import AIModel

class OutlineGenerator:
    """小说大纲生成器"""
    LOG_PREFIX = "[DEBUG_OUTLINE_GENERATOR]" # 日志前缀，哼，休想逃过我的眼睛！

    def __init__(self, ai_model: AIModel, config_manager):
        """
        初始化大纲生成器

        Args:
            ai_model: AI模型实例
            config_manager: 配置管理器实例
        """
        self.ai_model = ai_model
        self.config_manager = config_manager
        logging.info(f"{self.LOG_PREFIX} OutlineGenerator 已创建。接收到的参数 - ai_model: {type(ai_model)}, config_manager: {type(config_manager)}")

    async def generate_outline(self, title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, new_character_count, selected_characters=None, start_volume=None, start_chapter=None, end_volume=None, end_chapter=None, existing_outline=None, callback=None):
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
            new_character_count: 新生成角色数量
            selected_characters: 选择的已有角色列表
            start_volume: 起始卷号（从1开始）
            start_chapter: 起始章节号（从1开始）
            end_volume: 结束卷号（从1开始）
            end_chapter: 结束章节号（从1开始）
            existing_outline: 已有的大纲内容（用于指定范围生成）
            callback: 回调函数，用于接收流式生成的内容

        Returns:
            生成的大纲（JSON格式）
        """
        logging.info(f"{self.LOG_PREFIX} generate_outline: 核心生成逻辑开始。")
        logging.info(f"{self.LOG_PREFIX} generate_outline: 参数 - title='{title}', genre='{genre}', theme='{theme}', style='{style}', synopsis (len)='{len(synopsis) if synopsis else 0}', volume_count={volume_count}, chapters_per_volume={chapters_per_volume}, words_per_chapter={words_per_chapter}, new_character_count={new_character_count}, selected_characters (count)={len(selected_characters) if selected_characters else 0}, start_volume={start_volume}, start_chapter={start_chapter}, end_volume={end_volume}, end_chapter={end_chapter}, existing_outline (present)={existing_outline is not None}")

        prompt = self._create_outline_prompt(title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, new_character_count, selected_characters, start_volume, start_chapter, end_volume, end_chapter, existing_outline)

        if callback:
            # 流式生成
            logging.info(f"{self.LOG_PREFIX} generate_outline: 开始调用 AI 模型 (generate_stream) 进行流式生成。")
            full_response = ""
            # 中文日志：开始处理流式数据，看AI又整什么幺蛾子！
            logging.info(f"{self.LOG_PREFIX} generate_outline: 开始接收并处理流式数据块...")
            async for chunk in self.ai_model.generate_stream(prompt, callback):
                # 中文日志：新的一块来了！
                logging.info(f"{self.LOG_PREFIX} generate_outline: 正在处理新的流式数据块...")
                try:
                    # 中文日志：让我康康这块里面是啥！
                    logging.info(f"{self.LOG_PREFIX} generate_outline: 尝试从 chunk 中获取 text...")
                    # 假设 chunk 是一个对象，并且文本内容在 chunk.text 中
                    # 如果您的 AIModel.generate_stream 直接返回字符串块，则不需要 .text
                    text_to_add = chunk.text if hasattr(chunk, 'text') else str(chunk)
                    logging.info(f"{self.LOG_PREFIX} generate_outline: 成功获取 chunk 内容 (前100字符): '{text_to_add[:100]}{'...' if len(text_to_add) > 100 else ''}'")
                    full_response += text_to_add
                except AttributeError as e_attr:
                    logging.error(f"{self.LOG_PREFIX} generate_outline: 尝试访问 chunk.text 失败，chunk 可能没有 text 属性。错误: {e_attr}, chunk 类型: {type(chunk)}, chunk 内容: {str(chunk)[:200]}{'...' if len(str(chunk)) > 200 else ''}")
                    # 如果 chunk 本身就是字符串，尝试直接使用
                    if isinstance(chunk, str):
                        logging.info(f"{self.LOG_PREFIX} generate_outline: chunk 本身是字符串，直接拼接。")
                        full_response += chunk
                    else:
                        logging.warning(f"{self.LOG_PREFIX} generate_outline: 无法从 chunk 获取文本内容，跳过此 chunk。")
                    continue # 继续处理下一个块
                except Exception as e_chunk:
                    # 中文日志：可恶！处理这块的时候出错了！
                    logging.error(f"{self.LOG_PREFIX} generate_outline: 处理流式数据块时发生严重错误！错误详情: {e_chunk}, 当前 chunk 内容 (部分): {str(chunk)[:200]}{'...' if len(str(chunk)) > 200 else ''}")
                    # 根据您的策略，可以选择 continue 或 break
                    # logging.info(f"{self.LOG_PREFIX} generate_outline: 选择继续处理下一个数据块。")
                    # continue
                    logging.warning(f"{self.LOG_PREFIX} generate_outline: 发生错误，终止流式数据处理。")
                    break # 发生错误，终止循环
            logging.info(f"{self.LOG_PREFIX} generate_outline: AI 模型 (generate_stream) 流式生成结束。full_response_text 长度: {len(full_response)}")
            # 中文日志：把AI说的废话都拼起来了，打印出来看看！免得它不认账！
            logging.info(f"{self.LOG_PREFIX} generate_outline: 流式生成完整响应 full_response_text 内容如下 (为了避免过长，截取前1000字符):\n{full_response[:1000]}{'...' if len(full_response) > 1000 else ''}")
            generated_outline = self._parse_outline(full_response)
        else:
            # 非流式生成
            logging.info(f"{self.LOG_PREFIX} generate_outline: 开始调用 AI 模型 (generate) 进行非流式生成。")
            response = await self.ai_model.generate(prompt)
            logging.info(f"{self.LOG_PREFIX} generate_outline: AI 模型 (generate) 非流式生成结束。响应长度: {len(response)}")
            generated_outline = self._parse_outline(response)

        # 检查解析结果，如果解析失败，则直接返回错误信息字典，让上层处理
        if isinstance(generated_outline, dict) and "error" in generated_outline:
            return generated_outline # 错误检查！看你还怎么崩！

        # 如果有已有大纲且指定了生成范围，则合并大纲
        if existing_outline and start_volume and end_volume:
            # 在合并前也检查一下 generated_outline，虽然上面检查过一次，但多一层保险总是好的
            if isinstance(generated_outline, dict) and "error" in generated_outline:
                 return generated_outline
            return self._merge_outlines(existing_outline, generated_outline, start_volume, start_chapter, end_volume, end_chapter)
        else:
            return generated_outline

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

    def _create_outline_prompt(self, title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, new_character_count, selected_characters=None, start_volume=None, start_chapter=None, end_volume=None, end_chapter=None, existing_outline=None):
        """创建大纲生成的提示词"""
        logging.info(f"{self.LOG_PREFIX} _create_outline_prompt: 开始创建大纲生成提示词。")
        # 构建提示词基础部分
        if start_volume and end_volume:
            prompt = f"""
            请为我创建一部小说的指定范围的详细大纲，以JSON格式返回。小说信息如下：
            """
        else:
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
        新生成角色数量：{new_character_count} 个
        """

        # 添加选择的角色信息
        if selected_characters and len(selected_characters) > 0:
            prompt += f"""
        已选择的出场角色：
        """
            character_names = [char.get("name", "未命名角色") for char in selected_characters]
            prompt += ", ".join(character_names)
            prompt += "\n"

        # 特别提醒AI关于角色生成的说明
        prompt += f"""
        特别说明：
        1. 新生成角色数量 {new_character_count} 个仅指需要新创建的角色数量
        2. 请不要重复创建已有角色，已有角色会在"已选择的出场角色"中列出
        3. 在生成的JSON中，characters字段只包含新创建的角色，不要包含已有角色
        """

        # 如果指定了生成范围
        if start_volume and end_volume:
            prompt += f"""

        生成范围：从第{start_volume}卷{f'第{start_chapter}章' if start_chapter else '开始'} 到 第{end_volume}卷{f'第{end_chapter}章' if end_chapter else '结束'}
        """

            # 如果有已存在的大纲，添加到提示中
            if existing_outline:
                # 提取已有大纲的基本信息
                existing_title = existing_outline.get('title', '')
                existing_theme = existing_outline.get('theme', '')
                existing_synopsis = existing_outline.get('synopsis', '')
                existing_worldbuilding = existing_outline.get('worldbuilding', '')

                # 提取已有的角色信息
                existing_characters = existing_outline.get('characters', [])
                characters_info = ""
                for char in existing_characters:
                    characters_info += f"- {char.get('name', '')}: {char.get('identity', '')}, {char.get('personality', '')}, {char.get('background', '')}\\n"

                # 提取已有的卷和章节信息
                existing_volumes = existing_outline.get('volumes', [])
                volumes_info = ""
                for i, vol in enumerate(existing_volumes):
                    volumes_info += f"第{i+1}卷：{vol.get('title', '')}\\n"
                    volumes_info += f"简介：{vol.get('description', '')}\\n"
                    chapters = vol.get('chapters', [])
                    for j, chap in enumerate(chapters):
                        volumes_info += f"  第{j+1}章：{chap.get('title', '')}\\n"
                        volumes_info += f"  摘要：{chap.get('summary', '')}\\n"

                prompt += f"""

        已有的大纲信息：
        标题：{existing_title}
        核心主题：{existing_theme}
        故事梗概：{existing_synopsis}
        世界观设定：{existing_worldbuilding}

        已有的角色信息：
{characters_info}

        已有的卷和章节结构：
{volumes_info}

        注意：请只生成指定范围内的卷和章节，不要重复已有的内容。如果指定范围内的卷或章节已经存在，请替换它们。你只需要返回指定范围内的卷和章节，不需要返回其他卷和章节。
        """

        prompt += f"""

        请生成以下内容：
        1. 小说标题
        2. 核心主题
        3. 主要人物（包括姓名、身份、年龄、性别、性格特点、背景故事、外貌描述、能力特长和目标动机）
        4. 故事梗概
        5. 分卷结构（每卷包含标题、简介和具体章节）
        6. 世界观设定

        特别要求：
        1. 卷标题必须包含卷号，如"第二卷：卷标题"，卷号必须与实际卷号一致
        2. 章节标题必须包含章节号，如"第三章：章节标题"，章节号必须与实际章节号一致
        3. 只生成指定数量的新角色，不要重复已有角色
        4. 在characters字段中只包含新创建的角色，不要包含已有角色
        """

        if start_volume and end_volume:
            prompt += f"""
        3. 只生成指定范围内的卷和章节，但保持与已有大纲的一致性
        4. 不要重复已有的内容，只返回指定范围内的卷和章节
        5. 在JSON的volumes字段中，只包含指定范围内的卷，不要包含其他卷
        """

        prompt += f"""

        请确保大纲结构完整、逻辑合理，并以下面的JSON格式返回：

        ```json
        {{
            "title": "小说标题",
            "theme": "核心主题",
            "characters": [
                {{
                    "name": "角色名",
                    "identity": "身份",
                    "age": "年龄",
                    "gender": "性别",
                    "personality": "性格特点（详细描述）",
                    "background": "背景故事（详细描述）",
                    "appearance": "外貌描述（详细描述）",
                    "abilities": "能力特长（详细描述）",
                    "goals": "目标动机（详细描述）"
                }}
            ],
            "synopsis": "故事梗概",
            "volumes": [
                {{
                    "title": "第{start_volume}卷：卷标题",
                    "description": "卷简介",
                    "chapters": [
                        {{
                            "title": "第{start_chapter}章：章节标题",
                            "summary": "章节摘要"
                        }},
                        {{
                            "title": "第2章：章节标题",
                            "summary": "章节摘要"
                        }}
                    ]
                }},
                {{
                    "title": "第2卷：卷标题",
                    "description": "卷简介",
                    "chapters": [
                        {{
                            "title": "第1章：章节标题",
                            "summary": "章节摘要"
                        }}
                    ]
                }}
            ],
            "worldbuilding": "世界观设定"
        }}
        ```

        注意：如果指定了生成范围，请只在volumes字段中包含范围内的卷，不要包含其他卷。

        请只返回JSON格式的内容，不要包含其他解释或说明。
        """

        # 中文日志：哼，让我看看你最后给AI喂了什么迷魂汤！
        logging.info(f"{self.LOG_PREFIX} _create_outline_prompt: 最终生成的 prompt_text 内容如下:\n{prompt}")
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

    def _merge_outlines(self, existing_outline, generated_outline, start_volume, start_chapter, end_volume, end_chapter):
        """合并已有大纲和新生成的大纲

        Args:
            existing_outline: 已有的大纲
            generated_outline: 新生成的大纲
            start_volume: 起始卷号（从1开始）
            start_chapter: 起始章节号（从1开始）
            end_volume: 结束卷号（从1开始）
            end_chapter: 结束章节号（从1开始）

        Returns:
            合并后的大纲
        """
        # 创建结果大纲，基于已有大纲
        result_outline = existing_outline.copy()

        # 如果新生成的大纲中有volumes字段
        if 'volumes' in generated_outline and generated_outline['volumes']:
            # 确保结果大纲中有volumes字段
            if 'volumes' not in result_outline:
                result_outline['volumes'] = []

            # 遍历新生成的卷
            for new_volume in generated_outline['volumes']:
                # 提取卷号（从标题中提取数字）
                volume_title = new_volume.get('title', '')
                volume_number = 0

                # 尝试从标题中提取卷号
                import re
                match = re.search(r'第(\d+)卷', volume_title)
                if match:
                    volume_number = int(match.group(1))

                # 如果卷号在指定范围内
                if start_volume <= volume_number <= end_volume:
                    # 检查结果大纲中是否已有该卷
                    existing_volume_index = None
                    for i, vol in enumerate(result_outline['volumes']):
                        vol_title = vol.get('title', '')
                        match = re.search(r'第(\d+)卷', vol_title)
                        if match and int(match.group(1)) == volume_number:
                            existing_volume_index = i
                            break

                    # 如果已有该卷，替换或合并章节
                    if existing_volume_index is not None:
                        # 保留卷标题和简介
                        result_outline['volumes'][existing_volume_index]['title'] = new_volume.get('title', result_outline['volumes'][existing_volume_index]['title'])
                        result_outline['volumes'][existing_volume_index]['description'] = new_volume.get('description', result_outline['volumes'][existing_volume_index]['description'])

                        # 确保章节列表存在
                        if 'chapters' not in result_outline['volumes'][existing_volume_index]:
                            result_outline['volumes'][existing_volume_index]['chapters'] = []

                        # 如果有新章节
                        if 'chapters' in new_volume and new_volume['chapters']:
                            # 遍历新章节
                            for new_chapter in new_volume['chapters']:
                                # 提取章节号
                                chapter_title = new_chapter.get('title', '')
                                chapter_number = 0

                                match = re.search(r'第(\d+)章', chapter_title)
                                if match:
                                    chapter_number = int(match.group(1))

                                # 判断章节是否在范围内
                                in_range = True
                                if volume_number == start_volume and start_chapter and chapter_number < start_chapter:
                                    in_range = False
                                if volume_number == end_volume and end_chapter and chapter_number > end_chapter:
                                    in_range = False

                                if in_range:
                                    # 检查是否已有该章节
                                    existing_chapter_index = None
                                    for j, chap in enumerate(result_outline['volumes'][existing_volume_index]['chapters']):
                                        chap_title = chap.get('title', '')
                                        match = re.search(r'第(\d+)章', chap_title)
                                        if match and int(match.group(1)) == chapter_number:
                                            existing_chapter_index = j
                                            break

                                    # 如果已有该章节，替换
                                    if existing_chapter_index is not None:
                                        result_outline['volumes'][existing_volume_index]['chapters'][existing_chapter_index] = new_chapter
                                    else:
                                        # 如果没有，添加到适当位置
                                        # 找到插入位置
                                        insert_index = 0
                                        for j, chap in enumerate(result_outline['volumes'][existing_volume_index]['chapters']):
                                            chap_title = chap.get('title', '')
                                            match = re.search(r'第(\d+)章', chap_title)
                                            if match and int(match.group(1)) < chapter_number:
                                                insert_index = j + 1

                                        # 插入新章节
                                        result_outline['volumes'][existing_volume_index]['chapters'].insert(insert_index, new_chapter)
                    else:
                        # 如果没有该卷，添加到适当位置
                        # 找到插入位置
                        insert_index = 0
                        for i, vol in enumerate(result_outline['volumes']):
                            vol_title = vol.get('title', '')
                            match = re.search(r'第(\d+)卷', vol_title)
                            if match and int(match.group(1)) < volume_number:
                                insert_index = i + 1

                        # 插入新卷
                        result_outline['volumes'].insert(insert_index, new_volume)

        # 更新其他字段（如果有新内容）
        if 'title' in generated_outline and generated_outline['title']:
            result_outline['title'] = generated_outline['title']
        if 'theme' in generated_outline and generated_outline['theme']:
            result_outline['theme'] = generated_outline['theme']
        if 'synopsis' in generated_outline and generated_outline['synopsis']:
            result_outline['synopsis'] = generated_outline['synopsis']
        if 'worldbuilding' in generated_outline and generated_outline['worldbuilding']:
            result_outline['worldbuilding'] = generated_outline['worldbuilding']
        # 合并角色数据 - 只添加新生成的角色，不替换已有角色
        if 'characters' in generated_outline and generated_outline['characters']:
            if not result_outline.get('characters'):
                # 如果结果大纲中没有角色数据，直接使用新生成的角色数据
                result_outline['characters'] = generated_outline['characters']
            else:
                # 如果结果大纲中已有角色数据，合并新生成的角色数据
                existing_characters = result_outline.get('characters', [])
                new_characters = generated_outline.get('characters', [])

                # 获取已有角色的名称列表，用于检查重复
                existing_names = [char.get('name', '') for char in existing_characters]

                # 添加不重复的新角色
                for new_char in new_characters:
                    new_name = new_char.get('name', '')
                    if new_name and new_name not in existing_names:
                        existing_characters.append(new_char)
                        existing_names.append(new_name)

                # 更新角色数据
                result_outline['characters'] = existing_characters

        # 最终排序卷和章节，确保顺序正确
        if 'volumes' in result_outline and result_outline['volumes']:
            # 对卷进行排序
            import re
            def get_volume_number(volume):
                title = volume.get('title', '')
                match = re.search(r'第(\d+)卷', title)
                if match:
                    return int(match.group(1))
                return 0

            result_outline['volumes'].sort(key=get_volume_number)

            # 对每个卷的章节进行排序
            for volume in result_outline['volumes']:
                if 'chapters' in volume and volume['chapters']:
                    def get_chapter_number(chapter):
                        title = chapter.get('title', '')
                        match = re.search(r'第(\d+)章', title)
                        if match:
                            return int(match.group(1))
                        return 0

                    volume['chapters'].sort(key=get_chapter_number)

        return result_outline

    def _parse_outline(self, response: str):
        """
        解析AI生成的大纲响应。
        会尝试多种方式解析JSON，并在失败时记录详细错误和原始AI输出。哼，看你往哪跑！

        Args:
            response: AI返回的原始字符串。

        Returns:
            解析后的Python对象（通常是字典），或在解析失败时返回一个包含错误信息的字典。
        """
        # 中文日志：记录一下，看看AI又发了什么神经！
        logging.info(f"{self.LOG_PREFIX} _parse_outline: 开始解析AI响应。原始响应长度: {len(response)}")

        # 增强1：检查输入是否为空或非字符串
        if not response or not isinstance(response, str) or not response.strip():
            empty_response_message = "输入的 response 为空、非字符串或仅包含空白字符，无法进行JSON解析。"
            logging.warning(f"{self.LOG_PREFIX} _parse_outline: {empty_response_message} 原始响应 (部分): {str(response)[:200]}{'...' if len(str(response)) > 200 else ''}")
            return {
                "error": "输入内容无效", # 错误摘要
                "message": "AI未返回任何有效内容或内容格式不正确，无法解析。", # 给用户看的提示
                "raw_response": str(response) # 原始响应
            }

        # 增强2：初步检查是否像JSON（可选，因为正则会更精确）
        # if not response.strip().startswith('{') or not response.strip().endswith('}'):
        #     logging.warning(f"{self.LOG_PREFIX} _parse_outline: 响应内容看起来不像一个JSON对象 (并非以 '{{' 和 '}}' 包裹)。这可能导致直接解析失败。原始响应 (前100后100): {response.strip()[:100]}...{response.strip()[-100:]}")

        # 为了避免日志过长，可以只记录一部分，或者在debug级别记录完整响应
        # logging.debug(f"{self.LOG_PREFIX} _parse_outline: 原始AI响应内容 (前500字符): {response[:500]}...")

        # 方案一：尝试直接解析整个响应，万一AI这次很乖呢？
        try:
            parsed_data = json.loads(response)
            logging.info(f"{self.LOG_PREFIX} _parse_outline: AI响应直接解析JSON成功。看来AI今天心情不错嘛！解析后数据摘要 (类型): {type(parsed_data)}")
            if isinstance(parsed_data, dict):
                logging.info(f"{self.LOG_PREFIX} _parse_outline: 解析后数据键: {list(parsed_data.keys())}")
            return parsed_data
        except json.JSONDecodeError as e:
            # 中文日志：直接解析失败了，哼，就知道AI没那么老实！
            logging.warning(f"{self.LOG_PREFIX} _parse_outline: 直接解析JSON失败: {e}。AI的鬼画符真是难懂！")
            # logging.debug(f"{self.LOG_PREFIX} _parse_outline: 直接解析失败的原始响应: {response}") # 调试时可以打开，看看AI到底说了啥

        # 方案二：尝试提取 markdown 代码块中的 JSON，AI总喜欢搞这种花里胡哨的格式！
        json_text_markdown = "" # 先给它个空值，免得出错
        try:
            # 使用更健壮的正则表达式来提取被 ```json 和 ``` 包围的内容，看你往哪藏！
            match = re.search(r'```json\s*([\s\S]*?)\s*```', response, re.DOTALL)
            if match:
                json_text_markdown = match.group(1).strip()
                # 中文日志：找到了被```json ... ```包起来的东西，让我看看是不是宝贝！
                logging.info(f"{self.LOG_PREFIX} _parse_outline: 尝试从 '```json ... ```' 代码块中提取并解析JSON。")
                parsed_data = json.loads(json_text_markdown)
                # 中文日志：成功从代码块里掏出来了！算你识相！
                logging.info(f"{self.LOG_PREFIX} _parse_outline: 从 '```json ... ```' 代码块中解析JSON成功。解析后数据摘要 (类型): {type(parsed_data)}")
                if isinstance(parsed_data, dict):
                    logging.info(f"{self.LOG_PREFIX} _parse_outline: 解析后数据键: {list(parsed_data.keys())}")
                return parsed_data
            else:
                # 中文日志：没找到```json ... ```这种标记，AI又在搞什么飞机？
                logging.warning(f"{self.LOG_PREFIX} _parse_outline: 在响应中未找到 '```json ... ```' 代码块。")
        except json.JSONDecodeError as e:
            # 中文日志：从代码块里掏出来的也不是好东西，解析失败！气死我了！
            logging.warning(f"{self.LOG_PREFIX} _parse_outline: 从 '```json ... ```' 代码块中解析JSON失败: {e}。这AI给的都是些啥玩意儿！")
            # logging.debug(f"{self.LOG_PREFIX} _parse_outline: 从代码块提取但解析失败的JSON文本: {json_text_markdown}") # 调试时可以看看AI写的JSON有多烂
        except Exception as e_generic: # 捕获其他可能的异常，比如 re 模块的错误
            logging.error(f"{self.LOG_PREFIX} _parse_outline: 尝试从 '```json ... ```' 代码块提取或解析时发生预料之外的错误: {e_generic}")


        # 方案三：尝试查找第一个 '{' 和最后一个 '}' 之间的内容，死马当活马医了！
        json_text_substring = "" # 先给它个空值
        try:
            start_index = response.find('{')
            end_index = response.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_text_substring = response[start_index : end_index + 1].strip()
                # 中文日志：大海捞针，看看能不能从'{'和'}'之间找到点啥
                logging.info(f"{self.LOG_PREFIX} _parse_outline: 尝试解析从第一个 '{{' 到最后一个 '}}' 的子字符串作为JSON。")
                parsed_data = json.loads(json_text_substring)
                # 中文日志：嘿，还真捞着了！勉强能用！
                logging.info(f"{self.LOG_PREFIX} _parse_outline: 从子字符串 '{{...}}' 解析JSON成功。解析后数据摘要 (类型): {type(parsed_data)}")
                if isinstance(parsed_data, dict):
                    logging.info(f"{self.LOG_PREFIX} _parse_outline: 解析后数据键: {list(parsed_data.keys())}")
                return parsed_data
            else:
                # 中文日志：连'{'和'}'都凑不齐一对，AI这是彻底摆烂了吗？
                logging.warning(f"{self.LOG_PREFIX} _parse_outline: 在响应中未找到有效的 '{{' 和 '}}' 来构成JSON对象。")
        except json.JSONDecodeError as e:
            # 中文日志：就算是'{'和'}'之间的东西也是一坨翔，解析失败！
            logging.warning(f"{self.LOG_PREFIX} _parse_outline: 从子字符串 '{{...}}' 解析JSON失败: {e}。AI你是不是故意的！")
            # logging.debug(f"{self.LOG_PREFIX} _parse_outline: 从子字符串提取但解析失败的JSON文本: {json_text_substring}")
        except Exception as e_generic: # 捕获其他可能的异常
            logging.error(f"{self.LOG_PREFIX} _parse_outline: 尝试从 '{{...}}' 子字符串提取或解析时发生预料之外的错误: {e_generic}")


        # 如果所有尝试都失败了，只能认栽！
        error_message = "所有JSON解析尝试均失败。AI今天大概是没吃药。"
        # 中文日志：彻底没救了，AI给的就是一堆乱码！
        logging.error(f"{self.LOG_PREFIX} _parse_outline: {error_message} 原始响应 (前500字符): {response[:500]}...") # 记录部分原始响应避免日志过长
        # logging.error(f"{self.LOG_PREFIX} _parse_outline: 最终无法解析的原始AI响应: {response}") # 记录完整的原始响应
        # 返回一个标准的错误结构，包含错误信息和原始响应，方便上层处理，哼！
        return {
            "error": error_message, # 错误摘要，给机器看的
            "message": "AI返回的格式不正确，无法解析为有效的大纲结构。请检查AI的输出或提示词。", # 给用户看的提示
            "raw_response": response # 附带原始响应，用于排查问题！
        }
