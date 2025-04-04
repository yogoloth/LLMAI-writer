# LLMAI-writer

<p align="center">
  <img src="resources/icon.png" alt="LLMAI-writer Logo" width="200"/>
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

> **必读提示：** 本项目必须使用 **Python 3.9 或更高版本**！Gemini 功能依赖的 google-genai 库仅支持 Python 3.9+，这是 Google 官方的要求。如果您使用较旧版本的 Python，请参考常见问题部分的解决方案。

- **操作系统**：Windows 10/11、macOS 10.14+、Linux
- **Python**：3.9 或更高版本
- **网络连接**：用于访问 AI API 服务
- **硬盘空间**：约 100MB（不包括生成的小说文件）

## 🚀 安装说明

您可以选择使用传统方式或 Docker 方式安装和运行 LLMAI-writer。

### 方式一：传统安装

#### 1. 克隆仓库
```bash
git clone https://github.com/WhatRUHuh/LLMAI-writer.git
cd LLMAI-writer
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置 API 密钥
1. 复制 `config.example.ini` 为 `config.ini`
2. 编辑 `config.ini`，填入您的 API 密钥和其他配置

### 方式二：Docker 安装

> **注意：**Docker 版本基于 Python 3.12 构建，无需关心本地 Python 版本兼容问题。

#### 前提条件
- 安装 [Docker](https://www.docker.com/get-started)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

#### Linux/macOS 用户

1. 克隆仓库并进入项目目录
2. 运行启动脚本：
   ```bash
   chmod +x run_docker.sh
   ./run_docker.sh
   ```

#### Windows 用户

1. 克隆仓库并进入项目目录
2. 运行启动脚本：
   ```
   run_docker.bat
   ```

#### 配置和数据存储

- 首次运行时，复制 `config.example.ini` 为 `config.ini` 并进行配置
- 小说文件将保存在 `novels` 目录中，该目录会在容器和主机之间共享

## 📖 使用指南

> **小贴士：** 如果您此前从未接触过代码，建议您使用 Cursor、WindSurf、Cline、RooCode、Trae、Augment 等工具询问 AI 大模型，它们会自动帮您解释代码的功能和使用方法。

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

### 传统安装相关问题

#### 安装依赖失败
如果安装依赖时遇到问题，可以尝试手动安装主要依赖：
```bash
pip install PyQt6 openai anthropic google-genai
```

注意：如果安装 google-genai 失败，请确保您使用的是 Python 3.9 或更高版本。

如果您的 Python 版本低于 3.9，您有以下选择：
1. **升级 Python**：强烈推荐升级到 Python 3.9 或更高版本以获得完整功能
2. **使用 Docker 版本**：使用本项目提供的 Docker 配置，无需关心 Python 版本兼容问题
3. **移除 Gemini 相关代码**：如果无法升级 Python 且不想使用 Docker，您可以从项目中删除与 Gemini 相关的代码（主要在 `models/gemini_model.py` 和 UI 中的相关选项）

注意：根据 Google 官方文档，Gemini API 的 Python SDK 仅支持 Python 3.9 及更高版本，不存在兼容旧版本 Python 的方法。

#### API 连接问题
- 确保您的 API 密钥正确
- 如果需要代理访问 API，请在配置文件中正确设置代理
- 检查网络连接是否正常

#### 界面显示异常
- 尝试重启应用程序
- 检查是否安装了最新版本的 PyQt6
- 在不同的操作系统上，界面可能有细微差异

### Docker 相关问题

#### 显示问题
如果应用程序窗口无法显示，可能是X11转发配置问题。尝试以下解决方案：

1. Linux用户确保已允许Docker访问X服务器：
   ```bash
   xhost +local:docker
   ```

2. 检查DISPLAY环境变量是否正确设置

3. Windows用户可能需要安装X服务器（如VcXsrv或Xming）并进行适当配置

#### 字体问题
如果中文字体显示不正确，可能需要安装额外的字体包。编辑Dockerfile，添加更多字体包，然后重新构建镜像：

```bash
docker-compose build --no-cache
```

#### 数据持久化
如果您需要在容器重启后保留数据，请确保：

1. `config.ini` 文件在主机上正确配置
2. `novels` 目录已创建并正确挂载
3. 不要删除这些挂载的目录和文件

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- 特别感谢克劳德先生（Mr. Claude）在本项目开发过程中提供的源码支持与技术指导
- 感谢所有开源项目和 API 提供商，使本项目成为可能
- 感谢所有用户的反馈和建议，帮助我们不断改进

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 与我们联系。
