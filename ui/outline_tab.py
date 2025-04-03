#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QSplitter, QFileDialog, QProgressBar,
    QDialog, QInputDialog
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
        # 添加标准模型
        self.model_combo.addItems(["GPT", "Claude", "Gemini", "自定义OpenAI", "ModelScope"])

        # 添加自定义模型
        if hasattr(self.main_window, 'custom_openai_models') and self.main_window.custom_openai_models:
            for model_name in self.main_window.custom_openai_models.keys():
                self.model_combo.addItem(model_name)

        model_layout.addRow("AI模型:", self.model_combo)

        # 温度设置已移除

        # 添加提示词模板选择
        template_layout = QHBoxLayout()

        self.template_combo = QComboBox()
        self.template_combo.addItem("选择提示词模板")

        # 加载大纲生成模板
        outline_templates = self.prompt_manager.get_templates_by_category("outline")
        for template in outline_templates:
            self.template_combo.addItem(template.name)

        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_combo)

        # 添加新建、编辑和保存模板按钮
        self.new_template_button = QPushButton("新建")
        self.new_template_button.clicked.connect(self._create_new_template)
        template_layout.addWidget(self.new_template_button)

        self.edit_template_button = QPushButton("编辑")
        self.edit_template_button.setEnabled(False)
        self.edit_template_button.clicked.connect(self._edit_template)
        template_layout.addWidget(self.edit_template_button)

        self.delete_template_button = QPushButton("删除")
        self.delete_template_button.clicked.connect(self._delete_template)
        self.delete_template_button.setEnabled(False)  # 初始禁用
        template_layout.addWidget(self.delete_template_button)

        model_layout.addRow("提示词模板:", template_layout)

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
            self.edit_template_button.setEnabled(False)
            self.delete_template_button.setEnabled(False)
            return

        template_name = self.template_combo.currentText()
        template = self.prompt_manager.get_template(template_name)

        if template:
            # 启用编辑和删除按钮
            self.edit_template_button.setEnabled(True)
            self.delete_template_button.setEnabled(True)

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
        elif model_text == "modelscope":
            return "modelscope"
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

    def _create_new_template(self):
        """创建新模板"""
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("创建新模板")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # 模板名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模板名称:"))
        name_edit = QLineEdit(f"自定义大纲模板_{len(self.prompt_manager.get_templates_by_category('outline')) + 1}")
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        # 模板描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("模板描述:"))
        desc_edit = QLineEdit("自定义大纲生成模板")
        desc_layout.addWidget(desc_edit)
        layout.addLayout(desc_layout)

        # 模板分类
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("模板分类:"))
        category_edit = QLineEdit("outline")
        category_edit.setEnabled(False)  # 固定为outline分类
        category_layout.addWidget(category_edit)
        layout.addLayout(category_layout)

        # 模板内容
        content_label = QLabel("模板内容:")
        layout.addWidget(content_label)

        content_edit = QTextEdit()
        default_content = """请为我创建一部小说的详细大纲，具体要求如下：

小说标题：[用户输入的标题]
小说类型：[用户输入的类型]
主题：[用户输入的主题]
风格：[用户输入的风格]
简介：[用户输入的简介]

卷数：[用户设置的卷数] 卷
每卷章节数：[用户设置的章节数] 章
每章字数：[用户设置的字数] 字

人物设置：
主角数量：[用户设置的主角数量] 个
重要角色数量：[用户设置的重要角色数量] 个
配角数量：[用户设置的配角数量] 个
龙套数量：[用户设置的龙套数量] 个

请生成以下内容：
1. 小说标题
2. 核心主题
3. 主要人物（包括姓名、身份、性格特点和背景故事）
4. 故事梗概
5. 分卷结构（每卷包含标题、简介和具体章节）
6. 世界观设定

特别要求：
1. 卷标题必须包含卷号，如"第一卷：卷标题"
2. 章节标题必须包含章节号，如"第一章：章节标题"

请确保大纲结构完整、逻辑合理，并以JSON格式返回。"""
        content_edit.setPlainText(default_content)
        layout.addWidget(content_edit)

        # 按钮
        button_layout = QHBoxLayout()

        save_button = QPushButton("保存")
        save_button.clicked.connect(dialog.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_name = name_edit.text()
            template_content = content_edit.toPlainText()
            template_desc = desc_edit.text()

            # 添加模板
            success = self.prompt_manager.add_template(
                template_name,
                template_content,
                "outline",
                template_desc
            )

            if success:
                # 添加到下拉框
                self.template_combo.addItem(template_name)
                self.template_combo.setCurrentText(template_name)

                QMessageBox.information(self, "保存成功", f"模板 '{template_name}' 已创建")
            else:
                QMessageBox.warning(self, "保存失败", f"模板 '{template_name}' 已存在或保存失败")

    def _edit_template(self):
        """编辑选中的模板"""
        if self.template_combo.currentIndex() <= 0:
            return

        template_name = self.template_combo.currentText()
        template = self.prompt_manager.get_template(template_name)

        if not template:
            return

        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑模板: {template_name}")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # 模板名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模板名称:"))
        name_edit = QLineEdit(template.name)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        # 模板描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("模板描述:"))
        desc_edit = QLineEdit(template.description)
        desc_layout.addWidget(desc_edit)
        layout.addLayout(desc_layout)

        # 模板分类
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("模板分类:"))
        category_edit = QLineEdit(template.category)
        category_layout.addWidget(category_edit)
        layout.addLayout(category_layout)

        # 模板内容
        content_label = QLabel("模板内容:")
        layout.addWidget(content_label)

        content_edit = QTextEdit()
        content_edit.setPlainText(template.content)
        layout.addWidget(content_edit)

        # 按钮
        button_layout = QHBoxLayout()

        save_button = QPushButton("保存")
        save_button.clicked.connect(dialog.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 检查名称是否变更
            new_name = name_edit.text()
            old_name = template.name

            # 更新模板内容
            success = self.prompt_manager.update_template(
                old_name,
                content_edit.toPlainText(),
                category_edit.text(),
                desc_edit.text()
            )

            # 如果名称变更，需要删除旧模板并创建新模板
            if success and new_name != old_name:
                # 保存模板内容
                content = content_edit.toPlainText()
                category = category_edit.text()
                description = desc_edit.text()

                # 删除旧模板
                self.prompt_manager.delete_template(old_name)

                # 创建新模板
                self.prompt_manager.add_template(
                    new_name,
                    content,
                    category,
                    description
                )

                # 更新下拉框
                current_index = self.template_combo.currentIndex()
                self.template_combo.setItemText(current_index, new_name)

                QMessageBox.information(self, "保存成功", f"模板 '{new_name}' 已更新")
            elif success:
                QMessageBox.information(self, "保存成功", f"模板 '{old_name}' 已更新")

    def _save_as_template(self):
        """保存当前设置为新模板"""
        # 获取当前设置
        title = self.title_edit.text().strip()
        genre = self.genre_edit.text().strip()
        theme = self.theme_edit.toPlainText().strip()
        style = self.style_edit.toPlainText().strip()
        synopsis = self.synopsis_edit.toPlainText().strip()
        volume_count = self.volume_count_spin.value()
        chapters_per_volume = self.chapters_per_volume_spin.value()
        words_per_chapter = self.words_per_chapter_spin.value()

        # 获取角色数量设置
        protagonist_count = self.protagonist_count_spin.value()
        important_count = self.important_count_spin.value()
        supporting_count = self.supporting_count_spin.value()
        minor_count = self.minor_count_spin.value()

        # 创建模板内容
        template_content = f"""请为我创建一部小说的详细大纲，具体要求如下：

小说标题：{title if title else '[用户输入的标题]'}
小说类型：{genre if genre else '[用户输入的类型]'}
主题：{theme if theme else '[用户输入的主题]'}
风格：{style if style else '[用户输入的风格]'}
简介：{synopsis if synopsis else '[用户输入的简介]'}

卷数：{volume_count} 卷
每卷章节数：{chapters_per_volume} 章
每章字数：{words_per_chapter} 字

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
1. 卷标题必须包含卷号，如"第一卷：卷标题"
2. 章节标题必须包含章节号，如"第一章：章节标题"

请确保大纲结构完整、逻辑合理，并以JSON格式返回。"""

        # 获取模板名称
        template_name, ok = QInputDialog.getText(
            self, "保存模板", "请输入模板名称:",
            text=f"自定义大纲模板_{len(self.prompt_manager.get_templates_by_category('outline')) + 1}"
        )

        if ok and template_name:
            # 获取模板描述
            template_desc, ok = QInputDialog.getText(
                self, "模板描述", "请输入模板描述:",
                text=f"基于当前设置创建的大纲模板"
            )

            if ok:
                # 添加模板
                success = self.prompt_manager.add_template(
                    template_name,
                    template_content,
                    "outline",
                    template_desc
                )

                if success:
                    # 添加到下拉框
                    self.template_combo.addItem(template_name)
                    self.template_combo.setCurrentText(template_name)

                    QMessageBox.information(self, "保存成功", f"模板 '{template_name}' 已保存")
                else:
                    QMessageBox.warning(self, "保存失败", f"模板 '{template_name}' 已存在或保存失败")

    def _delete_template(self):
        """删除当前选中的模板"""
        if self.template_combo.currentIndex() <= 0:
            return

        template_name = self.template_combo.currentText()

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模板 '{template_name}' 吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 删除模板
            success = self.prompt_manager.delete_template(template_name)

            if success:
                # 从下拉框中移除
                current_index = self.template_combo.currentIndex()
                self.template_combo.removeItem(current_index)

                # 禁用编辑和删除按钮
                self.edit_template_button.setEnabled(False)
                self.delete_template_button.setEnabled(False)

                QMessageBox.information(self, "删除成功", f"模板 '{template_name}' 已删除")
            else:
                QMessageBox.warning(self, "删除失败", f"模板 '{template_name}' 删除失败")
