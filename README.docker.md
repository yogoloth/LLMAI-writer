# LLMAI-writer Docker 使用指南

本应用程序基于 Python 3.12 构建。

本文档介绍如何使用Docker运行LLMAI-writer应用程序。

## 前提条件

- 安装 [Docker](https://www.docker.com/get-started)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 快速开始

### Linux/macOS用户

1. 确保Docker已安装并运行
2. 打开终端，进入项目目录
3. 运行启动脚本：
   ```bash
   chmod +x run_docker.sh
   ./run_docker.sh
   ```

### Windows用户

1. 确保Docker Desktop已安装并运行
2. 打开命令提示符或PowerShell，进入项目目录
3. 运行启动脚本：
   ```
   run_docker.bat
   ```

## 配置

### 配置文件

应用程序使用`config.ini`文件进行配置。首次运行时，如果该文件不存在，将创建一个默认配置文件。

您可以编辑项目目录中的`config.ini`文件，修改后的配置将在下次启动容器时生效。

### 数据存储

小说文件将保存在`novels`目录中。该目录会在首次运行时自动创建，并且会在容器和主机之间共享。

## 高级配置

### 自定义Docker Compose配置

您可以编辑`docker-compose.yml`文件来自定义Docker容器的配置：

```yaml
version: '3'

services:
  llmai-writer:
    build: .
    container_name: llmai-writer
    environment:
      - DISPLAY=${DISPLAY}
      - QT_QPA_PLATFORM=xcb
    volumes:
      - ./config.ini:/app/config.ini
      - ./novels:/app/novels
      - /tmp/.X11-unix:/tmp/.X11-unix
    network_mode: "host"
    command: --dark  # 可选：启用深色模式
```

### 命令行参数

您可以在`docker-compose.yml`文件的`command`部分添加命令行参数：

- `--dark`: 启用深色模式
- `--file path/to/file.ainovel`: 启动时打开指定的小说文件

## 故障排除

### 显示问题

如果应用程序窗口无法显示，可能是X11转发配置问题。尝试以下解决方案：

1. 确保已允许Docker访问X服务器：
   ```bash
   xhost +local:docker
   ```

2. 检查DISPLAY环境变量是否正确设置：
   ```bash
   echo $DISPLAY
   ```

3. 如果使用WSL2，可能需要额外的配置。请参考[在WSL2中使用GUI应用程序](https://docs.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)。

### 字体问题

如果中文字体显示不正确，可能需要安装额外的字体包。编辑Dockerfile，添加更多字体包：

```dockerfile
RUN apt-get update && apt-get install -y \
    # 其他依赖 \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*
```

然后重新构建Docker镜像：

```bash
docker-compose build --no-cache
```
