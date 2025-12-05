# 简单GitHub上传脚本 - 当Git不可用时使用
# 此脚本将ERP相关文件打包并准备手动上传到GitHub

# 创建临时目录
$TempDir = "$env:TEMP\ai-stack-upload-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "🚀 开始准备ERP模块代码上传..." -ForegroundColor Cyan

# 1. 复制ERP相关文件到临时目录
$ERP_Files = @(
    "💼 Intelligent ERP & Business Management/api/AI-STACK详细开发进度111.txt",
    "💼 Intelligent ERP & Business Management/api/erp_11_stages_api.py",
    "💼 Intelligent ERP & Business Management/api/erp_integration_api.py",
    "💼 Intelligent ERP & Business Management/core/erp_11_stages_manager.py",
    "💼 Intelligent ERP & Business Management/core/erp_8dimension_analysis.py",
    "🚀 Super Agent Main Interface/core/experts/erp_experts.py",
    "V5版本统计报告.md",
    "git-push.ps1"
)

Write-Host "📋 复制ERP相关文件..." -ForegroundColor Cyan
foreach ($File in $ERP_Files) {
    if (Test-Path $File) {
        $DestPath = Join-Path $TempDir $File
        $DestDir = Split-Path $DestPath -Parent
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        Copy-Item $File $DestPath -Force
        Write-Host "   ✅ $File" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $File (文件不存在)" -ForegroundColor Yellow
    }
}

# 2. 创建版本说明文件
$VersionInfo = "# AI-STACK V5.9.0 ERP模块更新`n`n"
$VersionInfo += "## 版本信息`n"
$VersionInfo += "- 版本号: V5.9.0`n"
$VersionInfo += "- 发布日期: $(Get-Date -Format 'yyyy-MM-dd')`n"
$VersionInfo += "- 发布说明: ERP模块功能更新`n`n"
$VersionInfo += "## 包含的文件`n"
foreach ($File in $ERP_Files) {
    $VersionInfo += "- $File`n"
}
$VersionInfo += "`n## 功能更新`n"
$VersionInfo += "- ERP 11环节全流程实现`n"
$VersionInfo += "- 8维度深度分析算法`n"
$VersionInfo += "- 专家模型集成`n"
$VersionInfo += "- 性能优化和测试`n`n"
$VersionInfo += "## 开发进度`n"
$VersionInfo += "基于AI-STACK详细开发进度111.txt的P0级别任务实现"

Set-Content -Path "$TempDir\V5.9.0-RELEASE-NOTES.md" -Value $VersionInfo

# 3. 创建压缩包
$ZipFile = "$env:TEMP\ai-stack-v5.9.0-erp-update-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Write-Host "📦 创建压缩包..." -ForegroundColor Cyan
try {
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipFile -Force
    Write-Host "   ✅ 压缩包创建成功: $ZipFile" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 压缩包创建失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. 显示文件信息
Write-Host ""
Write-Host "📊 准备上传的文件信息:" -ForegroundColor Cyan
Write-Host "   压缩包: $ZipFile" -ForegroundColor White
Write-Host "   文件数量: $(@(Get-ChildItem $TempDir -Recurse -File).Count)" -ForegroundColor White
Write-Host "   总大小: $([math]::Round((Get-Item $ZipFile).Length / 1MB, 2)) MB" -ForegroundColor White

# 5. 提供手动上传指导
$RepoOwner = "weicai-design"
$RepoName = "ai-stack-super-enhanced"

Write-Host ""
Write-Host "🔗 手动上传指导:" -ForegroundColor Cyan
Write-Host "1. 访问: https://github.com/$RepoOwner/$RepoName" -ForegroundColor White
Write-Host "2. 点击 'Add file' → 'Upload files'" -ForegroundColor White
Write-Host "3. 拖放压缩包: $ZipFile" -ForegroundColor White
Write-Host "4. 提交信息: 'V5.9.0: ERP模块功能更新'" -ForegroundColor White
Write-Host "5. 选择 'Commit directly to the main branch'" -ForegroundColor White
Write-Host "6. 点击 'Commit changes'" -ForegroundColor White

# 6. 创建标签的指导
Write-Host ""
Write-Host "🏷️ 创建版本标签指导:" -ForegroundColor Cyan
Write-Host "1. 访问: https://github.com/$RepoOwner/$RepoName/releases/new" -ForegroundColor White
Write-Host "2. 标签版本: v5.9.0" -ForegroundColor White
Write-Host "3. 发布标题: AI-STACK V5.9.0" -ForegroundColor White
Write-Host "4. 描述: ERP模块功能更新" -ForegroundColor White
Write-Host "5. 上传压缩包作为附件" -ForegroundColor White
Write-Host "6. 点击 'Publish release'" -ForegroundColor White

# 7. 清理临时文件
Write-Host ""
Write-Host "🧹 清理临时文件..." -ForegroundColor Cyan
Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ 准备完成！" -ForegroundColor Green
Write-Host "📋 请按照上面的指导手动上传文件到GitHub" -ForegroundColor Green
Write-Host "🔗 仓库地址: https://github.com/$RepoOwner/$RepoName" -ForegroundColor Green