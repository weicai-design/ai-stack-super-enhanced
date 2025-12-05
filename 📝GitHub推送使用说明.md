# 📝 GitHub推送使用说明

**更新时间**: 2025-01-XX

---

## 🚀 快速推送

### 方式1：使用HTTPS推送脚本（推荐）⭐

```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/push_with_https.sh
```

脚本会提示您输入：
1. **GitHub用户名**
2. **Personal Access Token**（输入时不会显示）

---

## 🔑 获取Personal Access Token

如果还没有Token，请按以下步骤创建：

1. **访问GitHub Token页面**:
   ```
   https://github.com/settings/tokens
   ```

2. **点击 "Generate new token (classic)"**

3. **设置Token信息**:
   - Note（备注）: 例如 "AI-STACK推送"
   - Expiration（过期时间）: 选择合适的时间（建议90天或自定义）
   - Select scopes（权限）: 勾选 **`repo`**（全部仓库权限）

4. **点击 "Generate token"**

5. **复制Token**（只显示一次，请立即保存）

---

## 📋 推送步骤

### 步骤1：运行推送脚本
```bash
./scripts/push_with_https.sh
```

### 步骤2：输入凭据
- 输入GitHub用户名
- 输入Personal Access Token（输入时不会显示，这是正常的）

### 步骤3：确认推送
- 确认信息无误后输入 `y`

### 步骤4：选择是否保存凭据
- 如果选择保存，下次推送时不需要重新输入
- 凭据保存在 `~/.git-credentials`（已加密）

---

## 🔐 安全提示

1. **Token安全**:
   - Token相当于密码，请妥善保管
   - 不要将Token提交到代码仓库
   - 如果Token泄露，立即在GitHub上删除并重新生成

2. **凭据存储**:
   - 如果选择保存凭据，文件权限已设置为600（仅所有者可读写）
   - 建议定期更新Token

---

## ⚙️ 其他推送方式

### 方式2：手动HTTPS推送

```bash
cd /Users/ywc/ai-stack-super-enhanced

# 切换到HTTPS
git remote set-url origin https://github.com/weicai-design/ai-stack-super-enhanced.git

# 推送（会提示输入用户名和Token）
git push origin main
```

### 方式3：配置SSH密钥（一次性配置）

如果您想使用SSH方式（不需要每次输入密码），可以配置SSH密钥：

```bash
# 1. 检查是否已有SSH密钥
ls -la ~/.ssh/id_*

# 2. 如果没有，生成新的SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按提示操作，可以设置密码保护密钥

# 3. 启动ssh-agent
eval "$(ssh-agent -s)"

# 4. 添加SSH密钥到ssh-agent
ssh-add ~/.ssh/id_ed25519

# 5. 复制公钥
cat ~/.ssh/id_ed25519.pub

# 6. 将公钥添加到GitHub
# 访问: https://github.com/settings/ssh/new
# 粘贴公钥并保存

# 7. 测试连接
ssh -T git@github.com

# 8. 切换回SSH方式
git remote set-url origin git@github.com:weicai-design/ai-stack-super-enhanced.git

# 9. 推送
git push origin main
```

---

## ❓ 常见问题

### Q1: 提示 "Permission denied"
**A**: Token可能没有 `repo` 权限，请重新生成Token并确保勾选了 `repo` 权限。

### Q2: 提示 "Token已过期"
**A**: Token已过期，请重新生成新的Token。

### Q3: 推送时提示 "remote: Invalid username or password"
**A**: 
- 检查用户名是否正确
- 确认使用的是Token而不是密码
- 确认Token有正确的权限

### Q4: 如何查看当前远程地址？
```bash
git remote -v
```

### Q5: 如何清除保存的凭据？
```bash
rm ~/.git-credentials
git config --unset credential.helper
```

---

## 📊 当前状态

- ✅ **本地提交**: 已完成（提交ID: 054a08d）
- ✅ **文件暂存**: 已完成
- ⏳ **远程推送**: 等待执行

---

**提示**: 运行 `./scripts/push_with_https.sh` 开始推送！



























