#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiohttp
import json
import asyncio
from embedding_models.embedding_model import EmbeddingModel

class SiliconFlowEmbedding(EmbeddingModel):
    """SiliconFlow嵌入模型实现"""

    def __init__(self, config_manager):
        """
        初始化SiliconFlow嵌入模型

        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)
        self.api_key = config_manager.get_api_key('siliconflow')
        self.model_name = config_manager.get_embedding_model_name('siliconflow')
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"

        if not self.api_key:
            raise ValueError("SiliconFlow API密钥未配置")

        if not self.model_name:
            self.model_name = "BAAI/bge-m3"  # 默认模型

    async def embed(self, text):
        """
        将文本转换为嵌入向量

        Args:
            text: 要嵌入的文本

        Returns:
            嵌入向量
        """
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts):
        """
        批量将文本转换为嵌入向量

        Args:
            texts: 要嵌入的文本列表

        Returns:
            嵌入向量列表
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model_name,
            "input": texts
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data, proxy=self.proxy.get("https") if self.proxy else None) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API请求失败: {response.status}, {error_text}")

                result = await response.json()
                return [item["embedding"] for item in result["data"]]
