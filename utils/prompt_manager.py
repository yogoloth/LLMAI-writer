#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示词管理模块

提供提示词模板管理和历史记录功能。
"""

import os
import json
import time
from typing import List, Dict, Any, Optional


class PromptTemplate:
    """提示词模板类"""
    
    def __init__(self, name: str, content: str, category: str = "general", 
                 description: str = "", created_at: float = None):
        """
        初始化提示词模板
        
        Args:
            name: 模板名称
            content: 模板内容
            category: 模板分类
            description: 模板描述
            created_at: 创建时间戳
        """
        self.name = name
        self.content = content
        self.category = category
        self.description = description
        self.created_at = created_at or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "name": self.name,
            "content": self.content,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """
        从字典创建模板
        
        Args:
            data: 字典数据
            
        Returns:
            PromptTemplate实例
        """
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            category=data.get("category", "general"),
            description=data.get("description", ""),
            created_at=data.get("created_at", time.time())
        )


class PromptHistory:
    """提示词历史记录类"""
    
    def __init__(self, prompt: str, model: str, result: str = "", 
                 timestamp: float = None, metadata: Dict[str, Any] = None):
        """
        初始化提示词历史记录
        
        Args:
            prompt: 提示词内容
            model: 使用的模型
            result: 生成结果
            timestamp: 时间戳
            metadata: 元数据
        """
        self.prompt = prompt
        self.model = model
        self.result = result
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "prompt": self.prompt,
            "model": self.model,
            "result": self.result,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptHistory':
        """
        从字典创建历史记录
        
        Args:
            data: 字典数据
            
        Returns:
            PromptHistory实例
        """
        return cls(
            prompt=data.get("prompt", ""),
            model=data.get("model", ""),
            result=data.get("result", ""),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )


class PromptManager:
    """提示词管理器类"""
    
    def __init__(self, templates_file: str = "prompt_templates.json", 
                 history_file: str = "prompt_history.json"):
        """
        初始化提示词管理器
        
        Args:
            templates_file: 模板文件路径
            history_file: 历史记录文件路径
        """
        self.templates_file = templates_file
        self.history_file = history_file
        self.templates: Dict[str, PromptTemplate] = {}
        self.history: List[PromptHistory] = []
        self.max_history = 100  # 最大历史记录数
        
        # 加载数据
        self._load_templates()
        self._load_history()
        
        # 如果没有模板，创建默认模板
        if not self.templates:
            self._create_default_templates()
    
    def _load_templates(self):
        """加载模板"""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for template_data in data:
                        template = PromptTemplate.from_dict(template_data)
                        self.templates[template.name] = template
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载模板文件出错: {e}")
    
    def _load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for history_data in data:
                        history = PromptHistory.from_dict(history_data)
                        self.history.append(history)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载历史记录文件出错: {e}")
    
    def _save_templates(self):
        """保存模板"""
        try:
            with open(self.templates_file, "w", encoding="utf-8") as f:
                data = [template.to_dict() for template in self.templates.values()]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存模板文件出错: {e}")
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                data = [history.to_dict() for history in self.history]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存历史记录文件出错: {e}")
    
    def _create_default_templates(self):
        """创建默认模板"""
        # 大纲生成模板
        self.add_template(
            name="标准大纲模板",
            content="请为我创建一部小说的详细大纲，包括以下内容：\n\n1. 小说标题\n2. 核心主题\n3. 主要人物（包括姓名、身份、性格特点和背景故事）\n4. 故事梗概\n5. 分卷结构（每卷包含标题、简介和具体章节）\n6. 世界观设定\n\n请确保大纲结构完整、逻辑合理，并以JSON格式返回。",
            category="outline",
            description="标准的小说大纲生成模板"
        )
        
        # 章节生成模板
        self.add_template(
            name="标准章节模板",
            content="请根据以下信息，为我创作一个完整、连贯、生动的章节内容：\n\n小说标题：{title}\n核心主题：{theme}\n世界观设定：{worldbuilding}\n\n当前卷：{volume_title}\n卷简介：{volume_description}\n\n当前章节：{chapter_title}\n章节摘要：{chapter_summary}\n\n请确保内容：\n1. 符合章节摘要的描述\n2. 与前后章节保持连贯\n3. 展现人物性格和发展\n4. 符合小说的整体风格和主题\n5. 包含丰富的对话、描写和情节发展",
            category="chapter",
            description="标准的章节生成模板"
        )
        
        # 人物生成模板
        self.add_template(
            name="标准人物模板",
            content="请为我生成一个详细的角色设定，角色类型为{character_type}。\n\n请以JSON格式返回角色设定，包含以下字段:\n- name: 角色姓名\n- identity: 角色身份\n- age: 角色年龄\n- gender: 角色性别\n- personality: 性格特点（详细描述）\n- background: 背景故事（详细描述）\n- appearance: 外貌描述（详细描述）\n- abilities: 能力特长（详细描述）\n- goals: 目标动机（详细描述）\n\n请确保生成的角色设定丰富、合理、有深度，并且符合角色类型的特点。",
            category="character",
            description="标准的人物生成模板"
        )
        
        # 创意优化模板
        self.add_template(
            name="创意优化模板",
            content="请分析以下内容，并提供创意优化建议：\n\n{content}\n\n请从以下几个方面提供具体的优化建议：\n1. 创意性和独特性\n2. 情节发展和转折\n3. 人物塑造和互动\n4. 世界观构建\n5. 语言风格和表达\n\n对于每个方面，请提供具体的改进建议和示例。",
            category="improvement",
            description="内容创意优化建议模板"
        )
        
        # 保存默认模板
        self._save_templates()
    
    def add_template(self, name: str, content: str, category: str = "general", 
                    description: str = "") -> bool:
        """
        添加模板
        
        Args:
            name: 模板名称
            content: 模板内容
            category: 模板分类
            description: 模板描述
            
        Returns:
            是否添加成功
        """
        if name in self.templates:
            return False
        
        template = PromptTemplate(name, content, category, description)
        self.templates[name] = template
        self._save_templates()
        return True
    
    def update_template(self, name: str, content: str = None, category: str = None, 
                       description: str = None) -> bool:
        """
        更新模板
        
        Args:
            name: 模板名称
            content: 新的模板内容
            category: 新的模板分类
            description: 新的模板描述
            
        Returns:
            是否更新成功
        """
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        
        if content is not None:
            template.content = content
        
        if category is not None:
            template.category = category
        
        if description is not None:
            template.description = description
        
        self._save_templates()
        return True
    
    def delete_template(self, name: str) -> bool:
        """
        删除模板
        
        Args:
            name: 模板名称
            
        Returns:
            是否删除成功
        """
        if name not in self.templates:
            return False
        
        del self.templates[name]
        self._save_templates()
        return True
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板实例，如果不存在则返回None
        """
        return self.templates.get(name)
    
    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """
        获取指定分类的所有模板
        
        Args:
            category: 模板分类
            
        Returns:
            模板列表
        """
        return [t for t in self.templates.values() if t.category == category]
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """
        获取所有模板
        
        Returns:
            所有模板的列表
        """
        return list(self.templates.values())
    
    def add_history(self, prompt: str, model: str, result: str = "", 
                   metadata: Dict[str, Any] = None) -> None:
        """
        添加历史记录
        
        Args:
            prompt: 提示词内容
            model: 使用的模型
            result: 生成结果
            metadata: 元数据
        """
        history = PromptHistory(prompt, model, result, metadata=metadata)
        self.history.append(history)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        self._save_history()
    
    def get_history(self, limit: int = None, offset: int = 0) -> List[PromptHistory]:
        """
        获取历史记录
        
        Args:
            limit: 限制返回的记录数
            offset: 起始偏移量
            
        Returns:
            历史记录列表
        """
        if limit is None:
            return self.history[offset:]
        else:
            return self.history[offset:offset+limit]
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.history = []
        self._save_history()
    
    def get_prompt_suggestions(self, current_prompt: str) -> List[str]:
        """
        获取提示词建议
        
        基于当前输入的提示词和历史记录，提供改进建议
        
        Args:
            current_prompt: 当前提示词
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 基于长度的建议
        if len(current_prompt) < 50:
            suggestions.append("提示词过短，考虑添加更多细节和要求")
        
        # 基于关键词的建议
        if "请" not in current_prompt and "生成" not in current_prompt:
            suggestions.append("考虑使用礼貌用语，如'请生成...'")
        
        if "要求" not in current_prompt and "需求" not in current_prompt:
            suggestions.append("考虑明确指出具体要求，如'要求：1. ... 2. ...'")
        
        # 基于历史记录的建议
        successful_prompts = [h for h in self.history if h.result and len(h.result) > 100]
        if successful_prompts:
            # 找出最成功的提示词（简单地以结果长度作为衡量标准）
            best_prompt = max(successful_prompts, key=lambda h: len(h.result))
            suggestions.append(f"参考历史成功提示词: '{best_prompt.prompt[:50]}...'")
        
        return suggestions
