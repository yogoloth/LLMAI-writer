#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI小说生成器

一个基于AI的小说生成工具，支持大纲生成和章节生成。
支持深色模式、提示词模板、异步处理和性能优化。
"""

import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from ui.main_window import MainWindow
from ui.components import ThemeManager

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AI小说生成器")
    parser.add_argument("--dark", action="store_true", help="启用深色模式")
    parser.add_argument("--file", type=str, help="要打开的小说文件路径")
    args = parser.parse_args()

    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()

    # 设置主题
    if args.dark:
        theme_manager = ThemeManager(app)
        theme_manager.set_theme(ThemeManager.DARK_THEME)

    # 显示窗口
    window.show()

    # 如果指定了文件，则打开它
    if args.file and os.path.exists(args.file):
        # 使用QTimer延迟加载，确保窗口已完全初始化
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, lambda: window.load_file(args.file))

    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
