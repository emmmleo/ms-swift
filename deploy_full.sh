#!/bin/bash

# Swift Web UI 一键部署脚本
# 该脚本将同时启动后端 API 服务和前端 Docker 容器

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 工作目录
WORK_DIR=$(pwd)
LOG_DIR="$WORK_DIR/logs"
OUTPUT_DIR="$WORK_DIR/output"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}      Swift Web UI 一键部署脚本          ${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. 环境检查
echo -e "\n${GREEN}[1/5] 正在检查环境...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Docker，请先安装 Docker。${NC}"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Python，请先安装 Python 环境。${NC}"
    exit 1
fi

# 2. 准备目录
echo -e "\n${GREEN}[2/5] 正在准备目录...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$OUTPUT_DIR"
echo "日志目录: $LOG_DIR"
echo "输出目录: $OUTPUT_DIR"

# 3. 启动后端服务
echo -e "\n${GREEN}[3/5] 正在启动后端 API 服务...${NC}"
# 检查端口 8000 是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${BLUE}端口 8000 已被占用，正在尝试关闭旧进程...${NC}"
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9
fi

# 后台启动 agent.py
nohup python swift/ui/agent.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "后端服务已启动 (PID: $BACKEND_PID)"
echo -e "后端日志: $LOG_DIR/backend.log"

# 等待后端启动
echo "等待后端服务就绪..."
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}后端服务启动成功!${NC}"
else
    echo -e "${RED}后端服务启动失败，请检查日志。${NC}"
    cat "$LOG_DIR/backend.log"
    exit 1
fi

# 4. 部署前端容器
echo -e "\n${GREEN}[4/5] 正在部署前端 Docker 容器...${NC}"

cd web-ui || { echo -e "${RED}错误: 找不到 web-ui 目录${NC}"; exit 1; }

# 检查是否存在旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^swift-web-ui$"; then
    echo -e "${BLUE}发现旧容器，正在移除...${NC}"
    docker rm -f swift-web-ui
fi

# 构建镜像
echo "正在构建前端镜像 (swift-web-ui)..."
docker build -t swift-web-ui .

if [ $? -ne 0 ]; then
    echo -e "${RED}前端镜像构建失败!${NC}"
    exit 1
fi

# 启动容器
echo "正在启动容器..."
docker run -d \
  -p 8080:80 \
  --name swift-web-ui \
  --restart unless-stopped \
  swift-web-ui

if [ $? -eq 0 ]; then
    echo -e "${GREEN}前端容器启动成功!${NC}"
else
    echo -e "${RED}前端容器启动失败!${NC}"
    exit 1
fi

cd ..

# 5. 完成
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}      部署完成! (Deployment Success)     ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "前端访问地址: http://localhost:8080"
echo -e "后端 API 地址: http://localhost:8000"
echo -e "默认账号: admin"
echo -e "默认密码: swift"
echo -e "${BLUE}=========================================${NC}"
