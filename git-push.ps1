# GitHub 一键上传脚本 - Windows PowerShell版本
# 使用方法: .\git-push.ps1 或 powershell -ExecutionPolicy Bypass -File git-push.ps1

# 设置工作目录到当前脚本所在目录
$ScriptPath = $PSScriptRoot
if (-not $ScriptPath) {
    $ScriptPath = Get-Location
}
Set-Location $ScriptPath

# 检查是否有未提交的更改
$gitStatus = git status --porcelain
if (-not $gitStatus) {
    Write-Host "ℹ️  没有需要提交的更改" -ForegroundColor Yellow
    exit 0
}

# 显示将要提交的文件
Write-Host "📋 准备提交以下文件：" -ForegroundColor Cyan
git status --short

# 添加所有更改
Write-Host ""
Write-Host "📦 正在添加文件..." -ForegroundColor Cyan
git add .

# 生成提交信息
if ($args.Count -gt 0) {
    $COMMIT_MSG = $args[0]
} else {
    $COMMIT_MSG = "更新代码 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

# 提交更改
Write-Host "💾 正在提交更改..." -ForegroundColor Cyan
git commit -m $COMMIT_MSG

# 推送到 GitHub
Write-Host "🚀 正在推送到 GitHub..." -ForegroundColor Cyan
if (git push origin main) {
    Write-Host ""
    Write-Host "✅ 代码已成功上传到 GitHub！" -ForegroundColor Green
    Write-Host "📊 提交信息: $COMMIT_MSG" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 推送失败，请检查网络连接或权限设置" -ForegroundColor Red
    exit 1
}