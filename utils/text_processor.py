#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.document_processor import DocumentProcessor

class TextProcessor(DocumentProcessor):
    """文本文档处理器"""

    def process(self, file_path):
        """
        处理文本文档

        Args:
            file_path: 文档路径

        Returns:
            处理后的文本内容
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"处理文本文档出错: {e}")
            return None

    def get_supported_extensions(self):
        """
        获取支持的文件扩展名

        Returns:
            支持的文件扩展名列表
        """
        return [".txt", ".md", ".ainovel"]
