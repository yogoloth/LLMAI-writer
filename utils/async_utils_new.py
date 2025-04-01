#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
异步工具模块（优化版）

提供异步操作相关的工具类和函数，使用 asyncqt 库简化异步处理。
"""

import asyncio
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QProgressDialog, QApplication
from qasync import QEventLoop, asyncSlot
from typing import Callable, Any, Optional, Dict, List, Union, Coroutine


class AsyncHelper(QObject):
    """
    AsyncHelper类用于在Qt应用中更好地集成asyncio
    
    使用 qasync 库简化异步处理
    """
    
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        初始化异步助手
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.loop = QEventLoop(parent)
        self._running = False
    
    @asyncSlot()
    async def run_coroutine(self, coro: Coroutine, show_progress: bool = False):
        """
        运行一个协程，并在完成时发出信号
        
        Args:
            coro: 要运行的协程
            show_progress: 是否显示进度对话框
        """
        if self._running:
            raise RuntimeError("已经有一个协程在运行")
        
        self._running = True
        
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
        
        try:
            # 运行协程
            result = await coro
            self.finished.emit(result)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.error.emit(e)
        finally:
            if progress_dialog:
                progress_dialog.close()
            self._running = False
    
    def _cancel_coroutine(self):
        """取消正在运行的协程"""
        if self._running:
            asyncio.create_task(self._do_cancel())
    
    async def _do_cancel(self):
        """执行取消操作"""
        for task in asyncio.all_tasks():
            if task != asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


class GenerationThread(QObject):
    """
    生成任务，用于在后台运行生成任务
    
    使用 asyncio 和 qasync 简化异步处理
    """
    
    # 信号
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    
    def __init__(self, generator_method: Callable, args: tuple = (), kwargs: dict = None):
        """
        初始化生成任务
        
        Args:
            generator_method: 生成方法，必须是一个协程函数
            args: 传递给生成方法的位置参数
            kwargs: 传递给生成方法的关键字参数
        """
        super().__init__()
        self.generator_method = generator_method
        self.args = args
        self.kwargs = kwargs or {}
        self._is_cancelled = False
        self.task = None
    
    @asyncSlot()
    async def start(self):
        """启动生成任务"""
        try:
            # 添加回调函数，只发送进度信号，不调用原始回调
            self.kwargs['callback'] = lambda chunk: self.progress_signal.emit(chunk)
            
            # 运行生成器方法
            result = self.generator_method(*self.args, **self.kwargs)
            
            # 检查结果类型
            if asyncio.iscoroutine(result):
                # 如果是协程，直接等待结果
                self.task = asyncio.create_task(result)
                result = await self.task
                if not self._is_cancelled:
                    self.finished_signal.emit(result)
            elif hasattr(result, '__aiter__'):
                # 如果是异步生成器，迭代并收集结果
                full_response = ""
                async for chunk in result:
                    full_response += chunk
                    if self._is_cancelled:
                        break
                if not self._is_cancelled:
                    self.finished_signal.emit(full_response)
            else:
                # 如果是普通值，直接返回
                if not self._is_cancelled:
                    self.finished_signal.emit(result)
        
        except Exception as e:
            # 发送错误信号
            if not self._is_cancelled:
                self.error_signal.emit(str(e))
    
    def cancel(self):
        """取消生成任务"""
        self._is_cancelled = True
        if self.task and not self.task.done():
            self.task.cancel()


class ProgressIndicator(QObject):
    """
    进度指示器
    
    在状态栏显示进度指示器
    """
    
    def __init__(self, parent=None):
        """
        初始化进度指示器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_indicator)
        self.indicator_state = 0
        self.indicators = ["|", "/", "-", "\\"]
        self.parent = parent
    
    def start(self):
        """启动进度指示器"""
        self.timer.start(100)
    
    def stop(self):
        """停止进度指示器"""
        self.timer.stop()
        if hasattr(self.parent, "status_bar_manager"):
            status_text = self.parent.status_bar_manager.status_label.text()
            if status_text.endswith(tuple(self.indicators)):
                self.parent.status_bar_manager.status_label.setText(status_text[:-1])
    
    def _update_indicator(self):
        """更新进度指示器"""
        if hasattr(self.parent, "status_bar_manager"):
            status_text = self.parent.status_bar_manager.status_label.text()
            if status_text.endswith(tuple(self.indicators)):
                status_text = status_text[:-1]
            status_text += self.indicators[self.indicator_state]
            self.parent.status_bar_manager.status_label.setText(status_text)
            self.indicator_state = (self.indicator_state + 1) % len(self.indicators)


@asyncSlot()
async def run_async(coro, callback=None, error_callback=None):
    """
    运行异步协程的便捷函数
    
    Args:
        coro: 要运行的协程
        callback: 完成时的回调函数
        error_callback: 出错时的回调函数
    """
    try:
        result = await coro
        if callback:
            callback(result)
    except Exception as e:
        if error_callback:
            error_callback(e)
        else:
            raise
