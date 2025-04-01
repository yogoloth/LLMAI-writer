# LLMAI-writer

<p align="center">
  <strong style="font-size: 2em;">LLMAI-writer</strong>
</p>

LLMAI-writer 是一个功能强大的 AI 辅助小说创作工具，利用最先进的大型语言模型帮助作家构思、规划和创作小说。无论您是经验丰富的作家还是初学者，LLMAI-writer 都能帮助您更高效地完成创作过程。

## ✨ 功能特点

### 📝 全流程创作支持
- **大纲生成**：根据您的创意、主题和风格，AI 自动生成完整的小说大纲
- **总大纲编辑**：编辑小说标题、核心主题、故事梗概和世界观设定
- **章节大纲编辑**：管理卷和章节结构，编辑章节摘要
- **人物设计**：创建和管理小说中的角色，包括背景、性格、外貌等详细信息
- **章节生成**：基于大纲和前后章节上下文，生成连贯的章节内容

### 🤖 多模型支持
- **主流 AI 模型**：支持 OpenAI 的 GPT 系列、Anthropic 的 Claude 系列、Google 的 Gemini 系列
- **开源模型**：支持 ModelScope 的 DeepSeek-R1 模型
- **自定义 API**：支持任何兼容 OpenAI 协议的 API 服务
- **流式输出**：所有模型均支持流式输出，实时查看生成过程

### 🛠️ 实用工具
- **提示词模板**：内置多种提示词模板，也可自定义和保存模板
- **上下文感知**：章节生成时自动考虑前后章节的内容，保持故事连贯性
- **自动编号**：自动为章节添加序号，并在重排序时更新
- **拖放排序**：支持通过拖放重新排序卷和章节
- **深色模式**：支持明亮和深色两种界面主题

## 📋 系统要求

- **操作系统**：Windows 10/11、macOS 10.14+、Linux
- **Python**：3.8 或更高版本
- **网络连接**：用于访问 AI API 服务
- **硬盘空间**：约 100MB（不包括生成的小说文件）

## 🚀 安装说明

### 1. 克隆仓库
```bash
git clone https://github.com/WhatRUHuh/LLMAI-writer.git
cd LLMAI-writer
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥
1. 复制 `config.example.ini` 为 `config.ini`
2. 编辑 `config.ini`，填入您的 API 密钥和其他配置

## 📖 使用指南

### 启动程序
```bash
python main.py
```

### 创作流程

#### 1. 大纲生成
- 在"大纲生成"标签页中填写小说的基本信息（标题、类型、主题、风格等）
- 设置卷数、每卷章节数和人物数量
- 选择 AI 模型并点击"生成大纲"按钮

#### 2. 大纲编辑
- 在"总大纲编辑"标签页中完善标题、主题、简介和世界观设定
- 在"章节大纲编辑"标签页中管理卷和章节结构
- 使用 AI 辅助编辑功能优化大纲内容

#### 3. 人物设计
- 在"人物编辑"标签页中创建和管理角色
- 设置角色的基本信息、背景故事、性格特点等
- 使用 AI 辅助生成丰富的角色设定

#### 4. 章节创作
- 在"章节生成"标签页中选择要编辑的章节
- 使用 AI 辅助编辑功能生成章节内容
- 系统会自动考虑前后章节的内容，保持故事连贯性

#### 5. 保存和加载
- 使用工具栏上的"保存"和"打开"按钮保存和加载小说项目（.ainovel 格式）
- 可以导出为纯文本或其他格式

## ⚙️ 配置详解

`config.ini` 文件包含以下配置项：

### 代理设置
```ini
[Proxy]
enabled = true/false
http_proxy = http://127.0.0.1:7890
https_proxy = http://127.0.0.1:7890
```

### API 密钥和模型设置
```ini
[OpenAI]
api_key = your_openai_api_key
model_name = gpt-4-turbo

[Claude]
api_key = your_anthropic_api_key
model_name = claude-3-opus-20240229

[Gemini]
api_key = your_google_api_key
model_name = gemini-1.5-pro

[ModelScope]
api_key = your_modelscope_api_key
model_name = deepseek-r1-chat
```

### 自定义 API 设置
```ini
[CustomOpenAI]
enabled = true/false
base_url = https://your-custom-openai-compatible-api.com/v1
api_key = your_custom_api_key
model_name = your_model_name
```

## 🔧 常见问题

### 安装依赖失败
如果安装依赖时遇到问题，可以尝试手动安装主要依赖：
```bash
pip install PyQt6 openai anthropic google-generativeai
```

### API 连接问题
- 确保您的 API 密钥正确
- 如果需要代理访问 API，请在配置文件中正确设置代理
- 检查网络连接是否正常

### 界面显示异常
- 尝试重启应用程序
- 检查是否安装了最新版本的 PyQt6
- 在不同的操作系统上，界面可能有细微差异

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- 特别感谢克劳德先生（Mr. Claude）在本项目开发过程中提供的源码支持与技术指导
- 感谢所有开源项目和 API 提供商，使本项目成为可能
- 感谢所有用户的反馈和建议，帮助我们不断改进

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 与我们联系。
