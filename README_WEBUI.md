# 🌌 SkyForge Web UI 使用指南

SkyForge 是下一代模型训练与推理 Web 平台。它采用现代化容器架构，支持一键 Docker 部署，为您提供开箱即用的 LLM/RLHF 训练环境。

## 🌟 核心特性

*   **⚡️ 极速部署**：基于 Docker 容器化封装，无需繁琐的环境配置，一键启动。
*   **🐳 完美隔离**：前端 Web 服务与后端 GPU 训练服务完全解耦，互不干扰。
*   **🎨 现代化交互**：全新的 SkyForge UI 设计，操作直观，专注于模型训练工作流。
*   **🚀 强大的后端**：支持全量参数微调、LoRA、RLHF 等多种训练模式。

---

## �️ 环境准备

在开始之前，请确保您的服务器满足以下要求：

1.  **操作系统**: Linux (推荐 Ubuntu 20.04/22.04) 或 Windows WSL2。
2.  **Docker**: 已安装 Docker Engine 和 Docker Compose。
3.  **NVIDIA GPU**: 建议显存 >= 24GB (取决于训练的模型大小)。
4.  **NVIDIA Container Toolkit**: **必须安装**，用于让 Docker 容器调用 GPU 资源。
    *   [安装文档参考](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

---

## 🚀 快速启动

只需简单几步即可启动 SkyForge：

### 1. 进入项目目录

确保您已下载本项目代码：

```bash
cd skyforge
```

### 2. 启动服务

使用 Docker Compose 一键拉起所有服务：

```bash
docker-compose up -d
```

此命令将自动：
*   构建或拉取后端镜像 (`swift-backend`)
*   构建前端镜像 (`swift-frontend`)
*   启动服务并建立网络连接

### 3. 访问 Web UI

服务启动后，请在浏览器中访问：

**http://localhost:8080**

> ⚠️ **注意**：如果部署在远程服务器上，请将 `localhost` 替换为服务器的 IP 地址。确保您的防火墙已开放 **8080** (前端) 和 **8000** (后端 API) 端口。

---

## 📖 服务架构说明

SkyForge 包含两个核心服务容器：

| 服务名称 | 容器名 | 端口映射 | 说明 |
| :--- | :--- | :--- | :--- |
| **Backend** | `swift-backend` | `8000:8000` | 负责 GPU 调度、模型训练、推理 API。需独占 GPU 资源。 |
| **Frontend** | `swift-frontend` | `8080:80` | 基于 Vue.js 的 Web 界面，轻量级运行，通过 API 与后端通信。 |

### 常用操作

**查看日志**：

```bash
# 查看后端日志 (训练进度、报错信息)
docker logs -f swift-backend

# 查看前端日志 (Nginx 访问日志)
docker logs -f swift-frontend
```

**停止服务**：

```bash
docker-compose down
```

**重建镜像** (代码修改后)：

```bash
docker-compose up -d --build
```

---

## ❓ 常见问题

**Q: 启动后页面提示 "Network Error" 或无法连接后端？**
A: 前端默认尝试连接 `http://localhost:8000`。
*   **本地部署**：请检查 `swift-backend` 容器是否运行正常 (`docker ps`)，以及 8000 端口是否被占用。
*   **远程部署**：Web 浏览器运行在您的本地电脑上，它会尝试连接 `localhost:8000`，这会导致连接失败。您需要做以下任一操作：
    1.  (推荐) 使用 SSH 隧道将服务器的 8000 端口映射到本地：`ssh -L 8000:localhost:8000 user@server_ip`
    2.  或者修改前端代码中的 API 地址配置，并重新构建镜像。

**Q: 训练任务显示显存不足 (OOM)？**
A: 请检查 `docker-compose.yml` 中的 GPU 配置。默认配置尝试使用所有可见 GPU。
如果您与其他服务共享 GPU，请修改 `deploy.resources.reservations.devices` 部分来指定特定 GPU ID。

**Q: 如何挂载自定义数据集？**
A: `docker-compose.yml` 默认将当前目录挂载到容器内的 `/app`。您可以将数据集放在项目目录下，然后在 Web UI 中使用相对路径或绝对路径 `/app/...` 引用。
