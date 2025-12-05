# GitHub API 代码推送脚本 - 替代Git命令
# 当Git不可用时使用此脚本直接推送代码到GitHub

param(
    [string]$GitHubToken,
    [string]$RepoOwner = "weicai-design",
    [string]$RepoName = "ai-stack-super-enhanced",
    [string]$CommitMessage = "V5.9.0: 更新ERP模块功能",
    [string]$Branch = "main"
)

# 检查必要的参数
if (-not $GitHubToken) {
    Write-Host "❌ 错误：需要提供GitHub Token" -ForegroundColor Red
    Write-Host "使用方法: .\github-api-push.ps1 -GitHubToken 'your_token'" -ForegroundColor Yellow
    exit 1
}

# GitHub API基础URL
$BaseUrl = "https://api.github.com"
$Headers = @{
    "Authorization" = "token $GitHubToken"
    "Accept" = "application/vnd.github.v3+json"
}

# 获取当前分支的SHA
function Get-BranchSHA {
    param($BranchName)
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/refs/heads/$BranchName"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Get
        return $Response.object.sha
    }
    catch {
        Write-Host "❌ 获取分支SHA失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 创建Blob（文件内容）
function Create-Blob {
    param($FilePath)
    
    $Content = Get-Content -Path $FilePath -Raw -Encoding UTF8
    $Base64Content = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Content))
    
    $Body = @{
        content = $Base64Content
        encoding = "base64"
    } | ConvertTo-Json
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/blobs"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Post -Body $Body -ContentType "application/json"
        return $Response.sha
    }
    catch {
        Write-Host "❌ 创建Blob失败 ($FilePath): $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 创建树
function Create-Tree {
    param($BaseTreeSHA, $Files)
    
    $TreeEntries = @()
    
    foreach ($File in $Files) {
        $BlobSHA = Create-Blob -FilePath $File
        if ($BlobSHA) {
            $RelativePath = $File.Replace((Get-Location).Path + "\", "").Replace("\\", "/")
            $TreeEntries += @{
                path = $RelativePath
                mode = "100644"
                type = "blob"
                sha = $BlobSHA
            }
        }
    }
    
    $Body = @{
        base_tree = $BaseTreeSHA
        tree = $TreeEntries
    } | ConvertTo-Json
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/trees"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Post -Body $Body -ContentType "application/json"
        return $Response.sha
    }
    catch {
        Write-Host "❌ 创建树失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 创建提交
function Create-Commit {
    param($TreeSHA, $ParentSHA, $Message)
    
    $Body = @{
        message = $Message
        tree = $TreeSHA
        parents = @($ParentSHA)
    } | ConvertTo-Json
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/commits"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Post -Body $Body -ContentType "application/json"
        return $Response.sha
    }
    catch {
        Write-Host "❌ 创建提交失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 更新引用
function Update-Reference {
    param($CommitSHA, $BranchName)
    
    $Body = @{
        sha = $CommitSHA
    } | ConvertTo-Json
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/refs/heads/$BranchName"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Patch -Body $Body -ContentType "application/json"
        return $true
    }
    catch {
        Write-Host "❌ 更新引用失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 创建标签
function Create-Tag {
    param($TagName, $CommitSHA, $Message)
    
    $Body = @{
        tag = $TagName
        message = $Message
        object = $CommitSHA
        type = "commit"
    } | ConvertTo-Json
    
    $Url = "$BaseUrl/repos/$RepoOwner/$RepoName/git/tags"
    try {
        $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Post -Body $Body -ContentType "application/json"
        return $Response.sha
    }
    catch {
        Write-Host "❌ 创建标签失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 主执行流程
Write-Host "🚀 开始通过GitHub API推送代码..." -ForegroundColor Cyan

# 1. 获取当前分支SHA
Write-Host "📋 获取分支信息..." -ForegroundColor Cyan
$BranchSHA = Get-BranchSHA -BranchName $Branch
if (-not $BranchSHA) {
    Write-Host "❌ 无法获取分支信息，请检查仓库是否存在" -ForegroundColor Red
    exit 1
}

# 2. 定义要推送的ERP相关文件
$ERP_Files = @(
    "💼 Intelligent ERP & Business Management\api\AI-STACK详细开发进度111.txt",
    "💼 Intelligent ERP & Business Management\api\erp_11_stages_api.py",
    "💼 Intelligent ERP & Business Management\api\erp_integration_api.py",
    "💼 Intelligent ERP & Business Management\core\erp_11_stages_manager.py",
    "💼 Intelligent ERP & Business Management\core\erp_8dimension_analysis.py",
    "🚀 Super Agent Main Interface\core\experts\erp_experts.py",
    "V5版本统计报告.md",
    "git-push.ps1"
)

# 3. 创建树
Write-Host "📦 创建文件树..." -ForegroundColor Cyan
$TreeSHA = Create-Tree -BaseTreeSHA $BranchSHA -Files $ERP_Files
if (-not $TreeSHA) {
    Write-Host "❌ 创建文件树失败" -ForegroundColor Red
    exit 1
}

# 4. 创建提交
Write-Host "💾 创建提交..." -ForegroundColor Cyan
$CommitSHA = Create-Commit -TreeSHA $TreeSHA -ParentSHA $BranchSHA -Message $CommitMessage
if (-not $CommitSHA) {
    Write-Host "❌ 创建提交失败" -ForegroundColor Red
    exit 1
}

# 5. 更新引用
Write-Host "🔄 更新分支引用..." -ForegroundColor Cyan
$Success = Update-Reference -CommitSHA $CommitSHA -BranchName $Branch
if (-not $Success) {
    Write-Host "❌ 更新分支引用失败" -ForegroundColor Red
    exit 1
}

# 6. 创建标签
Write-Host "🏷️ 创建版本标签..." -ForegroundColor Cyan
$TagSHA = Create-Tag -TagName "v5.9.0" -CommitSHA $CommitSHA -Message "AI-STACK V5.9.0版本发布 - ERP模块功能更新"
if ($TagSHA) {
    Write-Host "✅ 标签创建成功: v5.9.0" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ 代码推送完成！" -ForegroundColor Green
Write-Host "📊 提交信息: $CommitMessage" -ForegroundColor Green
Write-Host "🔗 仓库地址: https://github.com/$RepoOwner/$RepoName" -ForegroundColor Green
if ($TagSHA) {
    Write-Host "🏷️ 版本标签: v5.9.0" -ForegroundColor Green
}