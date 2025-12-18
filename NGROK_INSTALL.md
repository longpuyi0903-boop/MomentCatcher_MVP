# ngrok 安装指南（Windows）

## 方法1：直接下载（最快，推荐）⭐

1. **下载ngrok**
   - 访问：https://ngrok.com/download
   - 选择 Windows 版本下载
   - 或直接下载：https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip

2. **解压到任意文件夹**
   - 解压 `ngrok.exe` 到任意位置，例如：`C:\ngrok\ngrok.exe`

3. **添加到系统PATH（可选，推荐）**
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑"
   - 点击"新建"，添加ngrok所在文件夹路径（例如：`C:\ngrok`）
   - 点击"确定"保存

4. **重启PowerShell，然后运行**
   ```powershell
   ngrok http 8000
   ```

---

## 方法2：不添加到PATH（临时使用）

如果不想修改PATH，可以直接运行：

```powershell
# 假设ngrok.exe在 C:\ngrok\ngrok.exe
C:\ngrok\ngrok.exe http 8000

# 或者先cd到ngrok所在文件夹
cd C:\ngrok
.\ngrok.exe http 8000
```

---

## 完成后的操作

运行成功后，你会看到类似这样的输出：

```
Session Status                online
Account                       your-email@example.com
Forwarding                    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
```

复制 `https://xxxx-xx-xx-xx-xx.ngrok-free.app` 这个地址，然后：
1. 在Netlify设置环境变量：`VITE_API_BASE_URL` = `https://xxxx-xx-xx-xx-xx.ngrok-free.app/api`
2. 重新部署前端

---

**快速链接：** https://ngrok.com/download

