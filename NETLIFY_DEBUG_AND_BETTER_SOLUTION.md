# 问题排查 + 更好的解决方案

## 当前问题：404错误

### 1. 查看Netlify错误日志

**方法1：在Netlify查看**
1. 点击左侧菜单 **"Logs & metrics"** → **"Functions"** 或 **"Deploys"**
2. 点击最新的部署记录
3. 查看构建日志和运行时日志

**方法2：在浏览器控制台查看**
- 打开网站，按F12打开开发者工具
- 查看 **Console** 和 **Network** 标签
- 404错误会显示具体请求的URL

---

### 2. 可能的原因

#### 原因A：环境变量未生效
- 检查：Netlify → Site settings → Environment variables
- 确认 `VITE_API_BASE_URL` 已设置
- **重要**：环境变量需要**重新部署**才会生效

#### 原因B：ngrok地址变化
- 免费版ngrok每次重启地址会变
- 需要更新Netlify环境变量并重新部署

#### 原因C：后端未运行
- 确认 `python run_api.py` 正在运行
- 确认ngrok正在运行

---

## 🚀 更好的解决方案（推荐）

### 方案：后端部署到云端（无需开电脑）

**推荐平台：Railway（最简单）** ⭐

#### 为什么选择Railway：
- ✅ 免费额度（每月$5，足够个人使用）
- ✅ 一键部署（连接GitHub）
- ✅ 自动HTTPS
- ✅ 稳定地址（不会变）
- ✅ 支持Python/FastAPI
- ✅ 无需一直开电脑

---

## Railway部署步骤（10分钟）

### 步骤1：准备代码
确保项目有 `requirements.txt` 和 `Procfile`

### 步骤2：部署到Railway
1. 访问 https://railway.app
2. 用GitHub账号登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你的仓库
5. Railway会自动检测Python项目并部署

### 步骤3：设置环境变量
- Railway会自动生成HTTPS地址（类似：`https://xxx.up.railway.app`）
- 这个地址是固定的，不会变

### 步骤4：更新Netlify环境变量
- 在Netlify设置 `VITE_API_BASE_URL` = `https://xxx.up.railway.app/api`
- 重新部署前端

---

## 快速临时方案（如果不想部署后端）

### 方案：使用ngrok的付费版或稳定地址
- ngrok付费版提供固定地址
- 但需要付费（$8/月）

### 或者：用其他内网穿透工具
- **cloudflare tunnel**（免费，更稳定）
- **localtunnel**（免费，npm安装）

---

## 建议

**最快解决当前问题**：
1. 检查Netlify环境变量是否正确
2. 确认ngrok和后端都在运行
3. 重新部署前端（确保环境变量生效）

**长期方案**：
- 后端部署到Railway（10分钟，一次部署，永久可用）
- 前端继续用Netlify（已经部署好了）
- 这样朋友随时可以访问，你不需要开电脑

---

## Railway vs 当前方案对比

| 方案 | 当前（本地+ngrok） | Railway |
|------|------------------|---------|
| 需要开电脑 | ✅ 是 | ❌ 否 |
| 地址稳定性 | ❌ 会变 | ✅ 固定 |
| 部署难度 | ✅ 简单 | ✅ 简单 |
| 费用 | 免费 | 免费额度 |
| 维护 | 需要保持运行 | 自动运行 |

**结论：Railway更适合让朋友长期使用！**

