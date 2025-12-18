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

**推荐平台：Render.com（完全免费，支持伪App）** ⭐

#### 为什么选择 Render.com：
- ✅ 完全免费（Web 服务免费计划）
- ✅ 一键部署（连接GitHub）
- ✅ 自动HTTPS
- ✅ 稳定地址（不会变）
- ✅ 支持Python/FastAPI
- ✅ 支持静态网站（可以部署前端）
- ✅ 手机端完美支持（伪App效果）
- ✅ 无需一直开电脑

---

## Render.com 部署步骤（15分钟）

详细步骤请参考：`RENDER_DEPLOY_GUIDE.md`

### 快速概述：
1. 部署后端（Web Service）：连接 GitHub → 配置 → 获取后端地址
2. 部署前端（Static Site）：连接 GitHub → 配置环境变量 → 获取前端地址
3. 手机端访问：添加到主屏幕即可

### 步骤4：更新前端环境变量
- 在 Render Static Site 设置 `VITE_API_BASE_URL` = `https://你的后端地址.onrender.com/api`
- Render 会自动重新构建

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
- 后端和前端都部署到 Render.com（15分钟，一次部署，永久可用）
- 或者后端用 Render，前端继续用 Netlify
- 这样朋友随时可以访问，你不需要开电脑

---

## Render.com vs 当前方案对比

| 方案 | 当前（本地+ngrok） | Render.com |
|------|------------------|---------|
| 需要开电脑 | ✅ 是 | ❌ 否 |
| 地址稳定性 | ❌ 会变 | ✅ 固定 |
| 部署难度 | ✅ 简单 | ✅ 简单 |
| 费用 | 免费 | 免费额度 |
| 维护 | 需要保持运行 | 自动运行 |

**结论：Railway更适合让朋友长期使用！**

