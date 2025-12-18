# Render.com 部署指南

## 🚀 为什么选择 Render？

- ✅ **完全免费**（Web 服务有免费计划）
- ✅ **一键部署**（连接 GitHub）
- ✅ **自动 HTTPS**
- ✅ **稳定地址**（不会变）
- ✅ **支持 Python/FastAPI**
- ✅ **支持静态网站**（可以部署前端）
- ✅ **手机端完美支持**（伪 App 效果）

---

## 步骤1：部署后端（Web Service）

### 1.1 访问 Render
1. 访问 https://render.com
2. 用 GitHub 账号登录（点击 "Get Started for Free"）

### 1.2 创建新的 Web Service
1. 登录后，点击 **"New +"** → **"Web Service"**
2. 选择 **"Build and deploy from a Git repository"**
3. 连接你的 GitHub 账号（如果还没连接）
4. 选择仓库：`MomentCatcher_MVP`

### 1.3 配置 Web Service
填写以下信息：

- **Name**: `moment-catcher-backend`（或任意名称）
- **Region**: 选择离你最近的（如 `Singapore` 或 `Oregon`）
- **Branch**: `main`（或你的主分支）
- **Root Directory**: 留空（项目根目录）
- **Runtime**: `Python 3`
- **Build Command**: 留空（Render 会自动检测）
- **Start Command**: `python run_api.py`

### 1.4 环境变量（可选）
如果后端需要环境变量，在 "Environment Variables" 部分添加。

### 1.5 创建并等待部署
1. 点击 **"Create Web Service"**
2. Render 会自动：
   - 安装依赖（从 `requirements.txt`）
   - 运行 `python run_api.py`
   - 生成 HTTPS 地址

### 1.6 获取后端地址
部署完成后，你会看到类似这样的地址：
```
https://moment-catcher-backend.onrender.com
```
**重要**：这是你的后端地址，复制它！

---

## 步骤2：部署前端（Static Site）

### 2.1 创建新的 Static Site
1. 在 Render  dashboard，点击 **"New +"** → **"Static Site"**
2. 选择仓库：`MomentCatcher_MVP`

### 2.2 配置 Static Site
填写以下信息：

- **Name**: `moment-catcher-frontend`（或任意名称）
- **Branch**: `main`
- **Root Directory**: `frontend`（重要！指定前端文件夹）
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`（构建后的文件夹）

### 2.3 设置环境变量
在 "Environment Variables" 部分，添加：
- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://你的后端地址.onrender.com/api`

例如：
```
VITE_API_BASE_URL=https://moment-catcher-backend.onrender.com/api
```

### 2.4 创建并等待部署
1. 点击 **"Create Static Site"**
2. Render 会自动构建并部署前端

### 2.5 获取前端地址
部署完成后，你会看到类似这样的地址：
```
https://moment-catcher-frontend.onrender.com
```
**这就是你的应用地址！** 手机端访问这个地址即可。

---

## 步骤3：手机端访问（伪 App）

### 方法1：添加到主屏幕（iOS Safari）
1. 在 Safari 打开前端地址
2. 点击底部的 **分享按钮**（方框+向上箭头）
3. 选择 **"添加到主屏幕"**
4. 给应用命名（如 "Moment Catcher"）
5. 点击 **"添加"**

### 方法2：添加到主屏幕（Android Chrome）
1. 在 Chrome 打开前端地址
2. 点击右上角 **三个点** → **"添加到主屏幕"**
3. 给应用命名
4. 点击 **"添加"**

### 方法3：分享链接给朋友
直接把前端地址分享给朋友，他们也可以添加到主屏幕！

---

## ⚠️ 注意事项

### Render 免费计划的限制
- **Web Service** 会自动休眠（15 分钟无活动后）
- 首次访问可能需要 **30-60 秒** 唤醒
- 每月有免费小时数限制（通常足够个人使用）

### 如果需要保持后端常驻
- 可以考虑升级到付费计划
- 或者使用免费的 "Health Check" 功能定期 ping 后端

---

## 🎉 完成！

现在你的应用已经完全部署到云端：
- ✅ 后端：`https://xxx.onrender.com/api`
- ✅ 前端：`https://xxx.onrender.com`
- ✅ 手机端可以随时访问
- ✅ 你不需要开电脑

---

## 需要帮助？

如果遇到部署问题，检查：
1. 构建日志（Build Logs）中的错误信息
2. 运行日志（Runtime Logs）中的错误信息
3. 环境变量是否正确设置

