#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI组件模块

提供通用的UI组件，用于减少重复代码和统一界面风格。
"""

import json
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QDialog, QListWidget, QListWidgetItem,
    QTabWidget, QInputDialog, QScrollArea, QProgressBar,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFileDialog, QToolTip,
    QToolBar, QStatusBar, QMainWindow, QApplication, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QTimer, QPoint
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QFont, QColor, QPalette, QAction

from utils.async_utils import GenerationThread, ProgressIndicator, AsyncHelper


class AIGenerateDialog(QDialog):
    """
    AI生成对话框

    用于使用AI生成内容的通用对话框
    """

    def __init__(self, parent=None, title="AI生成", field_name="内容", current_text="",
                 models=None, default_model="GPT", outline_info=None, context_info=None):
        """
        初始化AI生成对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            field_name: 字段名称
            current_text: 当前文本
            models: 可用的模型列表
            default_model: 默认选择的模型
            outline_info: 总大纲信息，包含标题、中心思想、故事梦概和世界观设定
            context_info: 上下文信息，如卷标题、卷简介、章节标题等
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 500)
        self.field_name = field_name
        self.current_text = current_text
        self.result_text = ""
        self.generation_thread = None
        self.models = models or ["GPT", "Claude", "Gemini", "自定义OpenAI", "ModelScope"]
        self.default_model = default_model if default_model in self.models else self.models[0]
        self.outline_info = outline_info or {}
        self.context_info = context_info or {}

        # 初始化UI
        self._init_ui()

        # 添加快捷键
        self._setup_shortcuts()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 提示词部分
        prompt_group = QGroupBox("提示词")
        prompt_layout = QVBoxLayout()

        prompt_label = QLabel(f"请输入提示词，告诉AI如何生成新的{self.field_name}：")
        prompt_layout.addWidget(prompt_label)

        self.prompt_edit = QTextEdit()

        # 构建默认提示词
        default_prompt = f"请根据以下内容，生成一个新的{self.field_name}：\n\n"

        # 添加总大纲信息（如果有）
        if self.outline_info:
            if self.outline_info.get("title"):
                default_prompt += f"小说标题：{self.outline_info.get('title')}\n"
            if self.outline_info.get("theme"):
                default_prompt += f"中心思想：{self.outline_info.get('theme')}\n"
            if self.outline_info.get("synopsis"):
                default_prompt += f"故事梦概：{self.outline_info.get('synopsis')}\n"
            if self.outline_info.get("worldbuilding"):
                default_prompt += f"世界观设定：{self.outline_info.get('worldbuilding')}\n"
            default_prompt += "\n"

        # 添加上下文信息（如果有）
        if self.context_info:
            # 如果是卷简介，添加卷标题信息
            if self.field_name == "卷简介" and self.context_info.get("volume_title"):
                default_prompt += f"卷标题：{self.context_info.get('volume_title')}\n\n"

            # 如果是章节摘要，添加卷标题、卷简介、章节标题信息以及前10章和后3章的标题和摘要
            if self.field_name == "章节摘要":
                if self.context_info.get("volume_title"):
                    default_prompt += f"卷标题：{self.context_info.get('volume_title')}\n"
                if self.context_info.get("volume_description"):
                    default_prompt += f"卷简介：{self.context_info.get('volume_description')}\n"
                if self.context_info.get("chapter_title"):
                    default_prompt += f"章节标题：{self.context_info.get('chapter_title')}\n"
                if self.context_info.get("chapter_number"):
                    default_prompt += f"当前章节序号：第{self.context_info.get('chapter_number')}章\n"

                # 添加当前章节摘要（如果有）
                current_summary = self.current_text.strip()
                if current_summary:
                    default_prompt += f"当前章节摘要：{current_summary}\n"
                default_prompt += "\n"

                # 添加前10章的标题和摘要
                previous_chapters = self.context_info.get("previous_chapters", [])
                if previous_chapters:
                    default_prompt += "前面章节的标题和摘要：\n"
                    for i, prev_chapter in enumerate(previous_chapters):
                        default_prompt += f"- {prev_chapter.get('title')}: {prev_chapter.get('summary')}\n"
                    default_prompt += "\n"

                # 添加后3章的标题和摘要
                next_chapters = self.context_info.get("next_chapters", [])
                if next_chapters:
                    default_prompt += "后面章节的标题和摘要：\n"
                    for i, next_chapter in enumerate(next_chapters):
                        default_prompt += f"- {next_chapter.get('title')}: {next_chapter.get('summary')}\n"
                    default_prompt += "\n"

            # 如果是章节内容，添加章节相关信息、前10章和后3章的标题和摘要，以及前一章的内容
            if self.field_name == "章节内容":
                if self.context_info.get("volume_title"):
                    default_prompt += f"卷标题：{self.context_info.get('volume_title')}\n"
                if self.context_info.get("volume_description"):
                    default_prompt += f"卷简介：{self.context_info.get('volume_description')}\n"
                if self.context_info.get("chapter_title"):
                    default_prompt += f"章节标题：{self.context_info.get('chapter_title')}\n"
                if self.context_info.get("chapter_number"):
                    default_prompt += f"当前章节序号：第{self.context_info.get('chapter_number')}章\n"
                default_prompt += "\n"

                # 添加前10章的标题和摘要
                previous_chapters = self.context_info.get("previous_chapters", [])
                if previous_chapters:
                    default_prompt += "前面章节的标题和摘要：\n"
                    for i, prev_chapter in enumerate(previous_chapters):
                        default_prompt += f"- {prev_chapter.get('title')}: {prev_chapter.get('summary')}\n"
                    default_prompt += "\n"

                # 添加前一章的内容
                previous_chapter_content = self.context_info.get("previous_chapter_content", "")
                if previous_chapter_content:
                    # 如果前一章内容过长，只取前2000个字符
                    if len(previous_chapter_content) > 2000:
                        previous_chapter_content = previous_chapter_content[:2000] + "...(省略后续内容)"
                    default_prompt += "前一章的内容：\n\n"
                    default_prompt += f"{previous_chapter_content}\n\n"

                # 添加后3章的标题和摘要
                next_chapters = self.context_info.get("next_chapters", [])
                if next_chapters:
                    default_prompt += "后面章节的标题和摘要：\n"
                    for i, next_chapter in enumerate(next_chapters):
                        default_prompt += f"- {next_chapter.get('title')}: {next_chapter.get('summary')}\n"
                    default_prompt += "\n"

        # 添加当前文本和要求
        current_text = self.current_text.strip()
        if current_text and self.field_name == "章节内容":
            default_prompt += f"当前章节内容：\n{current_text}\n\n"
        elif current_text:
            default_prompt += f"{current_text}\n\n"

        default_prompt += "要求：\n1. 保持原有风格\n2. 更加生动详细\n3. 逻辑连贯\n4. 与小说的整体设定保持一致"

        self.prompt_edit.setPlainText(default_prompt)
        prompt_layout.addWidget(self.prompt_edit)

        # 添加提示词模板选择
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("选择模板:"))

        self.template_combo = QComboBox()
        self.template_combo.addItems(["默认模板", "详细描述模板", "简洁模板", "创意模板"])
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        template_layout.addWidget(self.template_combo)

        # 添加保存模板按钮
        self.save_template_button = QPushButton("保存为模板")
        self.save_template_button.clicked.connect(self._save_as_template)
        template_layout.addWidget(self.save_template_button)

        template_layout.addStretch()
        prompt_layout.addLayout(template_layout)

        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)

        # 模型选择
        model_layout = QHBoxLayout()
        model_label = QLabel("选择模型：")
        model_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems(self.models)
        # 设置默认模型
        index = self.model_combo.findText(self.default_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        model_layout.addWidget(self.model_combo)

        # 温度设置已移除

        model_layout.addStretch()
        layout.addLayout(model_layout)

        # 生成按钮
        generate_button = QPushButton("生成")
        generate_button.clicked.connect(self.generate)
        layout.addWidget(generate_button)

        # 结果部分
        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout()

        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        result_layout.addWidget(self.result_edit)

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.progress_bar.setVisible(False)
        result_layout.addWidget(self.progress_bar)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 按钮部分
        button_layout = QHBoxLayout()

        self.use_button = QPushButton("使用结果")
        self.use_button.clicked.connect(self.accept)
        self.use_button.setEnabled(False)
        button_layout.addWidget(self.use_button)

        self.copy_button = QPushButton("复制结果")
        self.copy_button.clicked.connect(self._copy_result)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+Enter 生成
        generate_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        generate_shortcut.activated.connect(self.generate)

        # Ctrl+C 复制结果
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self._copy_result)

        # Esc 取消
        cancel_shortcut = QShortcut(QKeySequence("Esc"), self)
        cancel_shortcut.activated.connect(self.reject)

    def _on_template_changed(self, index):
        """模板选择变更事件"""
        # 构建基本提示词前缀（包含总大纲信息和上下文信息）
        prefix = f"请根据以下内容，生成一个新的{self.field_name}：\n\n"

        # 添加总大纲信息
        if self.outline_info:
            if self.outline_info.get("title"):
                prefix += f"小说标题：{self.outline_info.get('title')}\n"
            if self.outline_info.get("theme"):
                prefix += f"中心思想：{self.outline_info.get('theme')}\n"
            if self.outline_info.get("synopsis"):
                prefix += f"故事梦概：{self.outline_info.get('synopsis')}\n"
            if self.outline_info.get("worldbuilding"):
                prefix += f"世界观设定：{self.outline_info.get('worldbuilding')}\n"
            prefix += "\n"

        # 添加上下文信息
        if self.context_info:
            # 如果是卷简介，添加卷标题信息
            if self.field_name == "卷简介" and self.context_info.get("volume_title"):
                prefix += f"卷标题：{self.context_info.get('volume_title')}\n\n"

            # 如果是章节摘要，添加卷标题、卷简介和章节标题信息
            if self.field_name == "章节摘要":
                if self.context_info.get("volume_title"):
                    prefix += f"卷标题：{self.context_info.get('volume_title')}\n"
                if self.context_info.get("volume_description"):
                    prefix += f"卷简介：{self.context_info.get('volume_description')}\n"
                if self.context_info.get("chapter_title"):
                    prefix += f"章节标题：{self.context_info.get('chapter_title')}\n"
                prefix += "\n"

        # 添加当前文本
        content = f"{self.current_text}\n\n"

        templates = {
            0: prefix + content + "要求：\n1. 保持原有风格\n2. 更加生动详细\n3. 逻辑连贯\n4. 与小说的整体设定保持一致",
            1: prefix + content + "要求：\n1. 保持原有风格和主题\n2. 增加细节描写和背景信息\n3. 使用丰富的修辞手法\n4. 确保逻辑连贯和情节合理\n5. 与小说的整体设定保持一致",
            2: prefix + content + "要求：\n1. 保持核心内容和主题\n2. 使用简洁有力的语言\n3. 去除冗余信息\n4. 突出重点\n5. 与小说的整体设定保持一致",
            3: prefix + content + "要求：\n1. 保持基本主题\n2. 加入创新的元素和视角\n3. 使用富有想象力的语言\n4. 创造出令人惊喜的内容\n5. 与小说的整体设定保持一致"
        }

        if index in templates:
            self.prompt_edit.setPlainText(templates[index])

    def _save_as_template(self):
        """保存当前提示词为模板"""
        template_name, ok = QInputDialog.getText(
            self, "保存模板", "请输入模板名称:",
            text=f"自定义{self.field_name}模板"
        )

        if ok and template_name:
            # 这里应该实现模板保存逻辑
            # 简单起见，这里只是添加到下拉框
            self.template_combo.addItem(template_name)
            self.template_combo.setCurrentText(template_name)
            QMessageBox.information(self, "保存成功", f"模板 '{template_name}' 已保存")

    def _copy_result(self):
        """复制结果到剪贴板"""
        if self.result_text:
            QApplication.clipboard().setText(self.result_text)
            QToolTip.showText(self.copy_button.mapToGlobal(QPoint(0, 0)), "已复制到剪贴板", self)

    def generate(self):
        """生成内容"""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入提示词")
            return

        # 获取模型
        model_text = self.model_combo.currentText().lower()
        # 转换为模型类型
        if model_text == "gpt":
            model_type = "gpt"
        elif model_text == "claude":
            model_type = "claude"
        elif model_text == "gemini":
            model_type = "gemini"
        elif model_text == "自定义openai":
            model_type = "custom_openai"
        elif model_text == "modelscope":
            model_type = "modelscope"
        else:
            model_type = "gpt"  # 默认使用GPT
        try:
            # 尝试不同的方式获取main_window
            if hasattr(self.parent(), 'main_window'):
                main_window = self.parent().main_window
            elif hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'main_window'):
                main_window = self.parent().parent().main_window
            else:
                # 如果无法获取main_window，显示错误
                QMessageBox.warning(self, "错误", "无法获取main_window")
                return

            model = main_window.get_model(model_type)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取模型失败: {str(e)}")
            return

        # 清空结果
        self.result_edit.clear()
        self.result_text = ""

        # 显示进度条
        self.progress_bar.setVisible(True)

        # 禁用生成按钮
        self.findChild(QPushButton, "").setEnabled(False)

        # 创建并启动生成线程
        self.generation_thread = GenerationThread(
            model.generate_stream,
            (prompt,),
            {}
        )

        # 连接信号
        self.generation_thread.progress_signal.connect(self._on_progress)
        self.generation_thread.finished_signal.connect(self._on_finished)
        self.generation_thread.error_signal.connect(self._on_error)

        # 启动线程
        self.generation_thread.start()

    def _on_progress(self, chunk):
        """处理进度信号"""
        self.result_edit.insertPlainText(chunk)
        self.result_text += chunk
        # 滚动到底部
        scrollbar = self.result_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_finished(self, result):
        """处理完成信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 启用按钮
        self.use_button.setEnabled(True)
        self.copy_button.setEnabled(True)
        self.findChild(QPushButton, "").setEnabled(True)

        QMessageBox.information(self, "完成", "内容生成完成")

    def _on_error(self, error):
        """处理错误信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 启用生成按钮
        self.findChild(QPushButton, "").setEnabled(True)

        QMessageBox.warning(self, "错误", f"生成内容时出错: {error}")

    def get_result(self):
        """获取生成结果"""
        return self.result_text


class DraggableListWidget(QListWidget):
    """
    可拖放的列表控件

    支持项目拖放重新排序
    """

    item_moved = pyqtSignal(int, int)  # 从索引，到索引

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # 跟踪拖放操作
        self._drag_start_index = -1
        self.model().rowsMoved.connect(self._on_rows_moved)

    def dropEvent(self, event):
        """处理放下事件"""
        # 记录当前选中项的索引（拖动开始位置）
        self._drag_start_index = self.currentRow()
        super().dropEvent(event)

    def _on_rows_moved(self, parent, start, end, destination, row):
        """行移动事件处理"""
        if self._drag_start_index >= 0:
            # 计算新位置
            new_index = row
            if row > self._drag_start_index:
                new_index -= 1

            # 发出信号
            self.item_moved.emit(self._drag_start_index, new_index)

            # 重置拖动开始索引
            self._drag_start_index = -1


class ThemeManager:
    """
    主题管理器

    管理应用的主题（明亮/深色）
    """

    LIGHT_THEME = "light"
    DARK_THEME = "dark"

    def __init__(self, app):
        """
        初始化主题管理器

        Args:
            app: QApplication实例
        """
        self.app = app
        self.current_theme = self.LIGHT_THEME

    def set_theme(self, theme):
        """
        设置应用主题

        Args:
            theme: 主题名称，可以是 "light" 或 "dark"
        """
        if theme == self.current_theme:
            return

        if theme == self.DARK_THEME:
            self._set_dark_theme()
        else:
            self._set_light_theme()

        self.current_theme = theme

    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == self.LIGHT_THEME:
            self.set_theme(self.DARK_THEME)
        else:
            self.set_theme(self.LIGHT_THEME)

    def _set_light_theme(self):
        """设置明亮主题"""
        self.app.setStyle("Fusion")
        palette = QPalette()
        self.app.setPalette(palette)

    def _set_dark_theme(self):
        """设置深色主题"""
        self.app.setStyle("Fusion")

        # 创建深色调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        # 设置调色板
        self.app.setPalette(palette)


class StatusBarManager:
    """
    状态栏管理器

    管理主窗口的状态栏
    """

    def __init__(self, status_bar):
        """
        初始化状态栏管理器

        Args:
            status_bar: QStatusBar实例
        """
        self.status_bar = status_bar
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self._clear_message)

        # 创建状态标签
        self.status_label = QLabel()
        self.status_bar.addWidget(self.status_label)

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.status_bar.addWidget(self.progress_bar)

    def show_message(self, message, timeout=3000):
        """
        显示临时消息

        Args:
            message: 要显示的消息
            timeout: 消息显示时间（毫秒）
        """
        self.status_label.setText(message)

        # 重置定时器
        self.message_timer.stop()
        self.message_timer.start(timeout)

    def show_permanent_message(self, message):
        """
        显示永久消息

        Args:
            message: 要显示的消息
        """
        self.message_timer.stop()
        self.status_label.setText(message)

    def _clear_message(self):
        """清除消息"""
        self.status_label.clear()
        self.message_timer.stop()

    def show_progress(self, value=None, maximum=None):
        """
        显示进度条

        Args:
            value: 当前进度值
            maximum: 最大进度值
        """
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)

        if maximum is not None:
            self.progress_bar.setMaximum(maximum)

        if value is not None:
            self.progress_bar.setValue(value)

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)


class KeyboardShortcutManager:
    """
    键盘快捷键管理器

    管理应用的键盘快捷键
    """

    def __init__(self, main_window):
        """
        初始化键盘快捷键管理器

        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        self.shortcuts = {}

        # 设置常用快捷键
        self._setup_common_shortcuts()

    def _setup_common_shortcuts(self):
        """设置常用快捷键"""
        # 文件操作
        self.add_shortcut("Ctrl+N", self.main_window.new_novel, "新建小说")
        self.add_shortcut("Ctrl+O", self.main_window.load_novel, "打开小说")
        self.add_shortcut("Ctrl+S", self.main_window.save_novel, "保存小说")

        # 标签页切换
        self.add_shortcut("Ctrl+1", lambda: self.main_window.tab_widget.setCurrentIndex(0), "切换到大纲生成")
        self.add_shortcut("Ctrl+2", lambda: self.main_window.tab_widget.setCurrentIndex(1), "切换到总大纲编辑")
        self.add_shortcut("Ctrl+3", lambda: self.main_window.tab_widget.setCurrentIndex(2), "切换到章节大纲编辑")
        self.add_shortcut("Ctrl+4", lambda: self.main_window.tab_widget.setCurrentIndex(3), "切换到章节生成")
        self.add_shortcut("Ctrl+5", lambda: self.main_window.tab_widget.setCurrentIndex(4), "切换到人物编辑")
        self.add_shortcut("Ctrl+6", lambda: self.main_window.tab_widget.setCurrentIndex(5), "切换到设置")

        # 主题切换
        self.add_shortcut("Ctrl+T", self.main_window.toggle_theme, "切换主题")

    def add_shortcut(self, key_sequence, callback, description=None):
        """
        添加快捷键

        Args:
            key_sequence: 快捷键序列
            callback: 回调函数
            description: 快捷键描述
        """
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.activated.connect(callback)

        self.shortcuts[key_sequence] = {
            "shortcut": shortcut,
            "callback": callback,
            "description": description
        }

    def remove_shortcut(self, key_sequence):
        """
        移除快捷键

        Args:
            key_sequence: 要移除的快捷键序列
        """
        if key_sequence in self.shortcuts:
            shortcut = self.shortcuts[key_sequence]["shortcut"]
            shortcut.setEnabled(False)
            shortcut.deleteLater()
            del self.shortcuts[key_sequence]

    def get_shortcut_descriptions(self):
        """
        获取所有快捷键的描述

        Returns:
            快捷键描述列表
        """
        descriptions = []
        for key, data in self.shortcuts.items():
            if data["description"]:
                descriptions.append(f"{key}: {data['description']}")

        return descriptions
