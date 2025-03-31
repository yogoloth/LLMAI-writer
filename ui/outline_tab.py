import json
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QSplitter, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from generators.outline_generator import OutlineGenerator
from utils.async_utils import GenerationThread, ProgressIndicator
from utils.prompt_manager import PromptManager


class OutlineTab(QWidget):
    """大纲生成标签页"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.outline_generator = None
        self.generation_thread = None
        self.progress_indicator = ProgressIndicator(self)

        # 获取提示词管理器
        self.prompt_manager = self.main_window.prompt_manager

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
        self.model_combo.addItems(["GPT", "Claude", "Gemini", "自定义OpenAI"])
        model_layout.addRow("AI模型:", self.model_combo)

        # 温度设置已移除

        # 添加提示词模板选择
        self.template_combo = QComboBox()
        self.template_combo.addItem("选择提示词模板")

        # 加载大纲生成模板
        outline_templates = self.prompt_manager.get_templates_by_category("outline")
        for template in outline_templates:
            self.template_combo.addItem(template.name)

        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        model_layout.addRow("提示词模板:", self.template_combo)

        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        # 创建基本信息组
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout()

        # 添加小说标题输入框
        self.title_edit = QLineEdit()
        info_layout.addRow("小说标题:", self.title_edit)

        # 添加小说类型输入框
        self.genre_edit = QLineEdit()
        info_layout.addRow("小说类型:", self.genre_edit)

        # 添加小说主题输入框 - 使用文本编辑框并添加滚动条
        self.theme_edit = QTextEdit()
        self.theme_edit.setMinimumHeight(60)  # 设置最小高度
        self.theme_edit.setMaximumHeight(100)  # 设置最大高度
        info_layout.addRow("小说主题:", self.theme_edit)

        # 添加小说风格输入框 - 使用文本编辑框并添加滚动条
        self.style_edit = QTextEdit()
        self.style_edit.setMinimumHeight(60)  # 设置最小高度
        self.style_edit.setMaximumHeight(100)  # 设置最大高度
        info_layout.addRow("小说风格:", self.style_edit)

        # 添加小说简介输入框 - 使用文本编辑框并添加滚动条
        self.synopsis_edit = QTextEdit()
        self.synopsis_edit.setMinimumHeight(80)  # 设置最小高度
        self.synopsis_edit.setMaximumHeight(120)  # 设置最大高度
        info_layout.addRow("小说简介:", self.synopsis_edit)

        # 添加卷数设置
        self.volume_count_spin = QSpinBox()
        self.volume_count_spin.setRange(1, 20)
        self.volume_count_spin.setValue(3)
        self.volume_count_spin.setSuffix(" 卷")
        info_layout.addRow("卷数:", self.volume_count_spin)

        # 添加每卷章节数设置
        self.chapters_per_volume_spin = QSpinBox()
        self.chapters_per_volume_spin.setRange(3, 30)
        self.chapters_per_volume_spin.setValue(10)
        self.chapters_per_volume_spin.setSuffix(" 章/卷")
        info_layout.addRow("每卷章节数:", self.chapters_per_volume_spin)

        # 添加每章字数设置
        self.words_per_chapter_spin = QSpinBox()
        self.words_per_chapter_spin.setRange(1000, 10000)
        self.words_per_chapter_spin.setValue(3000)
        self.words_per_chapter_spin.setSingleStep(500)
        self.words_per_chapter_spin.setSuffix(" 字/章")
        info_layout.addRow("每章字数:", self.words_per_chapter_spin)

        # 创建角色设置组
        character_group = QGroupBox("角色设置")
        character_layout = QFormLayout()

        # 添加主角数量设置
        self.protagonist_count_spin = QSpinBox()
        self.protagonist_count_spin.setRange(1, 5)
        self.protagonist_count_spin.setValue(1)
        self.protagonist_count_spin.setSuffix(" 个")
        character_layout.addRow("主角数量:", self.protagonist_count_spin)

        # 添加重要角色数量设置
        self.important_count_spin = QSpinBox()
        self.important_count_spin.setRange(0, 10)
        self.important_count_spin.setValue(3)
        self.important_count_spin.setSuffix(" 个")
        character_layout.addRow("重要角色数量:", self.important_count_spin)

        # 添加配角数量设置
        self.supporting_count_spin = QSpinBox()
        self.supporting_count_spin.setRange(0, 20)
        self.supporting_count_spin.setValue(5)
        self.supporting_count_spin.setSuffix(" 个")
        character_layout.addRow("配角数量:", self.supporting_count_spin)

        # 添加龙套数量设置
        self.minor_count_spin = QSpinBox()
        self.minor_count_spin.setRange(0, 30)
        self.minor_count_spin.setValue(10)
        self.minor_count_spin.setSuffix(" 个")
        character_layout.addRow("龙套数量:", self.minor_count_spin)

        character_group.setLayout(character_layout)
        info_layout.addRow(character_group)

        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)

        # 创建操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout()

        self.generate_button = QPushButton("生成大纲")
        self.generate_button.clicked.connect(self.generate_outline)
        button_layout.addWidget(self.generate_button)

        # 已移除读取大纲和保存大纲按钮
        self.save_button = QPushButton("清空输出")
        self.save_button.clicked.connect(lambda: self.output_edit.clear())
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        button_group.setLayout(button_layout)
        left_layout.addWidget(button_group)

        # 添加弹性空间
        left_layout.addStretch()

        # 创建右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 创建输出区域
        output_group = QGroupBox("生成结果")
        output_layout = QVBoxLayout()

        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        output_layout.addWidget(self.output_edit)

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.progress_bar.setVisible(False)
        output_layout.addWidget(self.progress_bar)

        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)

        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([300, 700])

    def _on_template_selected(self, index):
        """模板选择事件处理"""
        if index <= 0:  # 第一项是提示文本
            return

        template_name = self.template_combo.currentText()
        template = self.prompt_manager.get_template(template_name)

        if template:
            # 显示模板信息
            QMessageBox.information(
                self,
                f"模板: {template_name}",
                f"描述: {template.description}\n\n分类: {template.category}"
            )

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
        else:
            return "gpt"  # 默认使用GPT

    def _update_buttons(self, has_outline):
        """更新按钮状态"""
        # 现在只更新清空输出按钮
        self.save_button.setEnabled(has_outline)

    def _stream_callback(self, chunk):
        """流式生成回调函数"""
        self.output_edit.insertPlainText(chunk)
        # 滚动到底部
        scrollbar = self.output_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str)
    def _on_progress(self, chunk):
        """处理进度信号"""
        self._stream_callback(chunk)

    @pyqtSlot(object)
    def _on_finished(self, result):
        """处理完成信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 更新UI
        self.generate_button.setEnabled(True)
        self.save_button.setEnabled(True)

        # 在大纲中添加原始输入信息
        result["input_info"] = {
            "title": self.title_edit.text().strip(),
            "genre": self.genre_edit.text().strip(),
            "theme": self.theme_edit.toPlainText().strip(),
            "style": self.style_edit.toPlainText().strip(),
            "synopsis": self.synopsis_edit.toPlainText().strip()
        }

        # 设置大纲
        self.main_window.set_outline(result)

        # 更新按钮状态
        self._update_buttons(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("大纲生成完成")

        # 显示完成消息
        QMessageBox.information(self, "生成完成", "大纲生成完成！")

    @pyqtSlot(str)
    def _on_error(self, error_message):
        """处理错误信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 更新UI
        self.generate_button.setEnabled(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("大纲生成失败")

        # 显示错误消息
        QMessageBox.warning(self, "生成失败", f"生成大纲时出错: {error_message}")

    def generate_outline(self):
        """生成大纲"""
        # 获取输入
        title = self.title_edit.text().strip()
        genre = self.genre_edit.text().strip()
        theme = self.theme_edit.toPlainText().strip()  # 使用toPlainText()获取QTextEdit的内容
        style = self.style_edit.toPlainText().strip()  # 使用toPlainText()获取QTextEdit的内容
        synopsis = self.synopsis_edit.toPlainText().strip()  # 使用toPlainText()获取QTextEdit的内容
        volume_count = self.volume_count_spin.value()
        chapters_per_volume = self.chapters_per_volume_spin.value()
        words_per_chapter = self.words_per_chapter_spin.value()

        # 获取角色数量设置
        protagonist_count = self.protagonist_count_spin.value()
        important_count = self.important_count_spin.value()
        supporting_count = self.supporting_count_spin.value()
        minor_count = self.minor_count_spin.value()

        if not theme:
            QMessageBox.warning(self, "输入错误", "请输入小说主题")
            return

        # 获取模型
        model_type = self._get_model_type()
        try:
            model = self.main_window.get_model(model_type)
        except ValueError as e:
            QMessageBox.warning(self, "模型错误", str(e))
            return

        # 温度设置已移除

        # 创建大纲生成器
        self.outline_generator = OutlineGenerator(model, self.main_window.config_manager)

        # 清空输出
        self.output_edit.clear()

        # 禁用生成按钮
        self.generate_button.setEnabled(False)

        # 显示进度条
        self.progress_bar.setVisible(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("正在生成大纲...")

        # 检查是否使用模板
        template_name = self.template_combo.currentText()
        if template_name and template_name != "选择提示词模板":
            template = self.prompt_manager.get_template(template_name)
            if template:
                # 记录使用模板
                self.main_window.status_bar_manager.show_message(f"正在使用模板 '{template_name}' 生成大纲...")

        # 创建并启动生成线程
        self.generation_thread = GenerationThread(
            self.outline_generator.generate_outline,
            (title, genre, theme, style, synopsis, volume_count, chapters_per_volume, words_per_chapter, protagonist_count, important_count, supporting_count, minor_count),
            {"callback": self._stream_callback}
        )

        # 连接信号
        self.generation_thread.progress_signal.connect(self._on_progress)
        self.generation_thread.finished_signal.connect(self._on_finished)
        self.generation_thread.error_signal.connect(self._on_error)

        # 启动线程
        self.generation_thread.start()

        # 记录提示词历史
        self.prompt_manager.add_history(
            prompt=f"大纲生成: {title} - {theme}",
            model=model_type,
            metadata={
                "title": title,
                "genre": genre,
                "theme": theme,
                "volume_count": volume_count,
                "chapters_per_volume": chapters_per_volume
            }
        )

    # 删除了optimize_outline方法

    # 删除了expand_chapters方法

    # 已移除save_outline方法
    # 这个功能现在由主窗口的工具栏按钮提供

    # 已移除load_outline方法
    # 这个功能现在由主窗口的工具栏按钮提供
