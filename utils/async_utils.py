#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
async_utils.py —— Qt + asyncio 协同工具

功能一览
--------
1. 后台线程安全执行：同步函数 / async 协程 / async 生成器
2. 流式回调自动通过 progress_signal(str) 推送
3. 取消、异常、GC 友好处理
"""

import asyncio
import inspect
from typing import Callable, Coroutine, Any

from PyQt6.QtCore    import QThread, pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import QProgressDialog, QApplication


# =============================================================================
# AsyncHelper —— 主线程里的线程调度器
# =============================================================================
class AsyncHelper(QObject):
    finished = pyqtSignal(object)
    error    = pyqtSignal(Exception)
    progress = pyqtSignal(str)

    # ------------------------------------------------------------------ #
    def run_coroutine(self,
                      coro: Coroutine | Callable,
                      callback: Callable[[Any], None] | None = None,
                      error_callback: Callable[[Exception], None] | None = None):
        """
        把协程/函数交给 GenerationThread 执行，并在主线程回调结果。
        既可用位置，也可用关键字传 callback / error_callback。
        """
        thread = GenerationThread(coro)

        if callback:
            thread.finished_signal.connect(callback,
                                           Qt.ConnectionType.QueuedConnection)
        if error_callback:
            thread.error_signal.connect(
                lambda msg: error_callback(Exception(msg)),
                Qt.ConnectionType.QueuedConnection
            )

        # 保存引用，防止线程被 GC
        if not hasattr(self, "_threads"):
            self._threads: list[GenerationThread] = []
        self._threads.append(thread)

        thread.finished.connect(lambda: self._threads.remove(thread),
                                Qt.ConnectionType.QueuedConnection)
        thread.start()
        return thread

    # ------------------------------------------------------------------ #
    # ★ FIX：兼容旧接口 —— 允许 run_async(coro, cb, err)
    def run_async(self,
                  coro,
                  callback=None,
                  error_callback=None):
        """
        旧接口别名。支持：
            run_async(coro, on_done, on_error)        # 位置参数
            run_async(coro, callback=..., error_callback=...)  # 关键字
        """
        return self.run_coroutine(coro,
                                  callback=callback,
                                  error_callback=error_callback)


# =============================================================================
# GenerationThread —— 真正执行任务的后台线程
# =============================================================================
class GenerationThread(QThread):
    progress_signal = pyqtSignal(str)   # 与 @pyqtSlot(str) 兼容
    finished_signal = pyqtSignal(object)
    error_signal    = pyqtSignal(str)

    def __init__(self,
                 generator: Callable | Coroutine,
                 args: tuple = (),
                 kwargs: dict | None = None):
        """
        Parameters
        ----------
        generator : Callable | Coroutine
            普通同步函数、async 协程函数或已创建的协程对象
        args : tuple
            位置参数（向后兼容）
        kwargs : dict
            关键字参数
        """
        super().__init__()
        self.fn_or_coro = generator
        self.args       = args
        self.kwargs     = kwargs or {}

        self._is_coro_fn  = inspect.iscoroutinefunction(generator)
        self._is_coro_obj = asyncio.iscoroutine(generator)

        self._loop      = None
        self._cancelled = False

    # ------------------------------------------------------------------ #
    def run(self):
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            result = self._loop.run_until_complete(self._exec())

            if not self._cancelled:
                self.finished_signal.emit(result)

        except Exception as e:
            if not self._cancelled:
                self.error_signal.emit(str(e))

        finally:
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
                self._loop.close()

    # ------------------------------------------------------------------ #
    async def _exec(self):
        """统一处理返回值类型并分块推送进度。"""
        if self._is_coro_fn:
            result = await self.fn_or_coro(*self.args,
                                           **self.kwargs,
                                           **self._patch_callback())
        elif self._is_coro_obj:
            result = await self.fn_or_coro
        else:
            result = self.fn_or_coro(*self.args,
                                     **self.kwargs,
                                     **self._patch_callback())

        if asyncio.iscoroutine(result):          # 纯协程
            return await result

        if hasattr(result, "__aiter__"):         # async 生成器（流式）
            buf = ""
            async for chunk in result:
                if self._cancelled:
                    break
                text = str(chunk)
                buf += text
                self.progress_signal.emit(text)
            return buf

        return result                            # 普通同步返回

    # ------------------------------------------------------------------ #
    def _patch_callback(self) -> dict:
        """
        若目标函数接受 callback/on_progress/on_chunk 并且调用方没有显式提供，
        则注入回调，推送至 progress_signal。
        """
        # 调用方已显式提供 → 不再注入，避免重复
        if {"callback", "on_progress", "on_chunk"} & self.kwargs.keys():
            return {}

        cb_names = {"callback", "on_progress", "on_chunk"}
        try:
            sig = (inspect.signature(self.fn_or_coro)
                   if not self._is_coro_obj
                   else inspect.signature(type(self.fn_or_coro)))
            common = cb_names & sig.parameters.keys()
            if common:
                key = next(iter(common))
                return {key: lambda chunk: self.progress_signal.emit(str(chunk))}
        except (TypeError, ValueError):
            pass
        return {}

    # ------------------------------------------------------------------ #
    def cancel(self):
        """平滑取消线程。"""
        if not self.isRunning():
            return
        self._cancelled = True

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        self.quit()
        self.wait(5000)        # 最多等 5 秒


# =============================================================================
# ProgressIndicator —— 简易进度对话框
# =============================================================================
class ProgressIndicator(QObject):
    def __init__(self, parent=None, message="处理中..."):
        super().__init__(parent)
        self.parent  = parent
        self.message = message
        self.dialog  = None

    def start(self):
        if self.dialog:
            return
        self.dialog = QProgressDialog(self.message, "取消", 0, 0, self.parent)
        self.dialog.setWindowTitle("请稍候")
        self.dialog.setMinimumDuration(800)
        self.dialog.setAutoClose(True)
        self.dialog.setAutoReset(True)
        self.dialog.show()
        QApplication.processEvents()

    def update(self, *, value=None, maximum=None, message=None):
        if not self.dialog:
            return
        if maximum is not None:
            self.dialog.setMaximum(maximum)
        if value is not None:
            self.dialog.setValue(value)
        if message is not None:
            self.dialog.setLabelText(message)
        QApplication.processEvents()

    def stop(self):
        if self.dialog:
            self.dialog.close()
            self.dialog = None


# =============================================================================
# run_async —— 便捷入口
# =============================================================================
def run_async(coro,
              callback=None,
              error_callback=None):
    """
    临时创建 AsyncHelper 启动后台任务。
    位置 / 关键字均可：
        run_async(coro, done_cb, err_cb)
        run_async(coro, callback=done_cb, error_callback=err_cb)
    """
    return AsyncHelper().run_coroutine(coro,
                                       callback=callback,
                                       error_callback=error_callback)
