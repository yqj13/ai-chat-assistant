from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from chat_service import chat_service
from sse_manager import sse_manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    content: str
    uid: str
    context_id: Optional[str] = None
    last_message_id: Optional[str] = None


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    发送消息接口 - 对应 Java 版的 /chat
    只触发 agent 执行，返回 message_id
    """
    message_id = await chat_service.chat(
        content=request.content,
        uid=request.uid,
        context_id=request.context_id,
        last_message_id=request.last_message_id
    )
    return JSONResponse(content={"message_id": message_id})


@app.get("/api/stream/{uid}")
async def stream(
    uid: str,
    message_id: Optional[str] = Query(None),
    last_sequence: int = Query(0)
):
    """
    SSE 连接接口 - 对应 Java 版的 /connect
    支持断点续传：传入 message_id 和 last_sequence
    """
    return StreamingResponse(
        sse_manager.stream_generator(
            uid=uid,
            message_id=message_id,
            last_sequence=last_sequence,
            timeout=120
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.delete("/api/user/{uid}")
async def cleanup_user(uid: str):
    """清理用户所有缓存"""
    await sse_manager.cleanup_user(uid)
    return JSONResponse(content={"status": "ok"})


@app.delete("/api/message/{uid}/{message_id}")
async def cleanup_message(uid: str, message_id: str):
    """清理指定消息缓存"""
    await sse_manager.cleanup_message(uid, message_id)
    return JSONResponse(content={"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )