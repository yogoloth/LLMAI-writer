#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from utils.document_processor import DocumentProcessor

class JsonProcessor(DocumentProcessor):
    """JSON文档处理器"""

    def process(self, file_path):
        """
        处理JSON文档

        Args:
            file_path: 文档路径

        Returns:
            处理后的文本内容
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 将JSON转换为文本
            if isinstance(data, dict):
                # 如果是字典，尝试提取有意义的字段
                text_parts = []
                for key, value in data.items():
                    if isinstance(value, str):
                        text_parts.append(f"{key}: {value}")
                    elif isinstance(value, (list, dict)):
                        text_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
                return "\n".join(text_parts)
            elif isinstance(data, list):
                # 如果是列表，尝试将每个元素转换为文本
                text_parts = []
                for item in data:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        item_parts = []
                        for key, value in item.items():
                            if isinstance(value, str):
                                item_parts.append(f"{key}: {value}")
                        if item_parts:
                            text_parts.append("\n".join(item_parts))
                    else:
                        text_parts.append(str(item))
                return "\n\n".join(text_parts)
            else:
                # 其他情况，直接转换为字符串
                return str(data)
        except Exception as e:
            print(f"处理JSON文档出错: {e}")
            return None

    def get_supported_extensions(self):
        """
        获取支持的文件扩展名

        Returns:
            支持的文件扩展名列表
        """
        return [".json"]
