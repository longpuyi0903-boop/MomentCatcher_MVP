# 可删除文件清单

## 📋 总结
基于代码审查，以下是建议删除的多余文件，按类别分类：

---

## 🧪 测试文件（可删除）

### Python 测试脚本
- `test_memory_rounds.py` - 记忆系统稳定性测试脚本（开发测试用）
- `test_memory_advanced.py` - 高级记忆测试脚本
- `test_api.py` - API 测试脚本
- `test_qwen_api.py` - Qwen API 测试脚本
- `test_aliyun_tts.py` - 阿里云 TTS 测试脚本

**说明**：这些是开发阶段的测试文件，生产环境不需要。

---

## 🧹 清理脚本（可删除，已使用完毕）

### 用户数据清理脚本
- `cleanup_users.py` - 刚创建的清理脚本（已使用）
- `cleanup_test_users.py` - 测试用户清理脚本
- `cleanup_users_simple.py` - 简化版清理脚本

**说明**：清理工作已完成，这些脚本可以删除。如需保留一个作为备份，建议保留 `cleanup_users.py`。

---

## 📚 文档文件（可选删除）

### Markdown 文档
- `FRONTEND_DEVELOPMENT_CHECKLIST.md` - 前端开发检查清单（开发阶段文档）
- `FRONTEND_SETUP_GUIDE.md` - 前端设置指南（开发阶段文档）
- `NODEJS_SETUP.md` - Node.js 设置指南（开发阶段文档）
- `MEMORY_STABILITY_TEST_PLAN.md` - 记忆稳定性测试计划（测试文档）
- `REMAINING_WORK_SUMMARY.md` - 剩余工作总结（开发阶段文档）
- `PHASE2_加强版_部署指南.md` - Phase2 部署指南（如果不再需要）
- `Moment_Catcher_项目总结_v3_更新版.md` - 项目总结（历史文档）

### Word 文档
- `背景.docx` / `~$背景.docx` - 背景文档（临时文件）
- `Moment Catcher 项目完整总结文档.docx` - 项目总结文档（历史文档）
- `UI demo.docx` / `UI demo.pdf` - UI 演示文档（如果不再需要）

**说明**：如果项目已稳定，这些开发文档可以删除。建议保留 `API_README.md` 和 `README.md`（如果有）。

---

## 🎨 参考代码目录（可选删除）

### 参考实现
- `moment-catcher_-interstellar-ai/` - 整个参考代码目录

**说明**：如果设计已经复刻完成，这个参考目录可以删除。但建议先确认所有设计都已实现。

---

## 🔧 旧代码文件（可删除）

### 废弃的模块
- `backend/audio/tts_engine_old.py` - 旧的 TTS 引擎（已被新版本替代）
- `voice_clone_simple.py` - 简单的语音克隆脚本（如果不再使用）

**说明**：确认新版本正常工作后，可以删除旧版本。

---

## 🖥️ Gradio 应用（可选删除）

### Gradio 界面
- `gradio_app.py` - Gradio Web 界面

**说明**：如果现在只使用 React 前端 + FastAPI 后端，Gradio 应用可以删除。但建议先确认是否还需要用于演示或调试。

---

## 📊 测试结果文件（可删除）

### 测试输出
- `test_results_20251215_151411.json` - 测试结果 JSON 文件
- `tests/` 目录下的所有测试文件（如果不再运行测试）

---

## 🗂️ 其他临时文件

### 配置文件/临时文件
- `voice_id.txt` - 语音 ID 文件（如果不再使用）
- `~$背景.docx` - Word 临时文件（可删除）

### Python 缓存文件（可删除）
- `**/__pycache__/` - Python 字节码缓存目录（所有子目录下的）
- `**/*.pyc` - Python 编译文件

**说明**：这些是 Python 自动生成的缓存文件，可以安全删除。Python 会在需要时重新生成。

### 测试音频文件（可删除）
- `audio_outputs/cloned_test.mp3` - 克隆语音测试文件
- `audio_outputs/latest_reply.wav` - 最新回复音频（临时文件）

**说明**：这些是测试或临时生成的音频文件，可以删除。

---

## ✅ 建议保留的文件

### 核心代码
- `api/main.py` - FastAPI 主应用
- `backend/` - 后端核心代码
- `frontend/` - 前端代码
- `config/` - 配置文件
- `data_model/` - 数据模型
- `storage/` - 存储目录（用户数据）

### 重要文档
- `API_README.md` - API 文档
- `requirements.txt` - Python 依赖
- `README.md` - 项目说明（如果有）

---

## 🚀 删除建议优先级

### 🔴 高优先级（建议立即删除）
1. 测试文件（`test_*.py`）
2. 清理脚本（`cleanup_*.py`，已使用完毕）- **注意**：`cleanup_users.py` 可以保留作为备份
3. 测试结果文件（`test_results_*.json`）
4. Word 临时文件（`~$*.docx`）
5. Python 缓存文件（`**/__pycache__/` 和 `**/*.pyc`）
6. 测试音频文件（`audio_outputs/cloned_test.mp3`, `audio_outputs/latest_reply.wav`）

### 🟡 中优先级（确认后删除）
1. 开发文档（`*_CHECKLIST.md`, `*_GUIDE.md`）
2. 参考代码目录（`moment-catcher_-interstellar-ai/`）
3. 旧代码文件（`*_old.py`）

### 🟢 低优先级（可选删除）
1. 项目总结文档（`*_总结*.md`, `*_总结*.docx`）
2. Gradio 应用（`gradio_app.py`，如果不再使用）

---

## 📝 删除命令示例

### Windows PowerShell
```powershell
# 删除测试文件
Remove-Item test_*.py -Force

# 删除清理脚本
Remove-Item cleanup_*.py -Force

# 删除测试结果
Remove-Item test_results_*.json -Force

# 删除临时文件
Remove-Item ~$*.docx -Force

# 删除参考代码目录（谨慎操作）
Remove-Item moment-catcher_-interstellar-ai -Recurse -Force
```

### 批量删除（谨慎使用）
```powershell
# 删除所有测试和清理脚本
Get-ChildItem -Filter "test_*.py" | Remove-Item -Force
Get-ChildItem -Filter "cleanup_*.py" | Remove-Item -Force

# 删除 Python 缓存文件（谨慎操作）
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File | Remove-Item -Force

# 删除测试音频文件
Remove-Item "audio_outputs\cloned_test.mp3" -Force -ErrorAction SilentlyContinue
Remove-Item "audio_outputs\latest_reply.wav" -Force -ErrorAction SilentlyContinue
```

---

## ⚠️ 注意事项

1. **备份重要数据**：删除前请确保重要数据已备份
2. **Git 提交**：如果使用 Git，建议先提交当前代码，再删除文件
3. **确认依赖**：删除前确认没有其他文件引用这些被删除的文件
4. **参考代码**：如果 `moment-catcher_-interstellar-ai/` 还有参考价值，建议保留

---

## 📊 预计可释放空间

- 测试文件：~50-100 KB
- 清理脚本：~10-20 KB
- 文档文件：~500 KB - 2 MB（取决于文档大小）
- 参考代码目录：~1-5 MB（取决于内容）
- Python 缓存文件：~100-500 KB
- 测试音频文件：~1-5 MB（取决于文件大小）
- **总计**：约 3-10 MB

