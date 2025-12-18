# GitHub网页端上传代码（最简单方法）

## 步骤1：在GitHub创建仓库

1. 访问 https://github.com
2. 登录你的账号
3. 点击右上角 **"+"** → **"New repository"**
4. 填写：
   - **Repository name**: `MomentCatcher_MVP`
   - **Description**: `AI Companion for Capturing Moments`（可选）
   - **Visibility**: 选择 **Public** 或 **Private**
   - ⚠️ **不要勾选** "Add a README file"、"Add .gitignore"、"Choose a license"
5. 点击 **"Create repository"**

---

## 步骤2：使用GitHub Desktop（推荐）或网页上传

### 方法A：GitHub Desktop（最简单）⭐

1. **下载GitHub Desktop**
   - 访问：https://desktop.github.com
   - 下载并安装

2. **连接仓库**
   - 打开GitHub Desktop
   - File → Add Local Repository
   - 选择你的项目文件夹：`D:\D盘\AI Agent\MomentCatcher_MVP`
   - 点击 "Publish repository"
   - 选择你刚创建的仓库
   - 点击 "Publish repository"

**完成！** 代码会自动上传到GitHub。

---

### 方法B：网页端直接上传（如果文件不多）

1. **在GitHub仓库页面**
   - 点击 **"uploading an existing file"** 链接

2. **拖拽文件**
   - 直接拖拽项目文件夹中的文件到页面
   - 注意：需要排除 `node_modules`、`__pycache__` 等大文件夹

3. **提交**
   - 填写提交信息：`Initial commit`
   - 点击 **"Commit changes"**

**缺点**：文件多的话比较麻烦，建议用方法A。

---

## 步骤3：验证上传成功

刷新GitHub页面，确认以下文件都在：
- ✅ `requirements.txt`
- ✅ `Procfile`
- ✅ `run_api.py`
- ✅ `api/main.py`
- ✅ `frontend/` 文件夹
- ✅ 其他项目文件

---

## 完成后：在 Render.com 部署

详细步骤请参考：`RENDER_DEPLOY_GUIDE.md`

快速步骤：
1. 访问 https://render.com
2. 用GitHub账号登录
3. "New +" → "Web Service"（后端）和 "Static Site"（前端）
4. 连接 GitHub 仓库 `MomentCatcher_MVP`
5. 配置并部署

---

**推荐：使用GitHub Desktop，最简单！**

