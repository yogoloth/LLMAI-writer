# LLMAI-writer

LLMAI-writer是一个基于大型语言模型的小说生成工具，支持大纲生成、章节生成和人物设计等功能。

## 功能特点

- **大纲生成**：根据用户输入的主题、风格和结构要求，自动生成完整的小说大纲
- **章节生成**：基于大纲内容，生成详细的章节内容
- **人物设计**：创建和管理小说中的角色
- **大纲编辑**：提供总大纲编辑和章节大纲编辑功能
- **多模型支持**：支持GPT、Claude、Gemini、ModelScope的DeepSeek-R1模型以及自定义OpenAI兼容API
- **深色模式**：支持明亮和深色两种界面主题
- **提示词模板**：内置多种提示词模板，也可自定义模板

## 安装说明

1. 克隆仓库：
   ```
   git clone https://github.com/WhatRUHuh/LLMAI-writer.git
   cd LLMAI-writer
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

   > **注意事项：** requirements.txt 文件由克劳德先生总结生成，如果安装过程中遇到问题，可以尝试删除文件中的版本号限制（即删除每行中的 `==x.x.x` 部分），或者手动安装主要依赖：PyQt6、openai、anthropic、google-generativeai 等。

3. 配置API密钥：
   - 复制`config.example.ini`为`config.ini`
   - 编辑`config.ini`，填入你的API密钥

## 使用方法

1. 运行程序：
   ```
   python main.py
   ```

2. 大纲生成：
   - 在"大纲生成"标签页中填写小说的基本信息
   - 选择AI模型
   - 点击"生成大纲"按钮

3. 编辑大纲：
   - 在"总大纲编辑"标签页中编辑标题、主题、简介等信息
   - 在"章节大纲编辑"标签页中编辑卷和章节信息

4. 生成章节：
   - 在"章节生成"标签页中选择要生成的章节
   - 点击"生成章节"按钮

5. 保存和加载：
   - 使用工具栏上的"保存"和"打开"按钮保存和加载小说项目

## 配置说明

在`config.ini`文件中配置以下内容：

- **代理设置**：如果需要使用代理访问API，配置代理地址和端口
- **API密钥**：配置OpenAI、Anthropic、Google、ModelScope的API密钥以及自定义API密钥
- **模型选择**：配置使用的具体模型版本
- **自定义API**：可以配置自定义OpenAI兼容API和ModelScope API的端点和启用状态

## 系统要求

- Python 3.8+
- PyQt6
- 网络连接（用于访问AI API）

## 许可证

[MIT License](LICENSE)

## 致谢

特别感谢克劳德先生（Mr. Claude）在本项目开发过程中提供的源码支持与技术指导。
