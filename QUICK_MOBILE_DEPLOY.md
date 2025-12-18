# 快速移动端部署指南（让朋友试用）

**目标：** 让外地朋友在手机上试用，步骤最少，速度最快

---

## ✅ 已完成：伪App全屏配置

已添加以下配置，实现全屏显示效果：
- ✅ 全屏meta标签（`apple-mobile-web-app-capable`）
- ✅ 动态视口高度（`100dvh`）
- ✅ 触摸优化（`touch-action: manipulation`）
- ✅ 安全区域适配（iPhone X+）

---

## 🚀 快速部署方案（3选1，最快5分钟）

### 方案1：Netlify（推荐，最简单）⭐

**步骤：**

1. **构建项目**
```bash
cd frontend
npm run build
```

2. **部署到Netlify**
   - 访问 [netlify.com](https://netlify.com)
   - 注册/登录（可以用GitHub账号）
   - 点击 "Add new site" → "Deploy manually"
   - 拖拽 `frontend/dist` 文件夹到页面
   - 等待部署完成（30秒）
   - 获得链接：`https://xxxxx.netlify.app`

3. **分享链接给朋友**
   - 朋友在手机浏览器打开链接
   - 点击浏览器菜单 → "添加到主屏幕"（可选，更像App）
   - 全屏显示，像App一样使用

**优点：** 
- ✅ 免费
- ✅ 自动HTTPS
- ✅ 速度快
- ✅ 步骤最少

---

### 方案2：Vercel（同样简单）

**步骤：**

1. **安装Vercel CLI**
```bash
npm i -g vercel
```

2. **部署**
```bash
cd frontend
npm run build
vercel
```
- 按提示操作（全部默认即可）
- 获得链接：`https://xxxxx.vercel.app`

3. **分享链接给朋友**

**优点：** 
- ✅ 免费
- ✅ 自动HTTPS
- ✅ 全球CDN

---

### 方案3：GitHub Pages（需要GitHub账号）

**步骤：**

1. **安装gh-pages**
```bash
cd frontend
npm install --save-dev gh-pages
```

2. **修改package.json**
```json
{
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  },
  "homepage": "https://你的用户名.github.io/仓库名"
}
```

3. **部署**
```bash
npm run deploy
```

4. **访问**
- `https://你的用户名.github.io/仓库名`

---

## 📱 朋友使用指南（发给朋友）

1. **在手机浏览器中打开链接**（Chrome/Safari都行）

2. **全屏使用**：
   - iOS Safari：点击底部分享按钮 → "加入主屏幕"
   - Android Chrome：点击右上角菜单 → "添加到主屏幕"
   - 或者直接在浏览器中使用（已经是全屏显示）

3. **使用体验**：
   - 全屏显示，无浏览器地址栏
   - 触摸优化，像原生App
   - 支持横竖屏切换

---

## ⚠️ 注意事项

### 后端API问题
**重要：** 如果后端运行在 `localhost:8000`，朋友无法访问！

**解决方案：**

1. **临时方案（快速测试）**：
   - 使用内网穿透工具（如ngrok, frp）
   ```bash
   # 安装ngrok
   # 运行后端后，执行：
   ngrok http 8000
   # 获得公网地址，如：https://xxxx.ngrok.io
   # 修改前端API地址为这个地址
   ```

2. **生产方案**：
   - 部署后端到服务器（云服务器、Heroku等）
   - 修改前端API配置为后端公网地址

---

## 🔧 如果后端在本地，修改API地址

修改 `frontend/vite.config.js`：
```js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://你的后端公网地址:8000', // 改为公网地址
        changeOrigin: true,
      }
    }
  },
  // 构建时也使用公网地址
  define: {
    'process.env.API_URL': JSON.stringify('https://你的后端公网地址:8000')
  }
})
```

---

## ✅ 完成检查清单

部署前检查：
- [x] 全屏meta标签已添加
- [x] CSS全屏样式已添加
- [ ] 前端已构建（`npm run build`）
- [ ] 已部署到服务器（Netlify/Vercel/GitHub Pages）
- [ ] 后端可访问（本地需内网穿透，或部署到服务器）
- [ ] 朋友可以访问链接

---

## 🎯 最快方案总结

**推荐：Netlify + ngrok（后端内网穿透）**

1. **前端部署（2分钟）**：
   ```bash
   cd frontend
   npm run build
   # 拖拽 dist 文件夹到 Netlify
   ```

2. **后端内网穿透（1分钟）**：
   ```bash
   ngrok http 8000
   # 复制地址，修改前端API配置
   ```

3. **分享链接（1分钟）**：
   - 把Netlify链接发给朋友
   - 完成！

**总计：5分钟内完成！**

---

**文档版本：** v1  
**创建日期：** 2025-01-XX  
**状态：** ✅ 伪App配置已完成，待部署

