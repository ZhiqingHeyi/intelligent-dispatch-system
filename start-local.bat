@echo off
chcp 65001 >nul
echo ==========================================
echo   智能卸料动态匹配系统 - 本地启动脚本
echo ==========================================
echo.

echo [信息] 后端端口: 8080
echo [信息] 前端端口: 7777 (需要Nginx)
echo.

cd /d "%~dp0dispatch_center"

echo [步骤 1/2] 启动后端服务...
echo    正在启动Flask服务器 (端口8080)...
echo    按 Ctrl+C 停止服务
echo.
python app.py

pause
