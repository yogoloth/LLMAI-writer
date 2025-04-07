from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem,
    QDialog
)
from PyQt6.QtCore import Qt

from ui.components import AIGenerateDialog


class ChapterTab(QWidget):
    """章节生成标签页"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.chapter_generator = None
        self.generation_thread = None
        self.outline = None
        self.current_volume_index = -1
        self.current_chapter_index = -1

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 创建左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 创建模型选择组
        model_group = QGroupBox("模型选择")
        model_layout = QFormLayout()

        self.model_combo = QComboBox()
        # 添加标准模型
        self.model_combo.addItems(["GPT", "Claude", "Gemini", "自定义OpenAI", "ModelScope"])

        # 添加自定义模型
        if hasattr(self.main_window, 'custom_openai_models') and self.main_window.custom_openai_models:
            for model_name in self.main_window.custom_openai_models.keys():
                self.model_combo.addItem(model_name)

        model_layout.addRow("AI模型:", self.model_combo)

        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        # 创建卷选择组
        volume_group = QGroupBox("卷选择")
        volume_layout = QVBoxLayout()

        self.volume_list = QListWidget()
        self.volume_list.currentRowChanged.connect(self.on_volume_selected)
        volume_layout.addWidget(self.volume_list)

        volume_group.setLayout(volume_layout)
        left_layout.addWidget(volume_group)

        # 创建章节选择组
        chapter_group = QGroupBox("章节选择")
        chapter_layout = QVBoxLayout()

        self.chapter_list = QListWidget()
        self.chapter_list.currentRowChanged.connect(self.on_chapter_selected)
        chapter_layout.addWidget(self.chapter_list)

        chapter_group.setLayout(chapter_layout)
        left_layout.addWidget(chapter_group)

        # 创建操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout()

        # 生成章节按钮已移除，使用AI辅助编辑按钮替代

        self.save_button = QPushButton("保存章节")
        self.save_button.clicked.connect(self.save_chapter)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        button_group.setLayout(button_layout)
        left_layout.addWidget(button_group)

        # 添加弹性空间
        left_layout.addStretch()

        # 创建右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 创建章节信息组
        info_group = QGroupBox("章节信息")
        info_layout = QVBoxLayout()

        self.info_edit = QTextEdit()
        self.info_edit.setReadOnly(False)  # 设置为可编辑
        info_layout.addWidget(self.info_edit)

        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        info_group.setFixedHeight(300)

        # 创建输出区域
        output_group = QGroupBox("章节内容")
        output_layout = QVBoxLayout()

        self.output_edit = QTextEdit()
        output_layout.addWidget(self.output_edit)

        # 添加AI生成按钮
        ai_button_layout = QHBoxLayout()
        self.ai_generate_button = QPushButton("AI辅助编辑")
        self.ai_generate_button.clicked.connect(self._generate_with_ai)
        self.ai_generate_button.setEnabled(False)
        ai_button_layout.addWidget(self.ai_generate_button)
        ai_button_layout.addStretch()
        output_layout.addLayout(ai_button_layout)

        # 进度条已移除，使用AI生成对话框中的进度条

        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)

        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([300, 700])

    def update_outline(self, outline):
        """更新大纲"""
        self.outline = outline

        # 清空卷列表
        self.volume_list.clear()

        # 添加卷
        if outline and "volumes" in outline:
            for i, volume in enumerate(outline["volumes"]):
                title = volume.get("title", f"第{i+1}卷")
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.volume_list.addItem(item)

    def on_volume_selected(self, row):
        """卷选择事件处理"""
        if row < 0:
            return

        self.current_volume_index = row

        # 清空章节列表
        self.chapter_list.clear()

        # 添加章节
        if self.outline and "volumes" in self.outline and row < len(self.outline["volumes"]):
            volume = self.outline["volumes"][row]
            if "chapters" in volume:
                for i, chapter in enumerate(volume["chapters"]):
                    title = chapter.get("title", f"第{i+1}章")
                    item = QListWidgetItem(title)
                    item.setData(Qt.ItemDataRole.UserRole, i)
                    self.chapter_list.addItem(item)

    def on_chapter_selected(self, row):
        """章节选择事件处理"""
        if row < 0 or self.current_volume_index < 0:
            return

        self.current_chapter_index = row

        # 更新章节信息
        if (self.outline and "volumes" in self.outline and
            self.current_volume_index < len(self.outline["volumes"])):

            volume = self.outline["volumes"][self.current_volume_index]
            if "chapters" in volume and row < len(volume["chapters"]):
                chapter = volume["chapters"][row]
                title = chapter.get("title", f"第{row+1}章")
                summary = chapter.get("summary", "")

                self.info_edit.setText(f"标题: {title}\n\n摘要: {summary}")

                # 加载章节内容（如果有）
                content = self.main_window.get_chapter(self.current_volume_index, row)
                if content:
                    self.output_edit.setPlainText(content)
                else:
                    self.output_edit.clear()

                # 生成按钮已移除

                # 启用AI辅助编辑按钮
                self.ai_generate_button.setEnabled(True)

                # 如果有内容，启用保存按钮
                self.save_button.setEnabled(bool(self.output_edit.toPlainText()))

    def _get_model_type(self):
        """获取选择的模型类型"""
        model_text = self.model_combo.currentText().lower()
        if model_text == "gpt":
            return "gpt"
        elif model_text == "claude":
            return "claude"
        elif model_text == "gemini":
            return "gemini"
        elif model_text == "自定义openai":
            return "custom_openai"
        elif model_text == "modelscope":
            return "modelscope"
        else:
            return "gpt"  # 默认使用GPT

    def _stream_callback(self, chunk):
        """流式生成回调函数"""
        self.output_edit.insertPlainText(chunk)
        # 滚动到底部
        scrollbar = self.output_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # 生成章节相关的信号处理方法已移除，使用 _generate_with_ai 方法替代

    # generate_chapter 方法已移除，使用 _generate_with_ai 方法替代

    def save_chapter(self, show_message=True):
        """保存章节

        Args:
            show_message: 是否显示消息对话框
        """
        if self.current_volume_index < 0 or self.current_chapter_index < 0:
            if show_message:
                QMessageBox.warning(self, "保存失败", "请先选择一个章节")
            return

        # 获取章节内容
        content = self.output_edit.toPlainText()
        if not content:
            if show_message:
                QMessageBox.warning(self, "保存失败", "章节内容为空")
            return

        # 保存章节内容
        self.main_window.set_chapter(self.current_volume_index, self.current_chapter_index, content)

        # 显示成功消息
        if show_message:
            QMessageBox.information(self, "保存成功", "章节已保存")

        # 启用保存按钮
        self.save_button.setEnabled(True)

    def _generate_with_ai(self):
        """使用AI生成内容"""
        if self.current_volume_index < 0 or self.current_chapter_index < 0:
            QMessageBox.warning(self, "生成失败", "请先选择一个章节")
            return

        # 获取总大纲信息
        outline_info = {}
        if self.outline:
            outline_info = {
                "title": self.outline.get("title", ""),
                "theme": self.outline.get("theme", ""),
                "synopsis": self.outline.get("synopsis", ""),
                "worldbuilding": self.outline.get("worldbuilding", "")
            }

        # 获取上下文信息
        context_info = {}
        volumes = self.outline.get("volumes", [])
        if self.current_volume_index < len(volumes):
            volume = volumes[self.current_volume_index]
            context_info["volume_title"] = volume.get("title", "")
            context_info["volume_description"] = volume.get("description", "")

            chapters = volume.get("chapters", [])
            if self.current_chapter_index < len(chapters):
                chapter = chapters[self.current_chapter_index]
                context_info["chapter_title"] = chapter.get("title", "")
                context_info["chapter_number"] = self.current_chapter_index + 1

                # 添加前10章的标题和摘要
                previous_chapters = []
                start_idx = max(0, self.current_chapter_index - 10)
                for i in range(start_idx, self.current_chapter_index):
                    if i < len(chapters):
                        prev_chapter = chapters[i]
                        previous_chapters.append({
                            "title": prev_chapter.get("title", ""),
                            "summary": prev_chapter.get("summary", "")
                        })
                context_info["previous_chapters"] = previous_chapters

                # 添加前一章的内容
                if self.current_chapter_index > 0:
                    prev_chapter_index = self.current_chapter_index - 1
                    prev_chapter_content = self.main_window.get_chapter(self.current_volume_index, prev_chapter_index)
                    if prev_chapter_content:
                        context_info["previous_chapter_content"] = prev_chapter_content

                # 添加后3章的标题和摘要
                next_chapters = []
                end_idx = min(len(chapters), self.current_chapter_index + 4)
                for i in range(self.current_chapter_index + 1, end_idx):
                    if i < len(chapters):
                        next_chapter = chapters[i]
                        next_chapters.append({
                            "title": next_chapter.get("title", ""),
                            "summary": next_chapter.get("summary", "")
                        })
                context_info["next_chapters"] = next_chapters

        # 获取当前章节信息
        current_text = self.output_edit.toPlainText()
        chapter_info = self.info_edit.toPlainText()

        dialog = AIGenerateDialog(
            self,
            "AI生成章节内容",
            "章节内容",
            current_text,
            models=["GPT", "Claude", "Gemini", "自定义OpenAI", "ModelScope"],
            default_model="GPT",
            outline_info=outline_info,
            context_info=context_info,
            prompt_manager=self.main_window.prompt_manager
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
            if result:
                self.output_edit.setPlainText(result)
                self.save_button.setEnabled(True)
                # 在使用AI生成结果后自动保存
                self.save_chapter(show_message=False)
                # 显示状态栏消息
                self.main_window.status_bar_manager.show_message("已使用AI生成结果并保存")
