# 前端开发设置指南

## ✅ 已完成的工作

### 1. ASR API 端点（后端）
- ✅ 添加了 `POST /api/asr` 端点
- ✅ 支持音频文件上传（wav, mp3, m4a等）
- ✅ 调用现有的 `asr_engine.py`

### 2. React 项目结构
- ✅ 创建了完整的 React + Vite 项目
- ✅ 组件结构：
  - `LandingPage` - 登录页面
  - `MainInterface` - 主界面（Tab导航）
  - `ChatInterface` - 对话界面（**文字输入已实现**）
  - `MemoriesView` - Memories 列表
  - `SettingsView` - 设置页面

### 3. 基础功能（文字输入）
- ✅ 初始化连接
- ✅ 开始新 Moment
- ✅ 发送消息（文字）
- ✅ 接收回复
- ✅ 语音播放（TTS）
- ✅ 保存 Moment
- ✅ 查看 Memories
- ✅ 查看风格画像

---

## 🚀 启动步骤

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 启动后端（如果还没启动）

```bash
# 在项目根目录
python run_api.py
```

后端运行在：`http://localhost:8000`

### 3. 启动前端

```bash
cd frontend
npm run dev
```

前端运行在：`http://localhost:3000`

### 4. 访问应用

打开浏览器访问：`http://localhost:3000`

---

## 📋 当前功能状态

### ✅ 已实现（文字输入版本）
- Landing Page（名字输入）
- 对话界面（文字输入 + 发送）
- 消息显示（用户 + Agent）
- 语音播放（TTS）
- Moment 管理（开始/保存）
- Memories 列表
- 设置页面

### ⏳ 待实现（下一步）
- **语音识别（ASR）**
  - 麦克风录音 UI
  - 音频上传
  - 识别结果显示
- **视觉效果**
  - 粒子背景
  - Moment Card 优化
  - 3D 星图

---

## 🔧 开发顺序

### Phase 1: 基础功能 ✅（已完成）
- [x] React 项目搭建
- [x] Landing Page
- [x] 文字输入对话
- [x] Moment 管理
- [x] Memories 列表

### Phase 2: 语音识别 ⏳（下一步）
- [ ] 录音按钮 UI
- [ ] 麦克风权限请求
- [ ] 音频录制（MediaRecorder）
- [ ] 音频上传到 `/api/asr`
- [ ] 识别结果显示
- [ ] 自动填入输入框

### Phase 3: 视觉效果 ⏳
- [ ] 粒子背景
- [ ] Moment Card 视觉
- [ ] 3D 星图

---

## 📝 注意事项

1. **后端必须运行**：前端依赖后端 API，确保 `run_api.py` 正在运行
2. **CORS 配置**：后端已配置允许所有来源（开发环境）
3. **API 代理**：Vite 配置了代理，前端 `/api` 请求会自动转发到 `http://localhost:8000`
4. **音频路径**：TTS 返回的音频路径需要正确处理（已修复）

---

## 🐛 常见问题

### 1. 前端无法连接后端
- 检查后端是否运行在 `http://localhost:8000`
- 检查浏览器控制台错误信息

### 2. CORS 错误
- 后端已配置 CORS，如果还有问题，检查后端日志

### 3. 音频无法播放
- 检查音频路径是否正确
- 检查浏览器是否支持音频格式

---

## 🎯 下一步

1. **测试基础功能**：确保文字输入版本正常工作
2. **添加语音识别**：实现录音和 ASR 集成
3. **添加视觉效果**：粒子、3D 等

---

## 📝 最近更新（2025-01-XX）

### UI设计优化
- ✅ 右侧浮动操作按钮1:1复刻参考代码（图标形式，hover显示文字）
- ✅ 底部主按钮移除背景填充（透明背景）
- ✅ Settings按钮图标替换为参考代码中的Settings图标
- ✅ Echoes页文字样式1:1复刻参考代码（字体、大小、行间距）

详细更新内容请查看：`SESSION_PROGRESS_SUMMARY.md`


