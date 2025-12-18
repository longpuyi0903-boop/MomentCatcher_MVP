# Render 后端环境变量设置指南

## 🔑 必需的环境变量

你的后端需要以下环境变量才能正常运行：

### 必需变量：

1. **`ALIYUN_QWEN_KEY`**
   - **说明**：阿里云通义千问 API 密钥
   - **用途**：用于 LLM 对话和语音识别（ASR）
   - **必需性**：✅ **必需**（没有这个后端无法启动）

2. **`ALIYUN_DASHSCOPE_API_KEY`**（可选）
   - **说明**：阿里云 DashScope API 密钥（TTS 使用）
   - **用途**：语音合成（TTS）
   - **必需性**：⚠️ 可选（如果没有，TTS 功能可能不可用）

---

## 📝 在 Render 上设置环境变量

### 步骤1：进入后端服务设置
1. 在 Render dashboard，找到你的 **Web Service**（后端）
2. 点击服务名称进入详情页

### 步骤2：打开环境变量设置
1. 点击顶部导航栏的 **"Environment"** 标签
2. 或者点击左侧边栏的 **"Environment"** 选项

### 步骤3：添加环境变量
1. 点击 **"Add Environment Variable"** 按钮
2. 添加以下变量：

   **变量1：**
   - **Key**: `ALIYUN_QWEN_KEY`
   - **Value**: 你的阿里云 API 密钥（从 `.env` 文件或阿里云控制台获取）

   **变量2（可选）：**
   - **Key**: `ALIYUN_DASHSCOPE_API_KEY`
   - **Value**: 你的 DashScope API 密钥（如果与上面不同）

3. 点击 **"Save Changes"**

### 步骤4：重新部署
设置完环境变量后，Render 会自动触发重新部署。如果没有自动部署：
1. 点击 **"Manual Deploy"** → **"Deploy latest commit"**
2. 等待部署完成（约 1-2 分钟）

---

## ✅ 验证部署是否成功

### 1. 检查部署日志
在 Render dashboard：
- 点击后端服务的 **"Logs"** 标签
- 查看是否有错误信息

**正常情况应该看到：**
```
🌟 Moment Catcher - FastAPI Backend
📝 API 端点:
   ✅ POST /api/init - 初始化连接
   ...
📚 API 文档: http://0.0.0.0:PORT/docs
🔗 API 地址: http://0.0.0.0:PORT
Application startup complete.
```

**如果有错误，可能看到：**
```
❌ ALIYUN_QWEN_KEY 未设置
EnvironmentError: ALIYUN_QWEN_KEY not found in .env
```

### 2. 测试 API 端点
部署成功后，你会得到一个后端地址，例如：
```
https://your-backend-name.onrender.com
```

测试方法：
- 访问 `https://your-backend-name.onrender.com/docs`（应该能看到 API 文档页面）
- 或者访问 `https://your-backend-name.onrender.com/api/init`（应该返回 JSON 响应）

---

## 🔍 排查问题

### 问题1：后端启动失败
**症状**：部署日志显示 `EnvironmentError` 或 "ALIYUN_QWEN_KEY not found"

**解决方法**：
1. 检查环境变量是否已正确设置
2. 确认变量名称拼写正确（大小写敏感）
3. 确认变量值没有多余空格
4. 点击 "Manual Deploy" 重新部署

### 问题2：后端一直显示 "Building" 或 "Deploying"
**症状**：部署状态一直不变成 "Live"

**解决方法**：
1. 检查构建日志（Build Logs）是否有错误
2. 检查运行日志（Runtime Logs）是否有错误
3. 确认 `requirements.txt` 和 `Procfile` 配置正确
4. 如果卡住超过 10 分钟，尝试手动取消并重新部署

### 问题3：后端地址无法访问
**症状**：访问后端地址返回 404 或超时

**解决方法**：
1. 确认服务状态是 "Live"（绿色）
2. 确认使用的是 HTTPS 地址（不是 HTTP）
3. 检查 CORS 配置（代码中已配置允许所有来源）
4. 检查防火墙或网络问题

---

## 📌 重要提示

1. **不要将 API 密钥提交到 Git**
   - 确保 `.env` 文件在 `.gitignore` 中
   - 只在 Render 的环境变量中设置密钥

2. **环境变量生效需要重新部署**
   - 修改环境变量后，必须重新部署才能生效
   - Render 通常会自动触发部署

3. **免费计划的服务会自动休眠**
   - 如果 15 分钟没有请求，服务会进入休眠状态
   - 下次访问需要 30-60 秒唤醒时间

---

## 🎯 下一步

设置完环境变量并成功部署后端后：
1. 复制后端地址（例如：`https://your-backend-name.onrender.com`）
2. 在前端的环境变量中设置 `VITE_API_BASE_URL` = `https://your-backend-name.onrender.com/api`
3. 重新部署前端

