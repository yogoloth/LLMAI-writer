#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

class EmbeddingModel(ABC):
    """嵌入模型的抽象基类，定义了所有嵌入模型需要实现的接口"""

    def __init__(self, config_manager):
        """
        初始化嵌入模型

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.proxy = config_manager.get_proxy_settings()

    @abstractmethod
    async def embed(self, text):
        """
        将文本转换为嵌入向量

        Args:
            text: 要嵌入的文本

        Returns:
            嵌入向量
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts):
        """
        批量将文本转换为嵌入向量

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        pass
