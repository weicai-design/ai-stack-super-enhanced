# ERP模块手动上传脚本
Write-Host "🚀 开始ERP模块手动上传流程..." -ForegroundColor Cyan

# 检查现有压缩包
$ZipFile = "C:\Users\caiwe\AppData\Local\Temp\ai-stack-v5.9.0-erp-update-20251204-120123.zip"
if (Test-Path $ZipFile) {
    Write-Host "✅ 找到现有压缩包: $ZipFile" -ForegroundColor Green
    $FileSize = [math]::Round((Get-Item $ZipFile).Length / 1MB, 2)
    Write-Host "   文件大小: $FileSize MB" -ForegroundColor White
} else {
    Write-Host "❌ 压缩包不存在: $ZipFile" -ForegroundColor Red
    exit 1
}

# 显示上传指导
Write-Host ""
Write-Host "🔗 手动上传指导:" -ForegroundColor Cyan
Write-Host "1. 访问: https://github.com/weicai-design/ai-stack-super-enhanced" -ForegroundColor White
Write-Host "2. 点击 'Add file' → 'Upload files'" -ForegroundColor White
Write-Host "3. 拖放压缩包: $ZipFile" -ForegroundColor White
Write-Host "4. 提交信息: 'V5.9.0: ERP模块功能更新'" -ForegroundColor White
Write-Host "5. 选择 'Commit directly to the main branch'" -ForegroundColor White
Write-Host "6. 点击 'Commit changes'" -ForegroundColor White

Write-Host ""
Write-Host "🏷️ 创建版本标签指导:" -ForegroundColor Cyan
Write-Host "1. 访问: https://github.com/weicai-design/ai-stack-super-enhanced/releases/new" -ForegroundColor White
Write-Host "2. 标签版本: v5.9.0" -ForegroundColor White
Write-Host "3. 发布标题: AI-STACK V5.9.0" -ForegroundColor White
Write-Host "4. 描述: ERP模块功能更新" -ForegroundColor White
Write-Host "5. 上传压缩包作为附件" -ForegroundColor White
Write-Host "6. 点击 'Publish release'" -ForegroundColor White

Write-Host ""
Write-Host "✅ 上传准备完成！" -ForegroundColor Green
Write-Host "📋 请按照上面的指导手动上传文件到GitHub" -ForegroundColor Green