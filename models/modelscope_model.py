#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from openai import OpenAI
from models.ai_model import AIModel

class ModelScopeModel(AIModel):
    """ModelScope模型实现，支持DeepSeek-R1等模型"""

    def __init__(self, config_manager):
        """
        初始化ModelScope模型
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)
        self.api_key = config_manager.get_api_key('modelscope')
        self.model_name = config_manager.get_model_name('modelscope')
        self.base_url = config_manager.get_config('MODELSCOPE', 'base_url', 'https://api-inference.modelscope.cn/v1/')
        
        if not self.api_key:
            raise ValueError("ModelScope API密钥未配置")
        
        if not self.model_name:
            self.model_name = "deepseek-ai/DeepSeek-R1"  # 默认使用DeepSeek-R1模型
            
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    async def generate(self, prompt, callback=None):
        """
        生成文本（非流式）
        
        Args:
            prompt: 提示词
            callback: 回调函数，用于处理生成的文本块
            
        Returns:
            生成的文本
        """
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            # 获取回答内容
            if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                return response.choices[0].message.content
            else:
                return str(response)
                
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
        try:
            # 使用to_thread将同步API调用转换为异步
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            # 处理流式响应
            done_reasoning = False
            for chunk in response:
                # 检查是否有reasoning_content
                reasoning_chunk = ""
                answer_chunk = ""
                
                if hasattr(chunk.choices[0].delta, 'reasoning_content'):
                    reasoning_chunk = chunk.choices[0].delta.reasoning_content or ""
                
                if hasattr(chunk.choices[0].delta, 'content'):
                    answer_chunk = chunk.choices[0].delta.content or ""
                
                # 优先处理reasoning_content
                if reasoning_chunk:
                    if callback:
                        callback(reasoning_chunk)
                    yield reasoning_chunk
                elif answer_chunk:
                    if not done_reasoning:
                        # 添加分隔符
                        separator = "\n\n === Final Answer ===\n\n"
                        if callback:
                            callback(separator)
                        yield separator
                        done_reasoning = True
                    
                    if callback:
                        callback(answer_chunk)
                    yield answer_chunk
                    
        except Exception as e:
            raise Exception(f"流式生成文本时出错: {str(e)}")
