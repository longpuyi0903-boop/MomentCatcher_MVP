# MiniMax 语音克隆故障排查指南

## 🔍 当前问题

错误码 `2013 - invalid params` 表示 API 参数格式不正确。

## 📋 可能的原因

1. **API 端点不正确**
   - 当前使用的端点可能不是正确的语音克隆端点
   - 需要查看 MiniMax 官方文档确认

2. **参数格式不正确**
   - 参数名称可能不对（如 `group_id`, `voice_name` 等）
   - 可能需要使用不同的参数格式

3. **文件上传方式不正确**
   - 可能需要先上传文件到文件服务，然后使用文件 ID
   - 或者需要使用 base64 编码而不是 multipart

4. **文件格式或大小限制**
   - 文件格式可能不支持（虽然 m4a 应该支持）
   - 文件大小可能超出限制

## 🔧 解决步骤

### 步骤 1：查看 MiniMax 官方文档

1. 访问 [MiniMax 开放平台](https://www.minimax.io/)
2. 登录你的账号
3. 查找 **语音克隆** 或 **Voice Clone** 相关的 API 文档
4. 确认：
   - 正确的 API 端点 URL
   - 正确的请求参数格式
   - 文件上传方式

### 步骤 2：检查 API 端点

当前代码使用的端点：
```
https://api.minimax.chat/v1/text_to_speech/voice_clone
```

可能的其他端点：
- `https://api.minimax.chat/v1/voice_clone`
- `https://api.minimax.chat/v1/voices`
- `https://api.minimax.chat/v1/text_to_speech/voices`

你可以通过环境变量修改：
```bash
# 在 .env 文件中添加
MINIMAX_CLONE_API_URL=https://api.minimax.chat/v1/正确的端点
```

### 步骤 3：查看完整错误响应

运行脚本后，会输出完整的错误响应，包含：
- 错误码
- 错误消息
- 可能的参数要求

### 步骤 4：根据文档调整代码

如果找到了正确的 API 格式，需要修改 `minimax_voice_clone.py` 中的：

1. **API 端点**（第 29-32 行）
2. **请求参数格式**（第 64-91 行）
3. **文件上传方式**（multipart vs JSON）

## 📝 临时解决方案

如果暂时无法找到正确的 API 格式，可以：

1. **使用预置音色**
   - MiniMax 提供 300+ 种预置音色
   - 可以在 `backend/audio/tts_engine.py` 中修改 `DEFAULT_VOICE_ID`

2. **联系 MiniMax 技术支持**
   - 询问语音克隆 API 的正确格式
   - 获取 API 文档链接

3. **查看 API 响应**
   - 运行脚本后查看完整的错误响应
   - 可能包含有用的提示信息

## 🔗 相关资源

- [MiniMax 开放平台](https://www.minimax.io/)
- [MiniMax API 文档](https://platform.minimaxi.com/docs)
- 项目中的 `minimax_voice_clone.py` - 语音克隆脚本

## 💡 提示

如果找到了正确的 API 格式，请告诉我，我会帮你更新代码！

