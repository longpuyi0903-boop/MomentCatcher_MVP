# 运行ngrok步骤

## 步骤1：确保后端正在运行

在另一个PowerShell窗口运行：
```powershell
python run_api.py
```

确保看到类似：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 步骤2：运行ngrok

在当前PowerShell窗口（在 `D:\D盘\Program Files>` 目录下）运行：

```powershell
.\ngrok.exe http 8000
```

或者从项目目录运行：
```powershell
"D:\D盘\Program Files\ngrok.exe" http 8000
```

---

## 步骤3：复制HTTPS地址

运行后会显示类似：

```
Session Status                online
Forwarding                    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
```

**复制这个HTTPS地址**：`https://xxxx-xx-xx-xx-xx.ngrok-free.app`

---

## 步骤4：在Netlify设置环境变量

1. 在Netlify项目页面，点击左侧 **"Site settings"**
2. 点击 **"Environment variables"**
3. 点击 **"Add a variable"**
4. 填写：
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://xxxx-xx-xx-xx-xx.ngrok-free.app/api`
5. 点击 **"Save"**

---

## 步骤5：重新部署前端

1. 重新构建：
```powershell
cd frontend
npm run build
```

2. 在Netlify的 "Production deploys" 卡片中，再次拖拽 `frontend/dist` 文件夹

---

**完成！** 现在朋友可以通过Netlify链接访问你的应用，并通过ngrok连接本地后端。

