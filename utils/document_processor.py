#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

class DocumentProcessor(ABC):
    """文档处理器的抽象基类，定义了所有文档处理器需要实现的接口"""

    @abstractmethod
    def process(self, file_path):
        """
        处理文档

        Args:
            file_path: 文档路径

        Returns:
            处理后的文本内容
        """
        pass

    @abstractmethod
    def get_supported_extensions(self):
        """
        获取支持的文件扩展名

        Returns:
            支持的文件扩展名列表
        """
        pass
