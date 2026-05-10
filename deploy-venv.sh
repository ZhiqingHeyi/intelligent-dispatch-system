#!/bin/bash

# 智能卸料动态匹配系统 - 虚拟环境部署脚本
# 服务器: 192.168.1.88
# Vue前端端口: 9023
# Flask后端端口: 9045

set -e

echo "=========================================="
echo "  智能卸料动态匹配系统 - 虚拟环境部署"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目路径
PROJECT_DIR="/opt/dispatch-center"
BACKEND_DIR="$PROJECT_DIR/dispatch_center"
FRONTEND_DIR="$PROJECT_DIR/vue-frontend-dist"
VENV_DIR="$PROJECT_DIR/venv"

# 端口配置
FRONTEND_PORT=9023
BACKEND_PORT=9045

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
echo "[步骤 1/8] 检查端口占用..."
echo "----------------------------------------"

# 检查端口是否被占用
check_port() {
    local port=$1
    if ss -tln | grep -q ":$port "; then
        print_error "端口 $port 已被占用"
        ss -tlnp | grep ":$port "
        return 1
    else
        print_status "端口 $port 可用"
        return 0
    fi
}

check_port $FRONTEND_PORT || exit 1
check_port $BACKEND_PORT || exit 1

echo ""
echo "[步骤 2/8] 创建项目目录..."
echo "----------------------------------------"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    print_status "项目目录已创建: $PROJECT_DIR"
else
    print_warning "项目目录已存在: $PROJECT_DIR"
fi

echo ""
echo "[步骤 3/8] 创建Python虚拟环境..."
echo "----------------------------------------"

if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在，删除旧环境..."
    rm -rf "$VENV_DIR"
fi

# 创建虚拟环境
python3 -m venv "$VENV_DIR"
print_status "虚拟环境已创建: $VENV_DIR"

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
print_status "虚拟环境已激活"

# 升级pip
pip install --upgrade pip -q
print_status "pip已升级"

echo ""
echo "[步骤 4/8] 安装Python依赖（虚拟环境内）..."
echo "----------------------------------------"

# 创建requirements.txt（使用>=不强制降级）
cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
flask>=3.0.0
requests>=2.31.0
openai>=1.6.1
pymysql>=1.1.0
EOF

print_status "安装依赖到虚拟环境..."
pip install -r "$PROJECT_DIR/requirements.txt"

print_status "依赖安装完成"
echo "安装的包版本："
pip list | grep -E "Flask|requests|openai|PyMySQL"

echo ""
echo "[步骤 5/8] 配置后端服务..."
echo "----------------------------------------"

# 修改app.py使用9045端口
if [ -f "$BACKEND_DIR/app.py" ]; then
    sed -i "s/port=7787/port=$BACKEND_PORT/g" "$BACKEND_DIR/app.py"
    print_status "后端端口已配置为: $BACKEND_PORT"
fi

echo ""
echo "[步骤 6/8] 配置Vue前端服务..."
echo "----------------------------------------"

# 创建前端服务脚本
cat > "$PROJECT_DIR/start-frontend.sh" << EOF
#!/bin/bash
cd $FRONTEND_DIR
python3 -m http.server $FRONTEND_PORT --bind 0.0.0.0
EOF
chmod +x "$PROJECT_DIR/start-frontend.sh"
print_status "前端服务脚本已创建"

echo ""
echo "[步骤 7/8] 创建systemd服务..."
echo "----------------------------------------"

# 后端服务
cat > /etc/systemd/system/dispatch-center-backend.service << EOF
[Unit]
Description=智能卸料动态匹配系统后端服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python $BACKEND_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_status "后端服务配置已创建"

# 前端服务
cat > /etc/systemd/system/dispatch-center-frontend.service << EOF
[Unit]
Description=智能卸料动态匹配系统前端服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$FRONTEND_DIR
ExecStart=/usr/bin/python3 -m http.server $FRONTEND_PORT --bind 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_status "前端服务配置已创建"

echo ""
echo "[步骤 8/8] 启动服务..."
echo "----------------------------------------"

# 重载systemd
systemctl daemon-reload

# 停止旧服务（如果存在）
systemctl stop dispatch-center-backend 2>/dev/null || true
systemctl stop dispatch-center-frontend 2>/dev/null || true

# 启动前端服务
systemctl enable dispatch-center-frontend
systemctl start dispatch-center-frontend
sleep 2

if systemctl is-active --quiet dispatch-center-frontend; then
    print_status "前端服务已启动 (端口: $FRONTEND_PORT)"
else
    print_error "前端服务启动失败"
    journalctl -u dispatch-center-frontend -n 10 --no-pager
    exit 1
fi

# 启动后端服务
systemctl enable dispatch-center-backend
systemctl start dispatch-center-backend
sleep 3

if systemctl is-active --quiet dispatch-center-backend; then
    print_status "后端服务已启动 (端口: $BACKEND_PORT)"
else
    print_error "后端服务启动失败"
    journalctl -u dispatch-center-backend -n 10 --no-pager
    exit 1
fi

# 检查端口
sleep 2
if ss -tlnp | grep -q ":$FRONTEND_PORT "; then
    print_status "前端端口 $FRONTEND_PORT 监听正常"
else
    print_warning "前端端口 $FRONTEND_PORT 可能未正常监听"
fi

if ss -tlnp | grep -q ":$BACKEND_PORT "; then
    print_status "后端端口 $BACKEND_PORT 监听正常"
else
    print_warning "后端端口 $BACKEND_PORT 可能未正常监听"
fi

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  Vue前端: http://192.168.1.88:$FRONTEND_PORT"
echo "  Flask后端API: http://192.168.1.88:$BACKEND_PORT"
echo "  后端API测试: http://192.168.1.88:$BACKEND_PORT/api/status"
echo ""
echo "文件位置:"
echo "  项目目录:     $PROJECT_DIR"
echo "  虚拟环境:     $VENV_DIR"
echo "  后端代码:     $BACKEND_DIR"
echo "  前端代码:     $FRONTEND_DIR"
echo ""
echo "常用命令:"
echo "  查看后端状态: systemctl status dispatch-center-backend"
echo "  查看前端状态: systemctl status dispatch-center-frontend"
echo "  重启后端:     systemctl restart dispatch-center-backend"
echo "  重启前端:     systemctl restart dispatch-center-frontend"
echo "  后端日志:     journalctl -u dispatch-center-backend -f"
echo "  前端日志:     journalctl -u dispatch-center-frontend -f"
echo ""
echo "虚拟环境使用:"
echo "  source $VENV_DIR/bin/activate"
echo "  deactivate"
echo ""
echo "=========================================="
