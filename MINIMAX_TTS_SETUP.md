# MiniMax Speech-2.6-Turbo TTS 配置指南

## 📋 概述

本项目已切换到 **MiniMax Speech-2.6-Turbo** 语音合成引擎，支持超低延迟（<250ms）和丰富的情感表达。

## 🔑 环境变量配置

### 必需的环境变量

在项目根目录的 `.env` 文件中添加以下配置：

```env
# MiniMax API 配置
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_group_id_here
```

### 如何获取 API Key 和 Group ID

1. **注册 MiniMax 账号**
   - 访问 [MiniMax 开放平台](https://www.minimax.io/)
   - 注册并登录账号

2. **创建应用并获取 API Key**
   - 在控制台创建新应用
   - 获取 API Key（类似：`sk-xxxxxxxxxxxxx`）

3. **获取 Group ID**
   - 在 MiniMax 控制台中找到你的 Group ID
   - 通常是一个字符串标识符

### 环境变量说明

- `MINIMAX_API_KEY`: MiniMax API 密钥，用于身份验证
- `MINIMAX_GROUP_ID`: MiniMax 组织/组 ID，某些 API 需要此参数

## 🎵 音色配置

### 默认音色

当前默认音色为 `female-shaonv`（少女音色）。你可以在 `backend/audio/tts_engine.py` 中修改 `DEFAULT_VOICE_ID` 来更改默认音色。

### 可用音色列表

MiniMax 提供 300+ 种预置音色，包括：
- `female-shaonv` - 少女音色
- `female-qingxin` - 清新女声
- `male-wennuan` - 温暖男声
- 等等...

具体音色列表请参考 [MiniMax API 文档](https://platform.minimaxi.com/docs/api-reference/speech-t2a-intro)

## 🎤 语音克隆功能

MiniMax 支持语音克隆功能，只需提供 **10-30 秒** 的音频样本即可完美复刻声音。

### 使用语音克隆

1. **准备音频文件**
   - 格式：wav, mp3, m4a 等
   - 时长：建议 10-30 秒
   - 质量：清晰、无背景噪音

2. **运行克隆脚本**

```bash
python minimax_voice_clone.py
```

3. **选择克隆方式**
   - 选项 1：从本地文件克隆（推荐）
   - 选项 2：从 URL 克隆（如果 API 支持）

4. **输入信息**
   - 音频文件路径或 URL
   - 音色名称（可选）

5. **使用克隆的音色**

克隆成功后，音色 ID 会自动保存到 `minimax_voice_id.txt`，TTS 引擎会自动加载。

你也可以手动指定：

```python
from backend.audio.tts_engine import text_to_speech

# 使用克隆的音色
audio_path = text_to_speech(
    text="你好，这是测试",
    voice="your_cloned_voice_id"  # 使用克隆的音色 ID
)
```

### 注意事项

- 音频文件建议使用清晰的人声，避免背景音乐和噪音
- 克隆过程可能需要 10-30 秒
- 克隆的音色 ID 会保存到 `minimax_voice_id.txt`
- 如果 API 端点不正确，可能需要根据官方文档调整 `MINIMAX_CLONE_API_URL`

## 🚀 使用方法

### 基本调用

```python
from backend.audio.tts_engine import text_to_speech

# 基本调用
audio_path = text_to_speech("你好，这是测试文本")

# 自定义音色和参数
audio_path = text_to_speech(
    text="你好，这是测试文本",
    voice="female-qingxin",  # 自定义音色
    speed=1.2,  # 语速（0.5-2.0）
    emotion="friendly"  # 情感参数
)
```

### 参数说明

- `text` (str): 要转换的文本内容
- `voice` (str, 可选): 音色 ID，默认使用 `DEFAULT_VOICE_ID`
- `save_path` (str, 可选): 保存路径，默认使用 `audio_outputs/latest_reply.wav`
- `speed` (float, 可选): 语速，范围 0.5-2.0，默认 1.0
- `emotion` (str, 可选): 情感参数，可选值：`neutral`, `friendly`, `happy`, `sad`, `excited` 等

## 🧪 测试

运行测试脚本：

```bash
python backend/audio/tts_engine.py
```

## ⚠️ 注意事项

1. **API 端点**: 如果遇到 API 调用失败，请检查：
   - API Key 是否正确
   - Group ID 是否正确
   - 网络连接是否正常
   - API 端点地址是否正确（可能需要根据官方文档调整）

2. **API 响应格式**: MiniMax API 的响应格式可能因版本而异，如果遇到解析错误，请检查：
   - 响应中是否包含 `audio` 字段（base64 编码）
   - 响应中是否包含 `audio_url` 字段（需要下载）
   - 响应是否直接返回音频流

3. **费用**: MiniMax Speech-2.6-Turbo 按字符数计费，请注意使用量

## 📚 相关文档

- [MiniMax 开放平台](https://www.minimax.io/)
- [MiniMax Speech API 文档](https://platform.minimaxi.com/docs/api-reference/speech-t2a-intro)
- [MiniMax Python SDK](https://github.com/minimax-ai/minimax-python)（如果有）

## 🔄 从阿里云 TTS 迁移

如果你之前使用的是阿里云 DashScope TTS，迁移步骤：

1. ✅ 已更新 `backend/audio/tts_engine.py` - 完成
2. ✅ 已更新 `requirements.txt` - 完成
3. ⏳ 配置环境变量（`.env` 文件）
4. ⏳ 测试 TTS 功能
5. ⏳ 根据实际 API 响应格式调整代码（如果需要）

## 🐛 故障排查

### 问题：API 调用返回 401 错误
**解决**: 检查 `MINIMAX_API_KEY` 是否正确设置

### 问题：API 调用返回 400 错误
**解决**: 检查请求参数是否正确，特别是 `group_id` 参数

### 问题：音频文件无法播放 / 文件损坏
**可能原因**:
1. **账户余额不足** (错误码 1008)
   - 检查 MiniMax 账户余额
   - 充值后再试
   
2. **API Key 无效** (错误码 1001)
   - 检查 `MINIMAX_API_KEY` 是否正确
   
3. **Group ID 无效** (错误码 1002)
   - 检查 `MINIMAX_GROUP_ID` 是否正确

4. **API 响应格式不正确**
   - 查看后端日志中的错误信息
   - 根据实际 API 文档调整代码

**解决步骤**:
- 查看后端控制台的错误日志
- 代码已自动检测并拒绝保存无效的音频数据
- 如果看到 "账户余额不足" 错误，需要先充值

### 问题：找不到环境变量
**解决**: 
- 确保 `.env` 文件在项目根目录
- 确保环境变量名称正确（`MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`）
- 重启应用以加载新的环境变量

### 问题：生成的 WAV 文件是 JSON 错误信息
**原因**: API 返回了错误信息而不是音频数据，但代码没有正确检测

**解决**: 
- ✅ 已修复：代码现在会自动检测并拒绝保存错误响应
- 如果仍然出现，请检查后端日志中的详细错误信息

## 💡 提示

- 首次使用建议先运行测试脚本验证配置
- 如果 API 端点或响应格式与代码不一致，请根据官方文档调整
- 可以尝试不同的音色和情感参数，找到最适合你应用场景的配置

