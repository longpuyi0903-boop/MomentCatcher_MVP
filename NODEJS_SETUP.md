# Node.js 和 npm 安装指南

## 问题
你的系统提示 `npm` 命令未找到，说明还没有安装 Node.js。

## 解决方案

### Windows 系统

#### 方法 1：官网下载（推荐）
1. 访问 Node.js 官网：https://nodejs.org/
2. 下载 LTS 版本（推荐，稳定）
3. 运行安装程序
4. 安装时选择"Add to PATH"（添加到环境变量）
5. 安装完成后重启终端

#### 方法 2：使用包管理器
如果你有 Chocolatey：
```powershell
choco install nodejs
```

或者使用 Winget：
```powershell
winget install OpenJS.NodeJS.LTS
```

### 验证安装
安装完成后，在**新的终端**中运行：
```powershell
node --version
npm --version
```

应该显示版本号，例如：
```
v20.10.0
10.2.3
```

### 如果还是不行
1. **检查环境变量**
   - 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   - 在 Path 中添加 Node.js 安装路径（通常是 `C:\Program Files\nodejs\`）

2. **重启终端**
   - 关闭所有 PowerShell 窗口
   - 重新打开终端

3. **检查安装路径**
   - Node.js 默认安装在 `C:\Program Files\nodejs\`
   - 确认该目录下有 `node.exe` 和 `npm.cmd`

---

## 安装完成后

### 1. 安装前端依赖
```powershell
cd frontend
npm install
```

### 2. 启动开发服务器
```powershell
npm run dev
```

前端将在 `http://localhost:3000` 启动

---

## 注意事项

- **Node.js 版本**：建议使用 LTS 版本（长期支持版）
- **npm 版本**：Node.js 自带 npm，无需单独安装
- **网络问题**：如果 npm install 很慢，可以使用国内镜像：
  ```powershell
  npm config set registry https://registry.npmmirror.com
  ```


