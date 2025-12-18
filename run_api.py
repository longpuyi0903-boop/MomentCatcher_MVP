"""
启动 FastAPI 后端服务器
"""

import uvicorn

if __name__ == "__main__":
    import os
    
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
    print("="*60)
    
    # 云端部署：使用环境变量PORT，监听0.0.0.0
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"📚 API 文档: http://{host}:{port}/docs")
    print(f"🔗 API 地址: http://{host}:{port}")
    print("="*60 + "\n")
    
    # 生产环境禁用reload（云端部署平台，如 Render）
    # Render 会设置 RENDER 环境变量，或者检查是否有 PORT 环境变量（云端部署标志）
    is_production = os.environ.get("RENDER") == "true" or os.environ.get("PORT") is not None
    reload = not is_production
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


