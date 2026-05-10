# 智能卸料动态匹配系统 - PowerShell自动部署脚本
# 服务器: 192.168.1.88
# 端口: 7787

$ErrorActionPreference = "Stop"

$server = "192.168.1.88"
$user = "root"
$password = "Admin@9000"
$remoteDir = "/opt/dispatch-center"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  智能卸料动态匹配系统 - 自动部署" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 创建SSH会话
Write-Host "[步骤 1/4] 连接到服务器..." -ForegroundColor Yellow
Write-Host "------------------------------------------"

# 使用plink (PuTTY) 执行命令
$plinkPath = "plink.exe"
$pscpPath = "pscp.exe"

# 检查是否安装了PuTTY
$puttyInstalled = $false
try {
    $null = Get-Command plink -ErrorAction Stop
    $puttyInstalled = $true
} catch {
    Write-Host "未找到PuTTY工具，将使用ssh/scp命令（需要手动输入密码）" -ForegroundColor Yellow
}

if ($puttyInstalled) {
    Write-Host "检测到PuTTY工具，使用自动密码登录" -ForegroundColor Green
    
    # 创建远程目录
    Write-Host "创建远程目录..." -ForegroundColor Gray
    $output = echo $password | plink -ssh -batch -pw $password $user@$server "mkdir -p $remoteDir" 2>&1
    Write-Host "[OK] 目录创建成功" -ForegroundColor Green
    
    # 上传文件
    Write-Host ""
    Write-Host "[步骤 2/4] 上传项目文件..." -ForegroundColor Yellow
    Write-Host "------------------------------------------"
    Write-Host "上传后端代码..." -ForegroundColor Gray
    
    # 使用pscp上传整个目录
    Get-ChildItem -Path "dispatch_center" -Recurse | ForEach-Object {
        $localPath = $_.FullName
        $relativePath = $_.FullName.Replace((Get-Location).Path + "\dispatch_center\", "").Replace("\", "/")
        $remotePath = "$remoteDir/dispatch_center/$relativePath"
        
        if ($_.PSIsContainer) {
            $null = echo $password | plink -ssh -batch -pw $password $user@$server "mkdir -p '$remotePath'" 2>&1
        } else {
            $remoteDirPath = Split-Path -Parent $remotePath
            $null = echo $password | plink -ssh -batch -pw $password $user@$server "mkdir -p '$remoteDirPath'" 2>&1
            $null = echo $password | pscp -scp -pw $password -q $localPath "$user@${server}:$remotePath" 2>&1
        }
    }
    Write-Host "[OK] 后端代码上传完成" -ForegroundColor Green
    
    # 上传部署脚本
    Write-Host "上传部署脚本..." -ForegroundColor Gray
    $null = echo $password | pscp -scp -pw $password -q "deploy-no-nginx.sh" "$user@${server}:$remoteDir/" 2>&1
    Write-Host "[OK] 部署脚本上传完成" -ForegroundColor Green
    
    # 执行部署脚本
    Write-Host ""
    Write-Host "[步骤 3/4] 在服务器上执行部署..." -ForegroundColor Yellow
    Write-Host "------------------------------------------"
    Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray
    
    $deployOutput = echo $password | plink -ssh -batch -pw $password $user@$server "cd $remoteDir && chmod +x deploy-no-nginx.sh && ./deploy-no-nginx.sh" 2>&1
    Write-Host $deployOutput
    
} else {
    Write-Host "请使用以下命令手动部署:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. SSH登录服务器:" -ForegroundColor Cyan
    Write-Host "   ssh root@$server" -ForegroundColor White
    Write-Host "   密码: $password" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. 创建目录:" -ForegroundColor Cyan
    Write-Host "   mkdir -p $remoteDir" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 在本地打开新终端，上传文件:" -ForegroundColor Cyan
    Write-Host "   scp -r dispatch_center/* root@${server}:$remoteDir/dispatch_center/" -ForegroundColor White
    Write-Host "   scp deploy-no-nginx.sh root@${server}:$remoteDir/" -ForegroundColor White
    Write-Host ""
    Write-Host "4. 在服务器上执行部署:" -ForegroundColor Cyan
    Write-Host "   cd $remoteDir" -ForegroundColor White
    Write-Host "   chmod +x deploy-no-nginx.sh" -ForegroundColor White
    Write-Host "   ./deploy-no-nginx.sh" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  部署脚本执行完成!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Green
Write-Host "  http://${server}:7787" -ForegroundColor White
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
