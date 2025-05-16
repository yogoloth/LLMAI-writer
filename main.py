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
import asyncio
import traceback # 导入 traceback 模块，这可是抓 Bug 的神器！
import logging # 导入 logging 模块，日志记录也要跟上！
from PyQt6.QtWidgets import QApplication, QMessageBox # 导入 QMessageBox，万一闪退了还能给用户个交代
from PyQt6.QtGui import QFont, QFontDatabase
from qasync import QEventLoop, QApplication as QAsyncApplication
from ui.main_window import MainWindow
from ui.components import ThemeManager
from ui.styles import get_style
from ui.app_icon import set_app_icon

# 配置日志记录器，最起码得把闪退信息记下来！
LOG_FILENAME = 'crash_report.log'
logging.basicConfig(
    level=logging.INFO, # 先用 INFO 级别，以后可以按需调整
    format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'), # 写入到文件，中文可别乱码了！
        logging.StreamHandler(sys.stdout) # 顺便在控制台也打一份，双保险！
    ]
)

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    全局异常处理函数。哼，看你往哪里逃！
    """
    # 格式化异常信息，务必把调用栈也打出来，不然怎么知道是哪里出了问题！
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # 打印到控制台，让开发者也看看！
    print("哎呀呀，程序好像被玩坏了！😱 详细错误信息如下：")
    print(error_message)
    
    # 写入到日志文件，这可是铁证如山！
    logging.error("捕获到未处理的全局异常 (Unhandled Exception Caught):\n%s", error_message)
    
    # （可选）尝试显示一个错误对话框，不过得小心别在这里又崩了！
    try:
        # 确保在主线程中调用UI元素，或者使用信号槽机制
        # 这里简单处理，如果 QApplication 实例存在，就尝试弹窗
        if QApplication.instance():
            # 为了避免再次触发 Qt 错误，这里用最简单的方式弹窗
            # 注意：如果主事件循环已经停止，这个可能不会显示，或者行为异常
            # QMessageBox.critical(None, "程序崩溃啦！", f"发生了一个无法处理的错误，程序即将关闭。\n详细信息已记录到 {LOG_FILENAME}\n\n错误详情：\n{error_message[:1000]}...") # 只显示一部分错误信息，免得弹窗太大
            # 更稳妥的方式是记录日志后直接退出，或者尝试一个更简单的文本提示
            print(f"严重错误！详细信息已记录到 {LOG_FILENAME}。程序可能需要关闭。")
        else:
            print(f"QApplication 实例不存在，无法显示错误对话框。错误已记录到 {LOG_FILENAME}。")

    except Exception as e:
        # 中文日志：连错误处理函数都崩了？这可真是没救了！
        logging.error("在 handle_exception 函数内部处理 QMessageBox 时发生异常: %s", str(e))
        print(f"在显示错误对话框时也发生了错误: {e}。错误已记录到 {LOG_FILENAME}。")

    # 最好是记录完日志后，让程序优雅地退出，或者至少尝试一下
    # sys.exit(1) # 这一行可能会导致某些情况下日志未完全写入，所以先注释掉


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AI小说生成器")
    parser.add_argument("--dark", action="store_true", help="启用深色模式")
    parser.add_argument("--file", type=str, help="要打开的小说文件路径")
    args = parser.parse_args()

    # 创建应用程序
    app = QAsyncApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 应用默认样式表
    app.setStyleSheet(get_style("light"))

    # 设置应用程序图标
    set_app_icon(app)

    # 创建事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

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
    with loop:
        return loop.run_forever()

if __name__ == "__main__":
    # 在应用程序主逻辑开始之前，设置全局异常钩子！这可是关键一步！
    sys.excepthook = handle_exception
    logging.info("全局异常钩子 sys.excepthook 已设置。") # 确认一下钩子挂上了！

    try: # 把主逻辑也包起来，万一这里面就崩了呢！
        asyncio.run(main())
    except Exception as e: # 捕获主事件循环启动前的其他潜在错误
        logging.critical("在 asyncio.run(main()) 执行期间捕获到未处理的异常: %s", str(e), exc_info=True)
        # 调用我们的异常处理器，确保所有信息都被记录
        handle_exception(type(e), e, e.__traceback__)
        sys.exit(1) # 确保程序在严重错误后退出
