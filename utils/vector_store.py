#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import faiss
import numpy as np
import pickle

class VectorStore:
    """向量数据库管理器"""

    def __init__(self, base_path="knowledge_bases"):
        """
        初始化向量数据库管理器

        Args:
            base_path: 知识库基础路径
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def create_index(self, kb_name, dimension):
        """
        创建索引

        Args:
            kb_name: 知识库名称
            dimension: 向量维度

        Returns:
            索引对象
        """
        index = faiss.IndexFlatL2(dimension)
        kb_path = os.path.join(self.base_path, kb_name)
        os.makedirs(kb_path, exist_ok=True)
        return index

    def save_index(self, kb_name, index, metadata):
        """
        保存索引

        Args:
            kb_name: 知识库名称
            index: 索引对象
            metadata: 元数据

        Returns:
            是否保存成功
        """
        try:
            kb_path = os.path.join(self.base_path, kb_name)
            os.makedirs(kb_path, exist_ok=True)

            # 保存索引
            faiss.write_index(index, os.path.join(kb_path, "index.faiss"))

            # 保存元数据
            with open(os.path.join(kb_path, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"保存索引出错: {e}")
            return False

    def load_index(self, kb_name):
        """
        加载索引

        Args:
            kb_name: 知识库名称

        Returns:
            (索引对象, 元数据)
        """
        try:
            kb_path = os.path.join(self.base_path, kb_name)

            # 加载索引
            index = faiss.read_index(os.path.join(kb_path, "index.faiss"))

            # 加载元数据
            with open(os.path.join(kb_path, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)

            return index, metadata
        except Exception as e:
            print(f"加载索引出错: {e}")
            return None, None

    def search(self, kb_name, query_vector, top_k=5):
        """
        搜索

        Args:
            kb_name: 知识库名称
            query_vector: 查询向量
            top_k: 返回结果数量

        Returns:
            (距离列表, ID列表)
        """
        try:
            index, metadata = self.load_index(kb_name)
            if index is None:
                return None, None

            # 确保查询向量是numpy数组并且形状正确
            query_vector = np.array(query_vector).reshape(1, -1).astype('float32')

            # 搜索
            distances, ids = index.search(query_vector, top_k)

            return distances[0], ids[0]
        except Exception as e:
            print(f"搜索出错: {e}")
            return None, None

    def get_document(self, kb_name, doc_id):
        """
        获取文档

        Args:
            kb_name: 知识库名称
            doc_id: 文档ID

        Returns:
            文档内容
        """
        try:
            _, metadata = self.load_index(kb_name)
            if metadata is None:
                return None

            return metadata["documents"].get(str(doc_id))
        except Exception as e:
            print(f"获取文档出错: {e}")
            return None

    def list_knowledge_bases(self):
        """
        列出所有知识库

        Returns:
            知识库列表
        """
        try:
            return [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]
        except Exception as e:
            print(f"列出知识库出错: {e}")
            return []

    def delete_knowledge_base(self, kb_name):
        """
        删除知识库

        Args:
            kb_name: 知识库名称

        Returns:
            是否删除成功
        """
        try:
            kb_path = os.path.join(self.base_path, kb_name)
            if os.path.exists(kb_path):
                for file in os.listdir(kb_path):
                    os.remove(os.path.join(kb_path, file))
                os.rmdir(kb_path)
                return True
            return False
        except Exception as e:
            print(f"删除知识库出错: {e}")
            return False
