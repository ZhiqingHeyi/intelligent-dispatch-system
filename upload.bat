@echo off
chcp 65001 >nul
echo ==========================================
echo   智能卸料动态匹配系统 - 文件上传脚本
echo ==========================================
echo.

set SERVER=192.168.1.88
set USER=root
set REMOTE_DIR=/opt/dispatch-center

echo [信息] 服务器地址: %SERVER%
echo [信息] 远程目录: %REMOTE_DIR%
echo.

echo [步骤 1/3] 创建远程目录...
ssh %USER%@%SERVER% "mkdir -p %REMOTE_DIR%"
if errorlevel 1 (
    echo [错误] 无法连接到服务器或创建目录失败
    pause
    exit /b 1
)
echo [成功] 远程目录已创建
echo.

echo [步骤 2/3] 上传后端代码...
scp -r dispatch_center\* %USER%@%SERVER%:%REMOTE_DIR%/dispatch_center/
if errorlevel 1 (
    echo [错误] 上传后端代码失败
    pause
    exit /b 1
)
echo [成功] 后端代码已上传
echo.

echo [步骤 3/3] 上传部署脚本...
scp deploy.sh %USER%@%SERVER%:%REMOTE_DIR%/
if errorlevel 1 (
    echo [警告] 部署脚本上传失败（可选）
) else (
    echo [成功] 部署脚本已上传
)
echo.

echo ==========================================
echo   ✅ 文件上传完成！
echo ==========================================
echo.
echo 下一步操作:
echo   1. SSH登录到服务器: ssh root@192.168.1.88
echo   2. 进入项目目录: cd /opt/dispatch-center
echo   3. 执行部署脚本: chmod +x deploy.sh && ./deploy.sh
echo.
echo 或者直接访问:
echo   http://192.168.1.88:7777
echo.
pause
