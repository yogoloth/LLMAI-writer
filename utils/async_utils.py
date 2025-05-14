#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
异步工具模块

提供异步操作相关的工具类和函数，用于改进UI响应性和异步处理。
"""

import asyncio
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QEventLoop
from PyQt6.QtWidgets import QProgressDialog, QApplication
from typing import Callable, Any, Optional, Dict, List, Union, Coroutine


class AsyncHelper(QObject):
    """
    AsyncHelper类用于在Qt应用中更好地集成asyncio

    提供了运行协程的方法，同时保持UI响应性
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loop = None
        self._running = False

    def run_coroutine(self, coro: Coroutine, show_progress: bool = False):
        """
        运行一个协程，并在完成时发出信号

        Args:
            coro: 要运行的协程
            show_progress: 是否显示进度对话框
        """
        if self._running:
            raise RuntimeError("已经有一个协程在运行")

        self._running = True

        # 创建事件循环
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # 进度对话框
        progress_dialog = None
        if show_progress:
            progress_dialog = QProgressDialog("处理中...", "取消", 0, 0, self.parent())
            progress_dialog.setWindowTitle("请稍候")
            progress_dialog.setMinimumDuration(500)  # 500ms后显示
            progress_dialog.setAutoClose(True)
            progress_dialog.setAutoReset(True)
            progress_dialog.setValue(0)
            progress_dialog.show()

            # 连接取消信号
            progress_dialog.canceled.connect(self._cancel_coroutine)

            # 连接进度信号
            self.progress.connect(progress_dialog.setValue)

        # 创建任务
        task = self._loop.create_task(coro)

        # 设置回调
        task.add_done_callback(self._on_task_done)

        # 创建定时器以保持事件循环运行
        timer = QTimer(self)
        timer.timeout.connect(lambda: self._process_events())
        timer.start(10)  # 每10ms处理一次事件

        # 运行事件循环
        self._loop.run_forever()

        # 清理
        timer.stop()
        if progress_dialog:
            progress_dialog.close()

        self._running = False

    def _process_events(self):
        """处理事件循环中的事件"""
        self._loop.call_soon(self._loop.stop)
        self._loop.run_forever()

    def _on_task_done(self, task):
        """任务完成回调"""
        try:
            result = task.result()
            self.finished.emit(result)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.error.emit(e)
        finally:
            self._loop.stop()

    def _cancel_coroutine(self):
        """取消正在运行的协程"""
        if self._loop and self._running:
            for task in asyncio.all_tasks(self._loop):
                task.cancel()

    def run_async(self, coro, callback=None, error_callback=None):
        """
        运行异步协程并处理回调

        Args:
            coro: 要运行的协程
            callback: 成功完成时的回调函数
            error_callback: 出错时的回调函数
        """
        # 创建一个线程来运行协程，避免事件循环冲突
        thread = GenerationThread(
            coro,  # 直接传递协程对象
            args=(),
            kwargs={}
        )

        # 保存线程引用，防止过早垃圾回收
        if not hasattr(self, '_threads'):
            self._threads = []
        self._threads.append(thread)

        # 连接信号
        if callback:
            thread.finished_signal.connect(callback)
        if error_callback:
            thread.error_signal.connect(lambda e: error_callback(Exception(e)))

        # 连接线程完成信号，清理线程引用
        thread.finished.connect(lambda: self._cleanup_thread(thread))

        # 启动线程
        thread.start()

        return thread

    def _cleanup_thread(self, thread):
        """
        清理已完成的线程

        Args:
            thread: 要清理的线程
        """
        if hasattr(self, '_threads') and thread in self._threads:
            self._threads.remove(thread)


class GenerationThread(QThread):
    """
    生成线程，用于在后台运行生成任务

    提供了统一的接口，用于处理AI生成任务
    """

    # 信号
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, generator_method: Callable, args: tuple = (), kwargs: dict = None):
        """
        初始化生成线程

        Args:
            generator_method: 生成方法，可以是一个协程函数或直接是一个协程对象
            args: 传递给生成方法的位置参数
            kwargs: 传递给生成方法的关键字参数
        """
        super().__init__()
        self.generator_method = generator_method
        self.args = args
        self.kwargs = kwargs or {}
        self._is_cancelled = False
        self._loop = None
        self._is_coroutine = asyncio.iscoroutine(generator_method)

    def __del__(self):
        """析构函数，确保线程正确清理"""
        self.cancel()
        self.wait()

    def run(self):
        """运行线程"""
        try:
            # 创建事件循环
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # 运行生成任务
            result = self._loop.run_until_complete(self._run_generator())

            # 发送完成信号
            if not self._is_cancelled:
                self.finished_signal.emit(result)

        except Exception as e:
            # 发送错误信号
            if not self._is_cancelled:
                self.error_signal.emit(str(e))
        finally:
            # 关闭事件循环
            if self._loop and self._loop.is_running():
                self._loop.stop()
            if self._loop and not self._loop.is_closed():
                self._loop.close()
            self._loop = None

    async def _run_generator(self):
        """运行生成器方法"""
        try:
            if self._is_coroutine:
                # 如果直接传入了协程对象，直接等待它
                return await self.generator_method
            else:
                # 运行生成器方法，不自动添加callback参数
                result = self.generator_method(*self.args, **self.kwargs)

                # 检查结果类型
                if asyncio.iscoroutine(result):
                    # 如果是协程，直接等待结果
                    return await result
                elif hasattr(result, '__aiter__'):
                    # 如果是异步生成器，迭代并收集结果
                    full_response = ""
                    async for chunk in result: # 迭代异步生成器获取数据块
                        if self._is_cancelled: # 检查是否被取消了，哼，想跑？没门！
                            break
                        full_response += chunk
                        self.progress_signal.emit(chunk) # 这里！实时发送进度信号！这样就能流式显示啦！🎉
                    return full_response
                else:
                    # 如果是普通值，直接返回
                    return result
        except Exception as e:
            print(f"运行生成器方法出错: {e}")
            raise

    def cancel(self):
        """取消生成任务"""
        if self.isRunning():
            self._is_cancelled = True

            # 取消事件循环中的所有任务
            if self._loop and not self._loop.is_closed():
                for task in asyncio.all_tasks(self._loop):
                    task.cancel()

                # 确保事件循环停止
                if self._loop.is_running():
                    self._loop.stop()

            # 等待线程结束，最多等待1秒
            if not self.wait(1000):
                # 如果线程没有在1秒内结束，强制终止
                self.terminate()
                # 等待线程真正结束
                self.wait()


class ProgressIndicator(QObject):
    """
    进度指示器，用于显示长时间操作的进度

    可以集成到UI中，提供视觉反馈
    """

    def __init__(self, parent=None, message="处理中..."):
        """
        初始化进度指示器

        Args:
            parent: 父窗口
            message: 显示的消息
        """
        super().__init__(parent)
        self.parent = parent
        self.message = message
        self.dialog = None

    def start(self):
        """开始显示进度指示器"""
        if self.dialog is None:
            self.dialog = QProgressDialog(self.message, "取消", 0, 0, self.parent)
            self.dialog.setWindowTitle("请稍候")
            self.dialog.setMinimumDuration(500)  # 500ms后显示
            self.dialog.setAutoClose(True)
            self.dialog.setAutoReset(True)
            self.dialog.setValue(0)
            self.dialog.show()

            # 处理事件，确保对话框显示
            QApplication.processEvents()

    def update(self, value=None, maximum=None, message=None):
        """
        更新进度指示器

        Args:
            value: 当前进度值
            maximum: 最大进度值
            message: 新的消息
        """
        if self.dialog:
            if maximum is not None:
                self.dialog.setMaximum(maximum)

            if value is not None:
                self.dialog.setValue(value)

            if message is not None:
                self.dialog.setLabelText(message)

            # 处理事件，确保对话框更新
            QApplication.processEvents()

    def stop(self):
        """停止显示进度指示器"""
        if self.dialog:
            self.dialog.close()
            self.dialog = None


def run_async(coro, callback=None, error_callback=None):
    """
    运行异步协程的便捷函数

    Args:
        coro: 要运行的协程
        callback: 完成时的回调函数
        error_callback: 出错时的回调函数

    Returns:
        QEventLoop: 事件循环对象，可用于等待协程完成
    """
    loop = QEventLoop()

    async def _run():
        try:
            result = await coro
            if callback:
                callback(result)
        except Exception as e:
            if error_callback:
                error_callback(e)
            else:
                raise
        finally:
            loop.quit()

    # 创建事件循环
    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)

    # 创建任务
    asyncio_loop.create_task(_run())

    # 创建定时器以保持事件循环运行
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(10)

    # 运行事件循环
    loop.exec()

    # 清理
    timer.stop()

    return loop
