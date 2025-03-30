import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from generators.chapter_generator import ChapterGenerator
from utils.async_utils import GenerationThread, ProgressIndicator
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
        self.model_combo.addItems(["GPT", "Claude", "Gemini"])
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

        self.generate_button = QPushButton("生成章节")
        self.generate_button.clicked.connect(self.generate_chapter)
        self.generate_button.setEnabled(False)
        button_layout.addWidget(self.generate_button)

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

                # 启用生成按钮
                self.generate_button.setEnabled(True)

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
        else:
            return "gpt"  # 默认使用GPT

    def _stream_callback(self, chunk):
        """流式生成回调函数"""
        self.output_edit.insertPlainText(chunk)
        # 滚动到底部
        scrollbar = self.output_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str)
    def _on_progress(self, chunk):
        """处理进度信号"""
        # 注意：不需要再次调用_stream_callback，因为生成器方法中已经调用了
        # 这里仅用于调试目的
        # self._stream_callback(chunk)
        pass

    @pyqtSlot(object)
    def _on_finished(self, result):
        """处理完成信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 更新UI
        self.generate_button.setEnabled(True)
        self.save_button.setEnabled(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("章节生成完成")

        # 如果结果不是字符串，尝试转换
        if not isinstance(result, str):
            try:
                result = str(result)
            except:
                result = "无法解析结果"

        # 保存章节内容
        self.main_window.set_chapter(self.current_volume_index, self.current_chapter_index, result)

        # 显示完成消息
        QMessageBox.information(self, "生成完成", "章节生成完成！")

    @pyqtSlot(str)
    def _on_error(self, error_message):
        """处理错误信号"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 更新UI
        self.generate_button.setEnabled(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("章节生成失败")

        # 显示错误消息
        QMessageBox.warning(self, "生成失败", f"生成章节时出错: {error_message}")

    def generate_chapter(self):
        """生成章节"""
        if self.current_volume_index < 0 or self.current_chapter_index < 0:
            QMessageBox.warning(self, "生成失败", "请先选择一个章节")
            return

        # 获取模型
        model_type = self._get_model_type()
        try:
            model = self.main_window.get_model(model_type)
        except ValueError as e:
            QMessageBox.warning(self, "模型错误", str(e))
            return

        # 创建章节生成器
        self.chapter_generator = ChapterGenerator(model, self.main_window.config_manager)

        # 清空输出
        self.output_edit.clear()

        # 禁用生成按钮
        self.generate_button.setEnabled(False)

        # 显示进度条
        self.progress_bar.setVisible(True)

        # 更新状态栏
        self.main_window.status_bar_manager.show_message("正在生成章节...")

        # 创建并启动生成线程
        self.generation_thread = GenerationThread(
            self.chapter_generator.generate_chapter,
            (self.outline, self.current_volume_index, self.current_chapter_index),
            {"callback": self._stream_callback}
        )

        # 连接信号
        self.generation_thread.progress_signal.connect(self._on_progress)
        self.generation_thread.finished_signal.connect(self._on_finished)
        self.generation_thread.error_signal.connect(self._on_error)

        # 启动线程
        self.generation_thread.start()

    def save_chapter(self):
        """保存章节"""
        if self.current_volume_index < 0 or self.current_chapter_index < 0:
            QMessageBox.warning(self, "保存失败", "请先选择一个章节")
            return

        # 获取章节内容
        content = self.output_edit.toPlainText()
        if not content:
            QMessageBox.warning(self, "保存失败", "章节内容为空")
            return

        # 保存章节内容
        self.main_window.set_chapter(self.current_volume_index, self.current_chapter_index, content)

        # 显示成功消息
        QMessageBox.information(self, "保存成功", "章节已保存")

        # 启用保存按钮
        self.save_button.setEnabled(True)
