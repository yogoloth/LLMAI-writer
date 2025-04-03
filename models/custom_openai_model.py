#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiohttp
import json
import asyncio
from models.ai_model import AIModel

class CustomOpenAIModel(AIModel):
    """自定义OpenAI兼容API模型实现"""

    def __init__(self, config_manager, model_config=None):
        """
        初始化自定义OpenAI兼容模型

        Args:
            config_manager: 配置管理器实例
            model_config: 可选的模型配置字典，如果提供则使用该配置，否则使用默认配置
        """
        super().__init__(config_manager)

        if model_config:
            # 使用提供的模型配置
            self.name = model_config.get('name', '自定义OpenAI模型')
            self.api_key = model_config.get('api_key', '')
            self.model_name = model_config.get('model_name', '')
            self.api_url = model_config.get('api_url', '')
        else:
            # 使用默认配置
            self.name = '自定义OpenAI'
            self.api_key = config_manager.get_api_key('custom_openai')
            self.model_name = config_manager.get_model_name('custom_openai')
            self.api_url = config_manager.get_config('CUSTOM_OPENAI', 'api_url', '')

        if not self.api_key:
            raise ValueError(f"模型 '{self.name}' 的API密钥未配置")

        if not self.model_name:
            raise ValueError(f"模型 '{self.name}' 的模型名称未配置")

        if not self.api_url:
            raise ValueError(f"模型 '{self.name}' 的API地址未配置")

    async def generate(self, prompt, callback=None):
        """
        生成文本（非流式）

        Args:
            prompt: 提示词
            callback: 回调函数，用于处理生成的文本块

        Returns:
            生成的文本
        """
        # 构建请求数据
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 设置代理
        proxy = None
        if self.proxy:
            proxy = self.proxy.get("https")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=data,
                    headers=headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status}, {error_text}")

                    result = await response.json()

                    # 解析响应
                    if "choices" in result and len(result["choices"]) > 0:
                        if "message" in result["choices"][0]:
                            return result["choices"][0]["message"]["content"]
                        elif "text" in result["choices"][0]:
                            return result["choices"][0]["text"]

                    # 如果无法解析，返回原始响应
                    return str(result)
        except Exception as e:
            raise Exception(f"生成文本时出错: {str(e)}")

    async def generate_stream(self, prompt, callback=None):
        """
        流式生成文本

        Args:
            prompt: 提示词
            callback: 回调函数，用于处理生成的文本块

        Returns:
            生成的文本流（异步生成器）
        """
        # 构建请求数据
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 设置代理
        proxy = None
        if self.proxy:
            proxy = self.proxy.get("https")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=data,
                    headers=headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status}, {error_text}")

                    # 处理流式响应
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            # 跳过空行和"data: [DONE]"
                            if line == "data: [DONE]":
                                continue

                            # 处理"data: "前缀
                            if line.startswith("data: "):
                                line = line[6:]

                            try:
                                data = json.loads(line)
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        chunk = choice["delta"]["content"]
                                    elif "text" in choice:
                                        chunk = choice["text"]
                                    else:
                                        continue

                                    if callback:
                                        callback(chunk)
                                    yield chunk
                            except json.JSONDecodeError:
                                # 忽略无法解析的行
                                continue
        except Exception as e:
            raise Exception(f"流式生成文本时出错: {str(e)}")
