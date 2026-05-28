import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from models import ChatRequest
from chat_service import chat_service
from sse_manager import sse_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Chat Service with Tools",
    description="支持工具调用的AI聊天服务（流式输出+断点续传）",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "AI Chat Service is running",
        "features": ["streaming", "resume", "tools"]
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        message_id = await chat_service.chat_stream(
            content=request.content,
            uid=request.uid,
            context_id=request.context_id,
            last_message_id=request.last_message_id
        )
        
        return {
            "status": "success",
            "message_id": message_id,
            "uid": request.uid
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream/{uid}/{message_id}")
async def stream_messages(uid: str, message_id: str):
    try:
        return EventSourceResponse(
            sse_manager.stream_generator(uid, message_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Stream endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/context/{context_id}")
async def cleanup_context(context_id: str):
    try:
        await chat_service.cleanup_context(context_id)
        return {"status": "success", "message": "Context cleaned up"}
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/user/{uid}")
async def cleanup_user(uid: str):
    try:
        await sse_manager.cleanup_user(uid)
        return {"status": "success", "message": "User data cleaned up"}
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )