# Netlify环境变量配置（使用ngrok后端）

## 步骤1：获取ngrok地址

1. 启动后端：`python run_api.py`
2. 运行ngrok：`ngrok http 8000`
3. 复制HTTPS地址，例如：`https://xxxx-xx-xx-xx-xx.ngrok-free.app`

## 步骤2：在Netlify设置环境变量

1. 在Netlify项目页面，点击 **"Site settings"**（站点设置）
2. 点击左侧 **"Environment variables"**（环境变量）
3. 点击 **"Add a variable"**（添加变量）
4. 添加：
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://你的ngrok地址/api`
   - 例如：`https://xxxx-xx-xx-xx-xx.ngrok-free.app/api`
5. 点击 **"Save"**

## 步骤3：重新部署

1. 重新构建前端（确保代码已更新）
2. 在Netlify页面，点击 **"Production deploys"** 卡片
3. 再次拖拽 `frontend/dist` 文件夹
4. 或点击 **"Trigger deploy"** → **"Deploy site"**

## 完成！

现在前端可以访问你的本地后端了。

**注意**：每次重启ngrok，地址会变，需要更新Netlify的环境变量并重新部署。

