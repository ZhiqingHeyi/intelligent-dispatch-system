@echo off
chcp 65001 >nul
echo ==========================================
echo   智能卸料动态匹配系统 - 一键部署脚本
echo ==========================================
echo.

set SERVER=192.168.1.88
set USER=root
set REMOTE_DIR=/opt/dispatch-center

echo [信息] 服务器地址: %SERVER%
echo [信息] 远程目录: %REMOTE_DIR%
echo.
echo ⚠️  注意: 此脚本需要SSH密码输入，请确保已安装SSH客户端
echo.

echo [步骤 1/4] 创建远程项目目录...
ssh %USER%@%SERVER% "mkdir -p %REMOTE_DIR%"
if errorlevel 1 (
    echo [错误] 无法连接到服务器
    pause
    exit /b 1
)
echo [✓] 目录创建成功
echo.

echo [步骤 2/4] 上传项目文件...
echo    正在上传后端代码...
scp -r dispatch_center\* %USER%@%SERVER%:%REMOTE_DIR%/dispatch_center/
if errorlevel 1 (
    echo [错误] 上传失败
    pause
    exit /b 1
)
echo [✓] 后端代码上传成功

echo    正在上传部署脚本...
scp deploy.sh %USER%@%SERVER%:%REMOTE_DIR%/
echo [✓] 部署脚本上传成功
echo.

echo [步骤 3/4] 执行服务器端部署...
echo    正在连接服务器并执行部署脚本...
echo    ⚠️  此步骤可能需要几分钟时间，请耐心等待...
echo.
ssh -t %USER%@%SERVER% "cd %REMOTE_DIR% && chmod +x deploy.sh && sudo ./deploy.sh"
if errorlevel 1 (
    echo.
    echo [警告] 部署脚本执行可能未完全成功
    echo         请手动登录服务器检查: ssh root@192.168.1.88
) else (
    echo.
    echo [✓] 服务器端部署完成
)
echo.

echo ==========================================
echo   🎉 部署流程完成！
echo ==========================================
echo.
echo 系统访问地址:
echo   前端界面: http://%SERVER%:7777
echo   后端API:  http://%SERVER%:8080
echo.
echo 如果无法访问，请检查:
echo   1. 防火墙是否开放7777和8080端口
echo   2. 服务状态: systemctl status dispatch-center
echo   3. Nginx状态: systemctl status nginx
echo.
echo 快速检查命令 (在服务器上执行):
echo   ss -tlnp | grep -E ':(7777|8080) '
echo.
pause
