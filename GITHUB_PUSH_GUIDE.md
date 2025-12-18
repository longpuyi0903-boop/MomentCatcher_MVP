# GitHub推送详细步骤

## 步骤1：初始化Git仓库

在项目根目录运行：

```powershell
# 初始化git仓库
git init

# 添加所有文件
git add .

# 第一次提交
git commit -m "Initial commit: Moment Catcher MVP"
```

---

## 步骤2：创建GitHub仓库

### 方法A：在GitHub网站创建（推荐）

1. **访问GitHub**
   - 打开 https://github.com
   - 登录你的账号（如果没有，先注册）

2. **创建新仓库**
   - 点击右上角 **"+"** → **"New repository"**
   - 填写仓库信息：
     - **Repository name**: `MomentCatcher_MVP`（或你喜欢的名字）
     - **Description**: `AI Companion for Capturing Moments`（可选）
     - **Visibility**: 选择 **Public**（公开）或 **Private**（私有）
     - ⚠️ **不要勾选** "Add a README file"、"Add .gitignore"、"Choose a license"（因为我们本地已经有了）
   - 点击 **"Create repository"**

3. **复制仓库地址**
   - 创建后，GitHub会显示仓库地址
   - 类似：`https://github.com/你的用户名/MomentCatcher_MVP.git`
   - **复制这个地址**

---

## 步骤3：添加远程仓库并推送

回到PowerShell，运行：

```powershell
# 添加远程仓库（替换为你的GitHub仓库地址）
git remote add origin https://github.com/你的用户名/MomentCatcher_MVP.git

# 查看远程仓库（确认添加成功）
git remote -v

# 推送代码到GitHub（第一次推送）
git branch -M main
git push -u origin main
```

**注意**：如果提示输入用户名和密码：
- 用户名：你的GitHub用户名
- 密码：**不是GitHub密码**，需要使用 **Personal Access Token**（见下方说明）

---

## 步骤4：如果提示需要认证

GitHub现在不允许用密码推送，需要使用 **Personal Access Token**：

### 创建Token：

1. **打开GitHub设置**
   - 点击右上角头像 → **"Settings"**
   - 左侧菜单 → **"Developer settings"**
   - 点击 **"Personal access tokens"** → **"Tokens (classic)"**

2. **生成新Token**
   - 点击 **"Generate new token"** → **"Generate new token (classic)"**
   - 填写：
     - **Note**: `MomentCatcher Push`（描述）
     - **Expiration**: 选择过期时间（建议90天或No expiration）
     - **Select scopes**: 勾选 **`repo`**（完整仓库访问权限）
   - 点击 **"Generate token"**

3. **复制Token**
   - ⚠️ **重要**：Token只会显示一次，立即复制保存！
   - 类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **使用Token推送**
   - 当提示输入密码时，粘贴Token（不是GitHub密码）
   - 或者使用命令：
   ```powershell
   git push -u origin main
   # 用户名：你的GitHub用户名
   # 密码：粘贴Token
   ```

---

## 步骤5：验证推送成功

1. **刷新GitHub页面**
   - 你应该能看到所有文件都上传了

2. **检查文件**
   - 确认 `requirements.txt`、`Procfile`、`run_api.py` 都在仓库中

---

## 常见问题

### Q1: 提示 "fatal: could not read Username"
**解决**：检查远程仓库地址是否正确，或使用SSH方式（见下方）

### Q2: 推送很慢或失败
**解决**：
- 检查网络连接
- 尝试使用SSH方式（需要配置SSH key）

### Q3: 想使用SSH方式（推荐，更安全）

1. **检查是否有SSH key**
   ```powershell
   ls ~/.ssh
   ```
   如果没有 `id_rsa.pub`，需要生成：
   ```powershell
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```

2. **添加SSH key到GitHub**
   - 复制公钥：`cat ~/.ssh/id_rsa.pub`
   - GitHub → Settings → SSH and GPG keys → New SSH key
   - 粘贴公钥并保存

3. **使用SSH地址添加远程仓库**
   ```powershell
   git remote set-url origin git@github.com:你的用户名/MomentCatcher_MVP.git
   git push -u origin main
   ```

---

## 完成后的下一步

推送成功后，你就可以在 Render.com 上部署了：

详细步骤请参考：`RENDER_DEPLOY_GUIDE.md`

---

**需要帮助？** 如果遇到任何问题，告诉我具体的错误信息！

