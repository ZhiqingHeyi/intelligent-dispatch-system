# 智能卸料动态匹配系统 - 服务器部署指南

## 📋 部署信息

- **服务器地址**: 192.168.1.88
- **用户名**: root
- **后端端口**: 8080
- **前端访问端口**: 7777 (通过Nginx反向代理)
- **项目目录**: /opt/dispatch-center

## 🏗️ 系统架构

```
用户浏览器 (端口7777)
       ↓
   Nginx (反向代理)
       ↓
 Flask后端服务 (端口8080)
       ↓
   SQLite数据库 + AI引擎
```

## 📦 已完成的准备工作

✅ 后端端口已配置为8080  
✅ 前端已构建为生产版本（输出到dispatch_center/static/vue-dist）  
✅ Nginx配置文件已创建（nginx.conf）  
✅ Linux部署脚本已创建（deploy.sh）  
✅ Windows上传脚本已创建（upload.bat）  
✅ 一键部署脚本已创建（deploy.bat）

## 🚀 快速部署（推荐方式）

### 方式一：使用一键部署脚本（Windows）

1. **双击运行** `deploy.bat`
2. **输入SSH密码**: Admin@9000
3. **等待自动完成**（约2-5分钟）
4. **访问系统**: http://192.168.1.88:7777

### 方式二：手动分步部署

#### 步骤1：上传文件到服务器

双击运行 `upload.bat` 或手动执行：

```bash
# 创建远程目录
ssh root@192.168.1.88 "mkdir -p /opt/dispatch-center"

# 上传后端代码
scp -r dispatch_center/* root@192.168.1.88:/opt/dispatch-center/dispatch_center/

# 上传部署脚本
scp deploy.sh root@192.168.1.88:/opt/dispatch-center/
```

#### 步骤2：SSH登录服务器并执行部署

```bash
ssh root@192.168.1.88
cd /opt/dispatch-center
chmod +x deploy.sh
sudo ./deploy.sh
```

### 方式三：完全手动部署（高级用户）

如果需要完全控制部署过程，可以按照以下步骤操作：

#### 1. 安装依赖

```bash
# 更新系统
apt-get update

# 安装Python3和pip
apt-get install -y python3 python3-pip

# 安装Nginx
apt-get install -y nginx

# 安装Python依赖
pip3 install flask requests openai --break-system-packages
```

#### 2. 上传项目文件

将 `dispatch_center` 目录上传到 `/opt/dispatch-center/dispatch_center/`

#### 3. 配置Nginx

创建配置文件 `/etc/nginx/conf.d/dispatch-center.conf`：

```nginx
server {
    listen 7777;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
    }
}
```

测试并重启Nginx：

```bash
nginx -t
systemctl restart nginx
systemctl enable nginx
```

#### 4. 创建系统服务

创建 `/etc/systemd/system/dispatch-center.service`：

```ini
[Unit]
Description=智能卸料动态匹配系统后端服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dispatch-center/dispatch_center
ExecStart=/usr/bin/python3 /opt/dispatch-center/dispatch_center/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
systemctl daemon-reload
systemctl enable dispatch-center
systemctl start dispatch-center
```

## ✅ 部署验证

### 检查端口监听

```bash
ss -tlnp | grep -E ':(7777|8080) '
```

预期输出：
```
LISTEN  0  128  0.0.0.0:7777  0.0.0.0:*  users:(("nginx",pid=...,fd=...))
LISTEN  0  128  0.0.0.0:8080  0.0.0.0:*  users:(("python3",pid=...,fd=...))
```

### 检查服务状态

```bash
# 检查后端服务
systemctl status dispatch-center

# 检查Nginx服务
systemctl status nginx
```

### 测试访问

在浏览器中打开：
- 前端界面: http://192.168.1.88:7777
- API测试: http://192.168.1.88:8080/api/status

## 🔧 常用运维命令

```bash
# 查看服务状态
systemctl status dispatch-center

# 重启服务
systemctl restart dispatch-center

# 停止服务
systemctl stop dispatch-center

# 查看实时日志
journalctl -u dispatch-center -f

# 查看最近100条日志
journalctl -u dispatch-center -n 100 --no-pager

# 重启Nginx
systemctl restart nginx

# 测试Nginx配置
nginx -t
```

## 🐛 故障排查

### 问题1：无法访问7777端口

**可能原因**：
- 防火墙未开放端口
- Nginx未启动或配置错误

**解决方案**：
```bash
# 检查防火墙（Ubuntu/Debian）
ufw allow 7777
ufw allow 8080

# 或者使用iptables
iptables -A INPUT -p tcp --dport 7777 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# 检查Nginx状态
systemctl status nginx

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### 问题2：后端服务启动失败

**解决方案**：
```bash
# 查看详细日志
journalctl -u dispatch-center -n 50 --no-pager

# 手动测试启动
cd /opt/dispatch-center/dispatch_center
python3 app.py

# 检查Python依赖是否安装完整
pip3 list | grep -E "(flask|requests|openai)"
```

### 问题3：前端页面空白或API错误

**检查项**：
1. 前端构建文件是否存在：`ls -la /opt/dispatch-center/dispatch_center/static/vue-dist/`
2. 后端API是否正常：`curl http://127.0.0.1:8080/api/status`
3. 浏览器控制台是否有错误（F12打开开发者工具）

### 问题4：端口被占用

```bash
# 查找占用端口的进程
lsof -i :8080
lsof -i :7777

# 杀掉占用进程（谨慎操作）
kill -9 <PID>
```

## 📁 文件说明

```
智能卸料动态匹配/
├── dispatch_center/          # 后端代码目录
│   ├── app.py               # 主应用（已修改端口为8080）
│   ├── static/vue-dist/     # 前端构建产物（已生成）
│   └── ...
├── vue-frontend/            # 前端源码（开发用）
├── nginx.conf               # Nginx配置文件
├── deploy.sh                # Linux部署脚本
├── upload.bat              # Windows上传脚本
├── deploy.bat              # Windows一键部署脚本
└── DEPLOY.md               # 本部署文档
```

## 🔒 安全建议

1. **修改默认密码**：部署完成后，请立即修改root密码
2. **配置防火墙**：只开放必要的端口（7777、8080）
3. **使用HTTPS**：生产环境建议配置SSL证书
4. **定期备份**：定期备份数据库文件（`dispatch_center/data.db`）
5. **更新系统**：`apt-get update && apt-get upgrade`

## 📞 技术支持

如遇到问题，请检查：
1. 服务日志：`journalctl -u dispatch-center -f`
2. Nginx日志：`/var/log/nginx/error.log`
3. 系统日志：`journalctl -xe`

---

**部署时间**: 2026-04-27  
**系统版本**: 1.0.0  
**部署环境**: Ubuntu/Debian + Python3 + Nginx
