#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import asyncio
from utils.vector_store import VectorStore
from utils.document_processor import DocumentProcessor

class KnowledgeBaseManager:
    """知识库管理器"""

    def __init__(self, config_manager, embedding_model):
        """
        初始化知识库管理器

        Args:
            config_manager: 配置管理器实例
            embedding_model: 嵌入模型实例
        """
        self.config_manager = config_manager
        self.embedding_model = embedding_model
        self.vector_store = VectorStore()
        self.document_processors = {}  # 文档处理器字典，键为文件扩展名，值为处理器实例

    def register_processor(self, processor):
        """
        注册文档处理器

        Args:
            processor: 文档处理器实例
        """
        for ext in processor.get_supported_extensions():
            self.document_processors[ext] = processor

    async def create_knowledge_base(self, kb_name, documents, chunk_size=1000, chunk_overlap=200):
        """
        创建知识库

        Args:
            kb_name: 知识库名称
            documents: 文档路径列表
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小

        Returns:
            是否创建成功
        """
        try:
            # 处理文档
            all_chunks = []
            doc_metadata = {}

            for doc_path in documents:
                # 获取文件扩展名
                _, ext = os.path.splitext(doc_path)
                ext = ext.lower()

                # 获取处理器
                processor = self.document_processors.get(ext)
                if processor is None:
                    print(f"不支持的文件类型: {ext}")
                    continue

                # 处理文档
                text = processor.process(doc_path)
                if not text:
                    continue

                # 分块
                chunks = self._split_text(text, chunk_size, chunk_overlap)
                
                # 添加到列表
                start_idx = len(all_chunks)
                all_chunks.extend(chunks)
                end_idx = len(all_chunks)

                # 添加元数据
                doc_metadata[os.path.basename(doc_path)] = {
                    "path": doc_path,
                    "chunk_indices": list(range(start_idx, end_idx))
                }

            if not all_chunks:
                return False

            # 嵌入文本
            embeddings = await self.embedding_model.embed_batch(all_chunks)

            # 创建索引
            dimension = len(embeddings[0])
            index = self.vector_store.create_index(kb_name, dimension)

            # 添加向量
            import numpy as np
            vectors = np.array(embeddings).astype('float32')
            index.add(vectors)

            # 保存元数据
            metadata = {
                "documents": {str(i): chunk for i, chunk in enumerate(all_chunks)},
                "doc_metadata": doc_metadata,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "embedding_model": self.embedding_model.__class__.__name__
            }

            # 保存索引
            return self.vector_store.save_index(kb_name, index, metadata)

        except Exception as e:
            print(f"创建知识库出错: {e}")
            return False

    async def query(self, kb_name, query, top_k=5):
        """
        查询知识库

        Args:
            kb_name: 知识库名称
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            查询结果列表
        """
        try:
            # 嵌入查询文本
            query_embedding = await self.embedding_model.embed(query)

            # 搜索
            distances, ids = self.vector_store.search(kb_name, query_embedding, top_k)
            if distances is None or ids is None:
                return []

            # 获取结果
            results = []
            for i, doc_id in enumerate(ids):
                doc = self.vector_store.get_document(kb_name, doc_id)
                if doc:
                    results.append({
                        "id": int(doc_id),
                        "text": doc,
                        "score": float(distances[i])
                    })

            return results

        except Exception as e:
            print(f"查询知识库出错: {e}")
            return []

    def list_knowledge_bases(self):
        """
        列出所有知识库

        Returns:
            知识库列表
        """
        return self.vector_store.list_knowledge_bases()

    def delete_knowledge_base(self, kb_name):
        """
        删除知识库

        Args:
            kb_name: 知识库名称

        Returns:
            是否删除成功
        """
        return self.vector_store.delete_knowledge_base(kb_name)

    def _split_text(self, text, chunk_size, chunk_overlap):
        """
        分割文本

        Args:
            text: 文本
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小

        Returns:
            文本块列表
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap

        return chunks
