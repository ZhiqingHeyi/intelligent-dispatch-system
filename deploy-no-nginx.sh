#!/bin/bash

# 智能卸料动态匹配系统 - 服务器部署脚本（无Nginx版）
# 服务器: 192.168.1.88
# 服务端口: 7787（前后端一体）

set -e

echo "=========================================="
echo "  智能卸料动态匹配系统 - 部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目路径
PROJECT_DIR="/opt/dispatch-center"
BACKEND_DIR="$PROJECT_DIR/dispatch_center"

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    print_error "请使用root用户运行此脚本"
    exit 1
fi

echo ""
echo "[步骤 1/4] 检查系统环境..."
echo "----------------------------------------"

# 检查Python3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python3已安装: $PYTHON_VERSION"
else
    print_error "Python3未安装，正在安装..."
    apt-get update && apt-get install -y python3 python3-pip
fi

# 检查pip3
if command -v pip3 &> /dev/null; then
    print_status "pip3已安装"
else
    print_warning "pip3未安装，正在安装..."
    apt-get install -y python3-pip
fi

echo ""
echo "[步骤 2/4] 创建项目目录..."
echo "----------------------------------------"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    print_status "项目目录已创建: $PROJECT_DIR"
else
    print_warning "项目目录已存在: $PROJECT_DIR"
fi

echo ""
echo "[步骤 3/4] 安装Python依赖..."
echo "----------------------------------------"

cd "$PROJECT_DIR"

# 创建requirements.txt（如果不存在）
cat > requirements.txt << 'EOF'
flask==3.0.0
requests==2.31.0
openai==1.6.1
pymysql==1.1.0
EOF

print_status "正在安装Python依赖..."
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

echo ""
echo "[步骤 4/4] 创建系统服务..."
echo "----------------------------------------"

# 创建systemd服务文件
cat > /etc/systemd/system/dispatch-center.service << EOF
[Unit]
Description=智能卸料动态匹配系统服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
ExecStart=/usr/bin/python3 $BACKEND_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_status "系统服务文件已创建"

# 重载systemd并启用服务
systemctl daemon-reload
systemctl enable dispatch-center
print_status "服务已设置为开机自启"

# 停止旧服务（如果存在）
if systemctl is-active --quiet dispatch-center 2>/dev/null; then
    print_warning "停止旧服务..."
    systemctl stop dispatch-center
fi

# 启动服务
systemctl start dispatch-center
sleep 3

# 检查服务状态
if systemctl is-active --quiet dispatch-center; then
    print_status "服务已成功启动"
else
    print_error "服务启动失败，请检查日志："
    journalctl -u dispatch-center -n 50 --no-pager
    exit 1
fi

# 检查端口监听状态
sleep 2
if ss -tlnp | grep -q ":7787 "; then
    print_status "服务正在监听7787端口"
else
    print_warning "服务可能未正常监听端口，请手动检查"
fi

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  http://192.168.1.88:7787"
echo ""
echo "常用命令:"
echo "  查看服务状态: systemctl status dispatch-center"
echo "  重启服务:     systemctl restart dispatch-center"
echo "  查看日志:     journalctl -u dispatch-center -f"
echo "  停止服务:     systemctl stop dispatch-center"
echo ""
echo "文件位置:"
echo "  项目目录:     /opt/dispatch-center"
echo "  后端代码:     $BACKEND_DIR"
echo ""
echo "=========================================="
