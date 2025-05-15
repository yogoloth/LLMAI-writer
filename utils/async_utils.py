import asyncio
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QEventLoop, Qt
from PyQt6.QtWidgets import QProgressDialog, QApplication
from typing import Callable, Any, Optional, Dict, List, Union, Coroutine

class AsyncHelper(QObject):
    """
    AsyncHelper类用于在Qt应用中更好地集成asyncio

    提供了运行协程的方法，同时保持UI响应性
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int) # 这个信号在新的实现中可能不再使用，但保留以防万一

    def __init__(self, parent=None):
        super().__init__(parent)
        # 不需要在这里创建或管理事件循环和运行状态，交由 GenerationThread 处理

    def run_coroutine(self, coro: Coroutine, callback=None, error_callback=None):
        """
        运行一个协程，并在完成时发出信号 (已修改为在线程中运行)

        Args:
            coro: 要运行的协程
            callback: 完成时的回调函数
            error_callback: 出错时的回调函数

        Returns:
            GenerationThread: 运行协程的线程对象
        """
        # 使用 GenerationThread 在后台运行协程
        thread = GenerationThread(
            coro,  # 直接传递协程对象
            args=(),
            kwargs={}
        )

        # 连接信号
        if callback:
            # 使用 Qt.ConnectionType.QueuedConnection 确保信号在接收者线程处理
            thread.finished_signal.connect(callback, Qt.ConnectionType.QueuedConnection)
        if error_callback:
            # 使用 Qt.ConnectionType.QueuedConnection 确保信号在接收者线程处理
            thread.error_signal.connect(lambda e: error_callback(Exception(e)), Qt.ConnectionType.QueuedConnection)

        # 保存线程引用，防止过早垃圾回收
        if not hasattr(self, '_threads'):
            self._threads = []
        self._threads.append(thread)

        # 连接线程完成信号，清理线程引用
        # 使用 Qt.ConnectionType.QueuedConnection 确保清理操作在主线程进行
        thread.finished.connect(lambda: self._cleanup_thread(thread), Qt.ConnectionType.QueuedConnection)


        # 启动线程
        thread.start()

        return thread # 返回线程对象，调用者可以持有引用或等待其完成（如果需要）

    def _cleanup_thread(self, thread):
        """
        清理已完成的线程

        Args:
            thread: 要清理的线程
        """
        if hasattr(self, '_threads') and thread in self._threads:
            self._threads.remove(thread)

    # 移除了旧的 _loop, _running, _process_events, _on_task_done, _cancel_coroutine 方法


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
        # 判断传入的是协程函数还是协程对象
        self._is_coroutine_func = asyncio.iscoroutinefunction(generator_method)
        self._is_coroutine_obj = asyncio.iscoroutine(generator_method)


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
                # 将异常对象转换为字符串发送
                self.error_signal.emit(str(e))
        finally:
            # 关闭事件循环
            if self._loop and self._loop.is_running():
                self._loop.stop()
            if self._loop and not self._loop.is_closed():
                self._loop.close()
            self._loop = None # 清除引用

    async def _run_generator(self):
        """运行生成器方法"""
        try:
            if self._is_coroutine_func:
                # 如果是协程函数，调用它并等待结果
                result = await self.generator_method(*self.args, **self.kwargs)
            elif self._is_coroutine_obj:
                # 如果直接传入了协程对象，直接等待它
                result = await self.generator_method
            else:
                 # 如果是普通函数，直接调用
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
                    # 使用 Qt.ConnectionType.QueuedConnection 确保信号在主线程处理
                    self.progress_signal.emit(chunk) # 这里！实时发送进度信号！这样就能流式显示啦！🎉
                return full_response
            else:
                # 如果是普通值，直接返回
                return result
        except Exception as e:
            print(f"运行生成器方法出错: {e}")
            raise # 重新抛出异常，以便在 run 方法中捕获

    def cancel(self):
        """取消生成任务"""
        if self.isRunning():
            self._is_cancelled = True

            # 在事件循环中安排取消任务
            if self._loop and not self._loop.is_closed():
                 # 不能直接在非事件循环线程中取消任务，需要在事件循环线程中调用
                 self._loop.call_soon_threadsafe(self._cancel_all_tasks)

            # 等待线程结束，最多等待1秒
            if not self.wait(1000):
                # 如果线程没有在1秒内结束，强制终止
                self.terminate()
                # 等待线程真正结束
                self.wait()

    def _cancel_all_tasks(self):
        """取消事件循环中的所有任务 (在事件循环线程中调用)"""
        if self._loop and not self._loop.is_closed():
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
            # 停止事件循环
            if self._loop.is_running():
                self._loop.stop()


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
    运行异步协程的便捷函数 (已修改为在线程中运行，不阻塞主线程)

    Args:
        coro: 要运行的协程
        callback: 完成时的回调函数
        error_callback: 出错时的回调函数

    Returns:
        GenerationThread: 运行协程的线程对象
    """
    # 使用 GenerationThread 在后台运行协程
    thread = GenerationThread(
        coro,  # 直接传递协程对象
        args=(),
        kwargs={}
    )

    # 连接信号
    if callback:
        # 使用 Qt.ConnectionType.QueuedConnection 确保信号在接收者线程处理
        thread.finished_signal.connect(callback, Qt.ConnectionType.QueuedConnection)
    if error_callback:
        # 使用 Qt.ConnectionType.QueuedConnection 确保信号在接收者线程处理
        thread.error_signal.connect(lambda e: error_callback(Exception(e)), Qt.ConnectionType.QueuedConnection)

    # 启动线程
    thread.start()

    # 返回线程对象，调用者可以持有引用或等待其完成（如果需要）
    return thread
