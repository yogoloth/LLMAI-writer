#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QSplitter, QFileDialog, QProgressBar,
    QDialog, QInputDialog, QScrollArea, QListWidget, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from utils.knowledge_base_manager import KnowledgeBaseManager
from utils.text_processor import TextProcessor
from utils.json_processor import JsonProcessor
from utils.pdf_processor import PdfProcessor
from utils.docx_processor import DocxProcessor
from embedding_models.siliconflow_embedding import SiliconFlowEmbedding
from utils.async_utils import AsyncHelper, ProgressIndicator

class KnowledgeBaseTab(QWidget):
    """知识库标签页"""

    def __init__(self, main_window):
        """
        初始化知识库标签页

        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        self.config_manager = main_window.config_manager
        self.async_helper = main_window.async_helper
        self.progress_indicator = main_window.progress_indicator
        self.knowledge_base_manager = None
        self.embedding_model = None
        self.active_threads = []

        # 初始化UI
        self._init_ui()

        # 初始化嵌入模型和知识库管理器
        self._init_embedding_model()

    def closeEvent(self, event):
        """
        关闭事件处理

        Args:
            event: 关闭事件
        """
        # 取消所有活动线程
        for thread in self.active_threads:
            if thread.isRunning():
                thread.cancel()

        # 清空线程列表
        self.active_threads.clear()

        # 调用父类方法
        super().closeEvent(event)

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # 创建知识库管理标签页
        manage_tab = QWidget()
        manage_layout = QVBoxLayout(manage_tab)
        tab_widget.addTab(manage_tab, "知识库管理")

        # 创建知识库查询标签页
        query_tab = QWidget()
        query_layout = QVBoxLayout(query_tab)
        tab_widget.addTab(query_tab, "知识库查询")

        # 初始化知识库管理标签页
        self._init_manage_tab(manage_layout)

        # 初始化知识库查询标签页
        self._init_query_tab(query_layout)

    def _init_manage_tab(self, layout):
        """
        初始化知识库管理标签页

        Args:
            layout: 布局
        """
        # 创建嵌入模型选择组
        model_group = QGroupBox("嵌入模型设置")
        model_layout = QFormLayout()

        # 嵌入模型选择
        self.embedding_model_combo = QComboBox()
        self.embedding_model_combo.addItem("SiliconFlow")
        model_layout.addRow("嵌入模型:", self.embedding_model_combo)

        # 嵌入模型名称
        self.embedding_model_name = QLineEdit()
        self.embedding_model_name.setText(self.config_manager.get_embedding_model_name('siliconflow') or "BAAI/bge-m3")
        model_layout.addRow("模型名称:", self.embedding_model_name)

        # 保存设置按钮
        self.save_model_button = QPushButton("保存设置")
        self.save_model_button.clicked.connect(self._save_model_settings)
        model_layout.addRow("", self.save_model_button)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # 创建知识库列表组
        kb_list_group = QGroupBox("知识库列表")
        kb_list_layout = QVBoxLayout()

        # 知识库列表
        self.kb_list = QListWidget()
        self.kb_list.itemClicked.connect(self._on_kb_selected)
        kb_list_layout.addWidget(self.kb_list)

        # 按钮布局
        kb_buttons_layout = QHBoxLayout()

        # 刷新按钮
        self.refresh_kb_button = QPushButton("刷新列表")
        self.refresh_kb_button.clicked.connect(self._refresh_kb_list)
        kb_buttons_layout.addWidget(self.refresh_kb_button)

        # 删除按钮
        self.delete_kb_button = QPushButton("删除知识库")
        self.delete_kb_button.clicked.connect(self._delete_kb)
        self.delete_kb_button.setEnabled(False)
        kb_buttons_layout.addWidget(self.delete_kb_button)

        kb_list_layout.addLayout(kb_buttons_layout)
        kb_list_group.setLayout(kb_list_layout)
        layout.addWidget(kb_list_group)

        # 创建新知识库组
        new_kb_group = QGroupBox("创建新知识库")
        new_kb_layout = QFormLayout()

        # 知识库名称
        self.kb_name_edit = QLineEdit()
        new_kb_layout.addRow("知识库名称:", self.kb_name_edit)

        # 文本块大小
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 10000)
        self.chunk_size_spin.setValue(1000)
        new_kb_layout.addRow("文本块大小:", self.chunk_size_spin)

        # 文本块重叠大小
        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setRange(0, 5000)
        self.chunk_overlap_spin.setValue(200)
        new_kb_layout.addRow("文本块重叠大小:", self.chunk_overlap_spin)

        # 选择文件按钮
        self.select_files_button = QPushButton("选择文件")
        self.select_files_button.clicked.connect(self._select_files)
        new_kb_layout.addRow("", self.select_files_button)

        # 选中的文件列表
        self.selected_files_list = QListWidget()
        new_kb_layout.addRow("选中的文件:", self.selected_files_list)

        # 清空选择按钮
        self.clear_files_button = QPushButton("清空选择")
        self.clear_files_button.clicked.connect(self._clear_files)
        new_kb_layout.addRow("", self.clear_files_button)

        # 创建知识库按钮
        self.create_kb_button = QPushButton("创建知识库")
        self.create_kb_button.clicked.connect(self._create_kb)
        new_kb_layout.addRow("", self.create_kb_button)

        new_kb_group.setLayout(new_kb_layout)
        layout.addWidget(new_kb_group)

    def _init_query_tab(self, layout):
        """
        初始化知识库查询标签页

        Args:
            layout: 布局
        """
        # 创建知识库选择组
        kb_select_group = QGroupBox("知识库选择")
        kb_select_layout = QFormLayout()

        # 知识库选择
        self.query_kb_combo = QComboBox()
        self.query_kb_combo.currentIndexChanged.connect(self._on_query_kb_changed)
        kb_select_layout.addRow("选择知识库:", self.query_kb_combo)

        # 刷新按钮
        self.refresh_query_kb_button = QPushButton("刷新列表")
        self.refresh_query_kb_button.clicked.connect(self._refresh_query_kb_list)
        kb_select_layout.addRow("", self.refresh_query_kb_button)

        kb_select_group.setLayout(kb_select_layout)
        layout.addWidget(kb_select_group)

        # 创建查询组
        query_group = QGroupBox("查询")
        query_layout = QVBoxLayout()

        # 查询输入
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("输入查询内容...")
        query_layout.addWidget(self.query_input)

        # 查询参数
        query_params_layout = QFormLayout()

        # 返回结果数量
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 20)
        self.top_k_spin.setValue(5)
        query_params_layout.addRow("返回结果数量:", self.top_k_spin)

        query_layout.addLayout(query_params_layout)

        # 查询按钮
        self.query_button = QPushButton("查询")
        self.query_button.clicked.connect(self._query_kb)
        self.query_button.setEnabled(False)
        query_layout.addWidget(self.query_button)

        query_group.setLayout(query_layout)
        layout.addWidget(query_group)

        # 创建结果组
        result_group = QGroupBox("查询结果")
        result_layout = QVBoxLayout()

        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

    def _init_embedding_model(self):
        """初始化嵌入模型和知识库管理器"""
        try:
            # 初始化嵌入模型
            self.embedding_model = SiliconFlowEmbedding(self.config_manager)

            # 初始化知识库管理器
            self.knowledge_base_manager = KnowledgeBaseManager(self.config_manager, self.embedding_model)

            # 注册文档处理器
            self.knowledge_base_manager.register_processor(TextProcessor())
            self.knowledge_base_manager.register_processor(JsonProcessor())
            self.knowledge_base_manager.register_processor(PdfProcessor())
            self.knowledge_base_manager.register_processor(DocxProcessor())

            # 刷新知识库列表
            self._refresh_kb_list()
            self._refresh_query_kb_list()
        except Exception as e:
            print(f"初始化嵌入模型和知识库管理器出错: {e}")
            QMessageBox.warning(self, "初始化失败", f"初始化嵌入模型和知识库管理器出错: {e}")

    def _save_model_settings(self):
        """保存嵌入模型设置"""
        try:
            # 获取模型名称
            model_name = self.embedding_model_name.text().strip()
            if not model_name:
                QMessageBox.warning(self, "保存失败", "模型名称不能为空")
                return

            # 保存设置
            self.config_manager.set_config("EMBEDDING_MODELS", "siliconflow_embedding_model", model_name)
            self.config_manager.save_config()

            # 重新初始化嵌入模型
            self._init_embedding_model()

            QMessageBox.information(self, "保存成功", "嵌入模型设置已保存")
        except Exception as e:
            print(f"保存嵌入模型设置出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存嵌入模型设置出错: {e}")

    def _refresh_kb_list(self):
        """刷新知识库列表"""
        try:
            # 清空列表
            self.kb_list.clear()

            # 获取知识库列表
            kb_list = self.knowledge_base_manager.list_knowledge_bases()

            # 添加到列表
            for kb_name in kb_list:
                self.kb_list.addItem(kb_name)

            # 禁用删除按钮
            self.delete_kb_button.setEnabled(False)
        except Exception as e:
            print(f"刷新知识库列表出错: {e}")

    def _refresh_query_kb_list(self):
        """刷新查询知识库列表"""
        try:
            # 保存当前选择
            current_kb = self.query_kb_combo.currentText()

            # 清空列表
            self.query_kb_combo.clear()

            # 获取知识库列表
            kb_list = self.knowledge_base_manager.list_knowledge_bases()

            # 添加到列表
            for kb_name in kb_list:
                self.query_kb_combo.addItem(kb_name)

            # 恢复选择
            index = self.query_kb_combo.findText(current_kb)
            if index >= 0:
                self.query_kb_combo.setCurrentIndex(index)

            # 启用/禁用查询按钮
            self.query_button.setEnabled(self.query_kb_combo.count() > 0)
        except Exception as e:
            print(f"刷新查询知识库列表出错: {e}")

    def _on_kb_selected(self, item):
        """
        知识库选中事件处理

        Args:
            item: 选中的项
        """
        # 启用删除按钮
        self.delete_kb_button.setEnabled(True)

    def _on_query_kb_changed(self, index):
        """
        查询知识库选择变更事件处理

        Args:
            index: 选中的索引
        """
        # 启用/禁用查询按钮
        self.query_button.setEnabled(index >= 0)

    def _select_files(self):
        """选择文件"""
        # 支持的文件类型
        file_filter = "所有支持的文件 (*.txt *.md *.json *.pdf *.docx *.doc *.ainovel);;文本文件 (*.txt *.md);;JSON文件 (*.json);;PDF文件 (*.pdf);;Word文件 (*.docx *.doc);;AI小说文件 (*.ainovel)"

        # 选择文件
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", file_filter)

        if not file_paths:
            return

        # 添加到列表
        for file_path in file_paths:
            # 检查是否已存在
            items = self.selected_files_list.findItems(file_path, Qt.MatchFlag.MatchExactly)
            if not items:
                self.selected_files_list.addItem(file_path)

    def _clear_files(self):
        """清空选择的文件"""
        self.selected_files_list.clear()

    def _delete_kb(self):
        """删除知识库"""
        # 获取选中的知识库
        selected_items = self.kb_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "删除失败", "请先选择一个知识库")
            return

        kb_name = selected_items[0].text()

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除知识库 '{kb_name}' 吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 删除知识库
        success = self.knowledge_base_manager.delete_knowledge_base(kb_name)

        if success:
            QMessageBox.information(self, "删除成功", f"知识库 '{kb_name}' 已删除")

            # 刷新列表
            self._refresh_kb_list()
            self._refresh_query_kb_list()
        else:
            QMessageBox.warning(self, "删除失败", f"删除知识库 '{kb_name}' 失败")

    def _create_kb_async(self, kb_name, documents, chunk_size, chunk_overlap):
        """
        异步创建知识库

        Args:
            kb_name: 知识库名称
            documents: 文档路径列表
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小

        Returns:
            协程对象
        """
        # 直接返回协程对象，不要调用它
        return self.knowledge_base_manager.create_knowledge_base(kb_name, documents, chunk_size, chunk_overlap)

    def _create_kb(self):
        """创建知识库"""
        # 获取知识库名称
        kb_name = self.kb_name_edit.text().strip()
        if not kb_name:
            QMessageBox.warning(self, "创建失败", "请输入知识库名称")
            return

        # 获取文本块大小和重叠大小
        chunk_size = self.chunk_size_spin.value()
        chunk_overlap = self.chunk_overlap_spin.value()

        # 获取选中的文件
        documents = []
        for i in range(self.selected_files_list.count()):
            documents.append(self.selected_files_list.item(i).text())

        if not documents:
            QMessageBox.warning(self, "创建失败", "请选择至少一个文件")
            return

        # 确认创建
        reply = QMessageBox.question(
            self,
            "确认创建",
            f"确定要创建知识库 '{kb_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 显示进度指示器
        self.progress_indicator.start()
        self.main_window.status_bar_manager.show_message(f"正在创建知识库 '{kb_name}'...")

        # 异步创建知识库
        thread = self.async_helper.run_async(
            self._create_kb_async(kb_name, documents, chunk_size, chunk_overlap),
            self._on_create_kb_done,
            lambda e: self._on_create_kb_error(e, kb_name)
        )

        # 保存线程引用
        self.active_threads.append(thread)

    def _on_create_kb_done(self, success):
        """
        创建知识库完成事件处理

        Args:
            success: 是否创建成功
        """
        # 停止进度指示器
        self.progress_indicator.stop()

        # 清理已完成的线程
        self._cleanup_finished_threads()

        kb_name = self.kb_name_edit.text().strip()

        if success:
            self.main_window.status_bar_manager.show_message(f"知识库 '{kb_name}' 创建成功")
            QMessageBox.information(self, "创建成功", f"知识库 '{kb_name}' 创建成功")

            # 清空输入
            self.kb_name_edit.clear()
            self.selected_files_list.clear()

            # 刷新列表
            self._refresh_kb_list()
            self._refresh_query_kb_list()
        else:
            self.main_window.status_bar_manager.show_message(f"知识库 '{kb_name}' 创建失败")
            QMessageBox.warning(self, "创建失败", f"知识库 '{kb_name}' 创建失败")

    def _on_create_kb_error(self, error, kb_name):
        """
        创建知识库错误事件处理

        Args:
            error: 错误信息
            kb_name: 知识库名称
        """
        # 停止进度指示器
        self.progress_indicator.stop()

        # 清理已完成的线程
        self._cleanup_finished_threads()

        # 显示错误消息
        self.main_window.status_bar_manager.show_message(f"创建知识库 '{kb_name}' 出错: {error}")
        QMessageBox.critical(self, "创建失败", f"创建知识库 '{kb_name}' 出错: {error}")

    def _query_kb_async(self, kb_name, query, top_k):
        """
        异步查询知识库

        Args:
            kb_name: 知识库名称
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            协程对象
        """
        # 直接返回协程对象，不要调用它
        return self.knowledge_base_manager.query(kb_name, query, top_k)

    def _query_kb(self):
        """查询知识库"""
        # 获取知识库名称
        kb_name = self.query_kb_combo.currentText()
        if not kb_name:
            QMessageBox.warning(self, "查询失败", "请选择一个知识库")
            return

        # 获取查询文本
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "查询失败", "请输入查询内容")
            return

        # 获取返回结果数量
        top_k = self.top_k_spin.value()

        # 显示进度指示器
        self.progress_indicator.start()
        self.main_window.status_bar_manager.show_message(f"正在查询知识库 '{kb_name}'...")

        # 异步查询知识库
        thread = self.async_helper.run_async(
            self._query_kb_async(kb_name, query, top_k),
            self._on_query_kb_done,
            lambda e: self._on_query_kb_error(e, kb_name)
        )

        # 保存线程引用
        self.active_threads.append(thread)

    def _on_query_kb_done(self, results):
        """
        查询知识库完成事件处理

        Args:
            results: 查询结果列表
        """
        # 停止进度指示器
        self.progress_indicator.stop()

        # 清理已完成的线程
        self._cleanup_finished_threads()

        kb_name = self.query_kb_combo.currentText()

        if results:
            self.main_window.status_bar_manager.show_message(f"查询知识库 '{kb_name}' 成功，找到 {len(results)} 条结果")

            # 显示结果
            result_text = f"查询知识库 '{kb_name}' 成功，找到 {len(results)} 条结果：\n\n"

            for i, result in enumerate(results):
                result_text += f"结果 {i+1}（相似度：{1.0 - result['score']:.4f}）：\n"
                result_text += f"{result['text']}\n\n"

            self.result_text.setPlainText(result_text)
        else:
            self.main_window.status_bar_manager.show_message(f"查询知识库 '{kb_name}' 未找到结果")
            self.result_text.setPlainText(f"查询知识库 '{kb_name}' 未找到结果")

    def _on_query_kb_error(self, error, kb_name):
        """
        查询知识库错误事件处理

        Args:
            error: 错误信息
            kb_name: 知识库名称
        """
        # 停止进度指示器
        self.progress_indicator.stop()

        # 清理已完成的线程
        self._cleanup_finished_threads()

        # 显示错误消息
        self.main_window.status_bar_manager.show_message(f"查询知识库 '{kb_name}' 出错: {error}")
        QMessageBox.critical(self, "查询失败", f"查询知识库 '{kb_name}' 出错: {error}")
        self.result_text.setPlainText(f"查询知识库 '{kb_name}' 出错: {error}")

    def _cleanup_finished_threads(self):
        """清理已完成的线程"""
        # 过滤出已完成的线程
        finished_threads = [thread for thread in self.active_threads if not thread.isRunning()]

        # 从活动线程列表中移除已完成的线程
        for thread in finished_threads:
            self.active_threads.remove(thread)
