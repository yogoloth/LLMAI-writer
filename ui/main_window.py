import sys
import os
import asyncio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QMessageBox, QFileDialog, QToolBar, QStatusBar
)
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QKeySequence, QAction
from PyQt6.QtCore import Qt, QSize

from utils.config_manager import ConfigManager
from utils.data_manager import NovelDataManager
from utils.prompt_manager import PromptManager
from utils.async_utils import AsyncHelper, ProgressIndicator
from models.gpt_model import GPTModel
from models.claude_model import ClaudeModel
from models.gemini_model import GeminiModel
from models.custom_openai_model import CustomOpenAIModel
from models.modelscope_model import ModelScopeModel

from ui.components import ThemeManager, StatusBarManager, KeyboardShortcutManager
from ui.outline_tab import OutlineTab
from ui.outline_edit_tab import OutlineEditTab
from ui.chapter_outline_tab import ChapterOutlineTab
from ui.chapter_tab import ChapterTab
from ui.character_tab import CharacterTab
from ui.chapter_analysis_tab import ChapterAnalysisTab
from ui.statistics_tab import StatisticsTab
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("AI小说生成器")
        self.resize(1200, 800)

        # 加载配置
        self.config_manager = ConfigManager()

        # 创建数据管理器
        self.data_manager = NovelDataManager(cache_enabled=True)

        # 创建提示词管理器
        self.prompt_manager = PromptManager()

        # 创建异步助手
        self.async_helper = AsyncHelper(self)

        # 创建进度指示器
        self.progress_indicator = ProgressIndicator(self)

        # 加载字体
        self._load_font()

        # 初始化UI
        self._init_ui()

        # 初始化AI模型
        self._init_models()

        # 创建主题管理器
        self.theme_manager = ThemeManager(QApplication.instance())

        # 创建状态栏管理器
        self.status_bar_manager = StatusBarManager(self.statusBar())

        # 创建键盘快捷键管理器
        self.shortcut_manager = KeyboardShortcutManager(self)

        # 显示欢迎消息
        self.status_bar_manager.show_message("欢迎使用AI小说生成器")

    def _load_font(self):
        """加载字体"""
        font_path = "SourceHanSansCN-Normal.otf"
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.font = QFont(font_family, 10)
                QApplication.setFont(self.font)
            else:
                print("无法加载字体文件")
        else:
            print(f"字体文件不存在: {font_path}")

    def _init_ui(self):
        """初始化UI"""
        # 创建状态栏
        self.setStatusBar(QStatusBar())

        # 创建工具栏
        self._create_toolbar()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建各个标签页
        self.outline_tab = OutlineTab(self)
        self.outline_edit_tab = OutlineEditTab(self)
        self.chapter_outline_tab = ChapterOutlineTab(self)
        self.chapter_tab = ChapterTab(self)
        self.character_tab = CharacterTab(self)
        self.chapter_analysis_tab = ChapterAnalysisTab(self)
        self.statistics_tab = StatisticsTab(self)
        self.settings_tab = SettingsTab(self)

        # 添加标签页
        self.tab_widget.addTab(self.outline_tab, "大纲生成")
        self.tab_widget.addTab(self.outline_edit_tab, "总大纲编辑")
        self.tab_widget.addTab(self.chapter_outline_tab, "章节大纲编辑")
        self.tab_widget.addTab(self.chapter_tab, "章节生成")
        self.tab_widget.addTab(self.character_tab, "人物编辑")
        self.tab_widget.addTab(self.chapter_analysis_tab, "章节分析")
        self.tab_widget.addTab(self.statistics_tab, "统计信息")
        self.tab_widget.addTab(self.settings_tab, "设置")

    def _init_models(self):
        """初始化AI模型"""
        try:
            self.gpt_model = GPTModel(self.config_manager)
            self.has_gpt = True
        except Exception as e:
            self.has_gpt = False
            print(f"GPT模型初始化失败: {e}")

        try:
            self.claude_model = ClaudeModel(self.config_manager)
            self.has_claude = True
        except Exception as e:
            self.has_claude = False
            print(f"Claude模型初始化失败: {e}")

        try:
            self.gemini_model = GeminiModel(self.config_manager)
            self.has_gemini = True
        except Exception as e:
            self.has_gemini = False
            print(f"Gemini模型初始化失败: {e}")

        # 初始化自定义OpenAI兼容API
        self.has_custom_openai = False
        if self.config_manager.is_custom_openai_enabled():
            try:
                self.custom_openai_model = CustomOpenAIModel(self.config_manager)
                self.has_custom_openai = True
            except Exception as e:
                print(f"自定义OpenAI模型初始化失败: {e}")

        # 初始化ModelScope API
        self.has_modelscope = False
        if self.config_manager.is_modelscope_enabled():
            try:
                self.modelscope_model = ModelScopeModel(self.config_manager)
                self.has_modelscope = True
            except Exception as e:
                print(f"ModelScope模型初始化失败: {e}")

        # 检查是否至少有一个模型可用
        if not any([self.has_gpt, self.has_claude, self.has_gemini, self.has_custom_openai, self.has_modelscope]):
            QMessageBox.warning(
                self,
                "模型初始化失败",
                "所有AI模型初始化失败，请检查API密钥和网络连接。"
            )

    def get_model(self, model_type):
        """获取指定类型的模型"""
        if model_type == "gpt" and self.has_gpt:
            return self.gpt_model
        elif model_type == "claude" and self.has_claude:
            return self.claude_model
        elif model_type == "gemini" and self.has_gemini:
            return self.gemini_model
        elif model_type == "custom_openai" and self.has_custom_openai:
            return self.custom_openai_model
        elif model_type == "modelscope" and self.has_modelscope:
            return self.modelscope_model
        else:
            # 返回第一个可用的模型
            if self.has_gpt:
                return self.gpt_model
            elif self.has_claude:
                return self.claude_model
            elif self.has_gemini:
                return self.gemini_model
            elif self.has_custom_openai:
                return self.custom_openai_model
            elif self.has_modelscope:
                return self.modelscope_model
            else:
                raise ValueError("没有可用的AI模型")

    def _create_toolbar(self):
        """创建工具栏"""
        # 创建主工具栏
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 文件操作
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_novel)
        toolbar.addAction(new_action)

        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.load_novel)
        toolbar.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_novel)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 统计
        stats_action = QAction("统计信息", self)
        stats_action.setShortcut(QKeySequence("Ctrl+I"))
        stats_action.triggered.connect(self.show_statistics)
        toolbar.addAction(stats_action)

        # 主题切换
        theme_action = QAction("切换主题", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

        # 帮助
        help_action = QAction("帮助", self)
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

    def toggle_theme(self):
        """切换主题"""
        self.theme_manager.toggle_theme()

        # 更新状态栏消息
        theme_name = "深色" if self.theme_manager.current_theme == ThemeManager.DARK_THEME else "明亮"
        self.status_bar_manager.show_message(f"已切换到{theme_name}主题")

    def show_statistics(self):
        """显示统计信息"""
        # 检查是否有大纲
        if not self.data_manager.get_outline():
            QMessageBox.warning(self, "统计失败", "没有可统计的内容")
            return

        # 切换到统计标签页
        self.tab_widget.setCurrentWidget(self.statistics_tab)

        # 更新统计信息
        self.statistics_tab.update_statistics()

    def show_help(self):
        """显示帮助"""
        # 显示快捷键列表
        shortcut_descriptions = self.shortcut_manager.get_shortcut_descriptions()
        shortcut_text = "\n".join(shortcut_descriptions)

        QMessageBox.information(
            self,
            "快捷键帮助",
            f"可用的快捷键:\n\n{shortcut_text}"
        )

    def new_novel(self):
        """新建小说"""
        # 检查是否有未保存的更改
        if self.data_manager.is_modified():
            reply = QMessageBox.question(
                self,
                "确认新建",
                "当前有未保存的更改，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # 清空数据
        self.data_manager.clear()

        # 更新UI
        self.set_outline(None)

        # 更新状态栏
        self.status_bar_manager.show_message("已创建新小说")

    def set_outline(self, outline):
        """设置小说大纲"""
        self.data_manager.set_outline(outline)
        # 更新各个标签页
        self.outline_edit_tab.update_outline()
        self.chapter_outline_tab.update_outline()
        self.chapter_tab.update_outline(outline)
        # 更新人物编辑标签页
        self.character_tab.update_characters()
        # 更新章节分析标签页
        self.chapter_analysis_tab.set_outline(outline)
        # 更新统计标签页
        self.statistics_tab.update_statistics()

    def get_outline(self):
        """获取小说大纲"""
        return self.data_manager.get_outline()

    def set_chapter(self, volume_index, chapter_index, content):
        """设置章节内容"""
        self.data_manager.set_chapter(volume_index, chapter_index, content)

    def get_chapter(self, volume_index, chapter_index):
        """获取章节内容"""
        return self.data_manager.get_chapter(volume_index, chapter_index)

    def save_novel(self):
        """保存小说"""
        # 显示进度指示器
        self.progress_indicator.start()
        self.status_bar_manager.show_message("正在保存小说...")

        # 检查是否有大纲
        if not self.data_manager.get_outline():
            self.progress_indicator.stop()
            QMessageBox.warning(self, "保存失败", "没有可保存的大纲数据")
            return

        # 选择保存文件
        filepath, _ = QFileDialog.getSaveFileName(self, "保存小说", "", "AI小说文件 (*.ainovel)")
        if not filepath:
            self.progress_indicator.stop()
            return

        # 如果文件名没有.ainovel后缀，添加后缀
        if not filepath.endswith('.ainovel'):
            filepath += '.ainovel'

        # 保存小说数据
        success = self.data_manager.save_to_file(filepath)

        # 停止进度指示器
        self.progress_indicator.stop()

        if success:
            self.status_bar_manager.show_message(f"小说已保存到: {filepath}")
            QMessageBox.information(self, "保存成功", f"小说已保存到: {filepath}")
        else:
            self.status_bar_manager.show_message("保存失败")
            QMessageBox.warning(self, "保存失败", "保存小说时出错")

    def load_novel(self):
        """加载小说"""
        # 检查是否有未保存的更改
        if self.data_manager.is_modified():
            reply = QMessageBox.question(
                self,
                "确认加载",
                "当前有未保存的更改，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # 选择小说文件
        filepath, _ = QFileDialog.getOpenFileName(self, "选择小说文件", "", "AI小说文件 (*.ainovel);;JSON文件 (*.json)")
        if not filepath:
            return

        # 显示进度指示器
        self.progress_indicator.start()
        self.status_bar_manager.show_message("正在加载小说...")

        try:
            # 加载小说数据
            success = self.data_manager.load_from_file(filepath)

            # 停止进度指示器
            self.progress_indicator.stop()

            if success:
                # 更新UI
                outline = self.data_manager.get_outline()
                self.set_outline(outline)

                self.status_bar_manager.show_message(f"已加载小说: {filepath}")
                QMessageBox.information(self, "加载成功", "小说已加载")
            else:
                self.status_bar_manager.show_message("加载失败")
                QMessageBox.warning(self, "加载失败", "无法加载文件，格式可能不兼容")

        except Exception as e:
            # 停止进度指示器
            self.progress_indicator.stop()
            self.status_bar_manager.show_message("加载失败")
            QMessageBox.warning(self, "加载失败", f"加载小说时出错: {e}")

    def load_file(self, filepath):
        """加载指定文件

        Args:
            filepath: 文件路径
        """
        # 显示进度指示器
        self.progress_indicator.start()
        self.status_bar_manager.show_message(f"正在加载文件: {filepath}...")

        try:
            # 加载小说数据
            success = self.data_manager.load_from_file(filepath)

            # 停止进度指示器
            self.progress_indicator.stop()

            if success:
                # 更新UI
                outline = self.data_manager.get_outline()
                self.set_outline(outline)

                self.status_bar_manager.show_message(f"已加载小说: {filepath}")
            else:
                self.status_bar_manager.show_message("加载失败")
                QMessageBox.warning(self, "加载失败", "无法加载文件，格式可能不兼容")

        except Exception as e:
            # 停止进度指示器
            self.progress_indicator.stop()
            self.status_bar_manager.show_message("加载失败")
            QMessageBox.warning(self, "加载失败", f"加载文件时出错: {e}")


def run_app():
    """运行应用程序"""
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())
