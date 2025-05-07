#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitz  # PyMuPDF
from utils.document_processor import DocumentProcessor

class PdfProcessor(DocumentProcessor):
    """PDF文档处理器"""

    def process(self, file_path):
        """
        处理PDF文档

        Args:
            file_path: 文档路径

        Returns:
            处理后的文本内容
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            print(f"处理PDF文档出错: {e}")
            return None

    def get_supported_extensions(self):
        """
        获取支持的文件扩展名

        Returns:
            支持的文件扩展名列表
        """
        return [".pdf"]
