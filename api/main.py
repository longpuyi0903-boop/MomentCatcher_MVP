"""
FastAPI Backend for Moment Catcher
REST API 封装后端功能
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
import tempfile
from pathlib import Path

# 导入后端模块
from backend.agent.reply_generator import generate_reply
from backend.audio.tts_engine import text_to_speech as tts_generate
from backend.audio.asr_engine import speech_to_text as asr_generate
from backend.memory.moment_manager import MomentManager
from backend.memory.moment_card import generate_moment_card
from backend.memory.style_rag import StyleRAG
from backend.memory.context_rag import ContextRAG
from config.persona_config import get_system_prompt, get_greeting
from data_model.user_session import UserSession

# 创建 FastAPI 应用
app = FastAPI(
    title="Moment Catcher API",
    description="AI 陪伴 Agent 的 REST API",
    version="1.0.0"
)

# 配置 CORS（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局管理器实例（按用户ID存储）
managers: Dict[str, Dict] = {}


def get_managers(user_id: str) -> Dict:
    """获取或创建用户的管理器实例"""
    if user_id not in managers:
        managers[user_id] = {
            'moment_manager': MomentManager(),
            'style_rag': StyleRAG(),
            'context_rag': ContextRAG()
        }
        # 设置用户ID
        managers[user_id]['moment_manager'].set_user_id(
            user_id.split('_')[0] if '_' in user_id else user_id,
            user_id.split('_')[1] if '_' in user_id else 'Kay'
        )
        managers[user_id]['style_rag'].set_user_id(
            user_id.split('_')[0] if '_' in user_id else user_id,
            user_id.split('_')[1] if '_' in user_id else 'Kay'
        )
        managers[user_id]['context_rag'].set_user_id(
            user_id.split('_')[0] if '_' in user_id else user_id,
            user_id.split('_')[1] if '_' in user_id else 'Kay'
        )
    return managers[user_id]


# ============================================================
# Pydantic 数据模型
# ============================================================

class InitRequest(BaseModel):
    """初始化请求"""
    user_name: str
    agent_name: str


class InitResponse(BaseModel):
    """初始化响应"""
    user_id: str
    greeting: str
    message: str


class ChatRequest(BaseModel):
    """聊天请求"""
    user_id: str
    message: str
    history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    emotion: str
    audio_path: Optional[str] = None
    moment_id: Optional[str] = None
    message_count: int


class StartMomentRequest(BaseModel):
    """开始新 Moment 请求"""
    user_id: str


class StartMomentResponse(BaseModel):
    """开始新 Moment 响应"""
    moment_id: str
    greeting: str
    message: str


class SaveMomentRequest(BaseModel):
    """保存 Moment 请求"""
    user_id: str


class SaveMomentResponse(BaseModel):
    """保存 Moment 响应"""
    moment_id: str
    card: Dict
    message: str


class MomentCard(BaseModel):
    """Moment Card 数据模型"""
    moment_id: str
    timestamp: str
    emotion: str
    title: str
    summary: str
    color: str
    message_count: int


class MomentsResponse(BaseModel):
    """所有 Moments 响应"""
    moments: List[Dict]
    total: int


class StyleProfileResponse(BaseModel):
    """风格画像响应"""
    profile: Dict


class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str


class ASRResponse(BaseModel):
    """ASR 响应"""
    text: str
    success: bool
    message: Optional[str] = None


# ============================================================
# API 路由
# ============================================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Moment Catcher API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/init", response_model=InitResponse)
async def init_connection(request: InitRequest):
    """
    初始化连接
    设置用户名和 Agent 名，返回问候语
    """
    try:
        user_id = f"{request.user_name}_{request.agent_name}"
        
        # 获取管理器
        mgrs = get_managers(user_id)
        
        # 生成问候语
        greeting = get_greeting(request.user_name, request.agent_name)
        
        return InitResponse(
            user_id=user_id,
            greeting=greeting,
            message=f"✨ Link Initiated: {request.user_name} <-> {request.agent_name}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/moments/start", response_model=StartMomentResponse)
async def start_moment(request: StartMomentRequest):
    """
    开始新的 Moment
    """
    try:
        mgrs = get_managers(request.user_id)
        moment_manager = mgrs['moment_manager']
        
        # 开始新 Moment
        moment_manager.start_new_moment()
        
        # 生成问候语
        user_name = request.user_id.split('_')[0] if '_' in request.user_id else request.user_id
        agent_name = request.user_id.split('_')[1] if '_' in request.user_id else 'Kay'
        greeting = get_greeting(user_name, agent_name)
        
        return StartMomentResponse(
            moment_id=moment_manager.current_moment_id or "",
            greeting=greeting,
            message="✨ 已开始新 Moment"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    发送消息并获取回复（带 RAG）
    """
    try:
        mgrs = get_managers(request.user_id)
        moment_manager = mgrs['moment_manager']
        style_rag = mgrs['style_rag']
        context_rag = mgrs['context_rag']
        
        # 如果没有活跃的 Moment，自动开始一个
        if not moment_manager.current_moment_id:
            moment_manager.start_new_moment()
        
        # 1. 学习用户风格
        style_rag.learn_from_message(request.message)
        
        # 2. 检索相关历史上下文
        context_prompt = context_rag.generate_context_prompt(request.message, max_context=2)
        
        # 3. 获取风格提示
        style_prompt = style_rag.get_style_prompt()
        
        # 4. 构建完整 prompt
        user_name = request.user_id.split('_')[0] if '_' in request.user_id else request.user_id
        agent_name = request.user_id.split('_')[1] if '_' in request.user_id else 'Kay'
        system_prompt = get_system_prompt(user_name=user_name, kay_name=agent_name)
        
        # 添加 RAG 上下文
        if context_prompt:
            system_prompt += f"\n\n{context_prompt}"
        
        if style_prompt:
            system_prompt += f"\n\n{style_prompt}"
        
        # 5. 创建临时 session
        temp_session = UserSession(user_name=user_name, kay_name=agent_name)
        
        # 将 history 转换为 session.messages 格式
        if request.history:
            for msg in request.history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                temp_session.add_message(role, content, "neutral")
        
        # 6. 生成回复
        assistant_reply, detected_emotion = generate_reply(
            user_message=request.message,
            session=temp_session,
            system_prompt=system_prompt
        )
        
        # 7. 保存到当前 Moment
        moment_manager.add_message("user", request.message, emotion="neutral")
        moment_manager.add_message("assistant", assistant_reply, emotion="neutral")
        
        # 8. 生成语音
        audio_path = None
        audio_url = None
        try:
            audio_path = tts_generate(assistant_reply)
            # 转换为可访问的 URL（相对路径）
            if audio_path:
                # 从绝对路径转换为相对路径，前端可以通过代理访问
                audio_path_str = str(audio_path)
                if 'audio_outputs' in audio_path_str:
                    audio_url = f"/api/audio/{Path(audio_path).name}"
        except Exception as e:
            print(f"⚠️ TTS 生成失败: {e}")
        
        return ChatResponse(
            reply=assistant_reply,
            emotion=detected_emotion or "neutral",
            audio_path=audio_url,  # 返回 URL 而不是本地路径
            moment_id=moment_manager.current_moment_id,
            message_count=len(moment_manager.current_messages)
        )
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\n{traceback.format_exc()}"
        print(f"❌ Chat API 错误: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Chat API 错误: {str(e)}")


@app.post("/api/moments/save", response_model=SaveMomentResponse)
async def save_moment(request: SaveMomentRequest):
    """
    保存当前 Moment 并生成 Moment Card
    """
    try:
        mgrs = get_managers(request.user_id)
        moment_manager = mgrs['moment_manager']
        
        if not moment_manager.current_moment_id:
            raise HTTPException(status_code=400, detail="当前没有活跃的 Moment")
        
        if len(moment_manager.current_messages) == 0:
            raise HTTPException(status_code=400, detail="当前 Moment 没有对话，无法保存")
        
        # 1. 结束 Moment
        moment_data = moment_manager.end_moment()
        
        # 2. 生成 Moment Card
        card = generate_moment_card(moment_data)
        
        # 3. 更新 Moment 数据
        moment_manager.update_moment(moment_data['moment_id'], {
            'summary': card.summary,
            'emotion_tag': card.emotion,
            'title': card.title,
            'color': card.color,
            'card_generated': True
        })
        
        # 4. 返回结果
        card_dict = {
            'moment_id': card.moment_id,
            'timestamp': card.timestamp,
            'emotion': card.emotion,
            'title': card.title,
            'summary': card.summary,
            'color': card.color,
            'message_count': card.message_count
        }
        
        return SaveMomentResponse(
            moment_id=card.moment_id,
            card=card_dict,
            message="✅ Moment 已保存并生成 Moment Card"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/moments", response_model=MomentsResponse)
async def get_all_moments(user_id: str):
    """
    获取所有 Moments
    """
    try:
        mgrs = get_managers(user_id)
        moment_manager = mgrs['moment_manager']
        
        moments = moment_manager.get_all_moments()
        
        # 反转列表，给每个 Moment 分配编号
        moments_for_numbering = list(reversed(moments))
        numbered_moments = []
        for i, moment in enumerate(moments_for_numbering, 1):
            moment['display_number'] = i
            numbered_moments.append(moment)
        
        # 反转回来用于显示（最新的在上）
        display_moments = list(reversed(numbered_moments))
        
        return MomentsResponse(
            moments=display_moments,
            total=len(moments)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/style/profile", response_model=StyleProfileResponse)
async def get_style_profile(user_id: str):
    """
    获取用户风格画像
    """
    try:
        mgrs = get_managers(user_id)
        style_rag = mgrs['style_rag']
        
        profile = style_rag.get_style_profile()
        
        return StyleProfileResponse(profile=profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts")
async def text_to_speech_api(request: TTSRequest):
    """
    文本转语音
    返回音频文件路径
    """
    try:
        audio_path = tts_generate(request.text)
        
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="TTS 生成失败")
        
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename="reply.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/asr", response_model=ASRResponse)
async def speech_to_text_api(audio_file: UploadFile = File(...)):
    """
    语音转文字（ASR）
    接收音频文件，返回识别结果
    
    支持格式：wav, mp3, m4a 等
    """
    tmp_file_path = None
    try:
        # 创建临时文件保存上传的音频
        suffix = Path(audio_file.filename).suffix or '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            # 读取上传的文件内容
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 调用 ASR 引擎
        text = asr_generate(tmp_file_path)
        
        # 删除临时文件
        try:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except:
            pass
        
        if text and text.strip():
            return ASRResponse(
                text=text.strip(),
                success=True,
                message="语音识别成功"
            )
        else:
            # 记录详细错误信息
            print(f"⚠️ ASR 返回空结果")
            print(f"   文件: {audio_file.filename}")
            print(f"   大小: {len(content)} bytes")
            print(f"   文件扩展名: {suffix}")
            # 打印ASR引擎的详细错误（如果有）
            return ASRResponse(
                text="",
                success=False,
                message="识别结果为空，请检查音频质量和格式。请查看后端日志获取详细信息。"
            )
    except Exception as e:
        # 确保临时文件被删除
        try:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"ASR 处理失败: {str(e)}")


@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    """
    获取音频文件
    用于前端访问 TTS 生成的音频文件
    """
    audio_dir = Path("audio_outputs")
    audio_file = audio_dir / filename
    
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    return FileResponse(
        audio_file,
        media_type="audio/wav",
        filename=filename
    )


@app.post("/api/update-names")
async def update_names(request: Dict):
    """
    更新用户名字和 Agent 名字
    重命名所有相关用户数据，不删除之前的记录
    
    Request body:
    {
        "old_user_id": "old_user_old_agent",
        "new_user_name": "new_user",
        "new_agent_name": "new_agent"
    }
    """
    try:
        import shutil
        from pathlib import Path
        
        old_user_id = request.get("old_user_id")
        new_user_name = request.get("new_user_name", "").strip()
        new_agent_name = request.get("new_agent_name", "").strip()
        
        if not old_user_id or not new_user_name or not new_agent_name:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 生成新的 user_id
        new_user_id = f"{new_user_name}_{new_agent_name}".replace(" ", "_")
        
        if old_user_id == new_user_id:
            return {
                "success": True,
                "message": "名字未改变",
                "new_user_id": new_user_id
            }
        
        # 1. 重命名 Moments 目录
        old_moments_dir = Path("storage/moments") / old_user_id
        new_moments_dir = Path("storage/moments") / new_user_id
        
        if old_moments_dir.exists():
            if new_moments_dir.exists():
                # 如果新目录已存在，合并数据（将旧数据复制到新目录）
                print(f"📁 合并 Moments 数据：{old_user_id} -> {new_user_id}")
                for moment_file in old_moments_dir.glob("*.json"):
                    new_file = new_moments_dir / moment_file.name
                    if not new_file.exists():
                        shutil.copy2(moment_file, new_file)
                # 保留旧目录作为备份（可选：删除旧目录）
                # shutil.rmtree(old_moments_dir)
            else:
                # 重命名目录
                old_moments_dir.rename(new_moments_dir)
                print(f"📁 Moments 目录已重命名：{old_user_id} -> {new_user_id}")
        
        # 2. 重命名风格数据文件
        old_style_file = Path("storage/user_data") / f"{old_user_id}_style.json"
        new_style_file = Path("storage/user_data") / f"{new_user_id}_style.json"
        
        if old_style_file.exists():
            if new_style_file.exists():
                # 合并风格数据
                print(f"📁 合并风格数据：{old_user_id} -> {new_user_id}")
                with open(old_style_file, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                with open(new_style_file, 'r', encoding='utf-8') as f:
                    new_data = json.load(f)
                # 合并数据（保留所有历史记录）
                merged_data = {**old_data, **new_data}
                with open(new_style_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
            else:
                # 重命名文件
                old_style_file.rename(new_style_file)
                print(f"📁 风格文件已重命名：{old_user_id} -> {new_user_id}")
        
        # 3. 更新管理器实例（如果存在）
        if old_user_id in managers:
            # 更新管理器中的 user_id
            mgrs = managers[old_user_id]
            mgrs['moment_manager'].set_user_id(new_user_name, new_agent_name)
            mgrs['style_rag'].set_user_id(new_user_name, new_agent_name)
            mgrs['context_rag'].set_user_id(new_user_name, new_agent_name)
            
            # 将管理器迁移到新的 user_id
            managers[new_user_id] = mgrs
            if old_user_id != new_user_id:
                del managers[old_user_id]
            print(f"📁 管理器已更新：{old_user_id} -> {new_user_id}")
        
        # 4. 保存名字到 names.json（用于持久化）
        names_file = Path("storage/user_data/names.json")
        names_data = {}
        if names_file.exists():
            with open(names_file, 'r', encoding='utf-8') as f:
                names_data = json.load(f)
        names_data[new_user_id] = {
            "user_name": new_user_name,
            "agent_name": new_agent_name
        }
        with open(names_file, 'w', encoding='utf-8') as f:
            json.dump(names_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"名字已更新：{new_user_name} <-> {new_agent_name}",
            "new_user_id": new_user_id,
            "new_user_name": new_user_name,
            "new_agent_name": new_agent_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新名字失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "API is running"}


# ============================================================
# 启动应用
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🌟 Moment Catcher - FastAPI Backend")
    print("="*60)
    print("📝 API 端点:")
    print("   ✅ POST /api/init - 初始化连接")
    print("   ✅ POST /api/moments/start - 开始新 Moment")
    print("   ✅ POST /api/chat - 发送消息")
    print("   ✅ POST /api/moments/save - 保存 Moment")
    print("   ✅ GET  /api/moments - 获取所有 Moments")
    print("   ✅ GET  /api/style/profile - 获取风格画像")
    print("   ✅ POST /api/tts - 文本转语音")
    print("   ✅ POST /api/asr - 语音转文字")
    print("   ✅ POST /api/update-names - 更新用户名字")
    print("="*60)
    print("📚 API 文档: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

