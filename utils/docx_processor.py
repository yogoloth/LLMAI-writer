#!/usr/bin/env python
# -*- coding: utf-8 -*-

import docx
from utils.document_processor import DocumentProcessor

class DocxProcessor(DocumentProcessor):
    """DOCX文档处理器"""

    def process(self, file_path):
        """
        处理DOCX文档

        Args:
            file_path: 文档路径

        Returns:
            处理后的文本内容
        """
        try:
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"处理DOCX文档出错: {e}")
            return None

    def get_supported_extensions(self):
        """
        获取支持的文件扩展名

        Returns:
            支持的文件扩展名列表
        """
        return [".docx", ".doc"]
