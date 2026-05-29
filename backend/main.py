from fastapi import FastAPI, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from chat_service import chat_service
from sse_manager import sse_manager
from agui_chat_service import agui_chat_service
from agui_sse_manager import agui_sse_manager

logger = logging.getLogger(__name__)

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
    deep_thinking: Optional[bool] = False
    web_search: Optional[bool] = False


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    发送消息接口 - 对应 Java 版的 /chat
    只触发 agent 执行，返回 message_id
    
    参数说明：
    - content: 用户输入内容
    - uid: 用户ID
    - context_id: 对话上下文ID（用于多轮对话）
    - last_message_id: 最后消息ID（用于断点续传）
    - deep_thinking: 是否开启深度思考模式
    - web_search: 是否强制使用联网查询
    """
    message_id = await chat_service.chat(
        content=request.content,
        uid=request.uid,
        context_id=request.context_id,
        last_message_id=request.last_message_id,
        deep_thinking=request.deep_thinking,
        web_search=request.web_search
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


class AguiChatRequest(BaseModel):
    content: str
    uid: str
    run_id: Optional[str] = None


@app.post("/api/agui/chat")
async def agui_chat(request: AguiChatRequest):
    """
    AgUI 协议 - 发送消息接口
    触发 agent 执行，返回 message_id
    """
    message_id = await agui_chat_service.chat(
        content=request.content,
        uid=request.uid,
        run_id=request.run_id
    )
    return JSONResponse(content={"message_id": message_id})


class AguiStreamRequest(BaseModel):
    content: Optional[str] = None
    uid: str
    message_id: Optional[str] = None
    last_sequence: int = 0
    model: Optional[str] = None
    temperature: Optional[float] = None


@app.post("/api/agui/stream")
async def agui_stream(
    request: AguiStreamRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_custom_header: Optional[str] = Header(None, alias="X-Custom-Header")
):
    """
    AgUI 协议 - SSE 连接接口
    支持流式输出和工具调用，消息格式遵循 TDesign AgUI 协议
    
    支持自定义请求头：
    - Authorization: Bearer token
    - X-Custom-Header: 自定义头
    
    请求体参数：
    - content: 用户输入内容（可选，若提供则先触发聊天）
    - uid: 用户ID（必填）
    - message_id: 消息ID（可选，用于断点续传）
    - last_sequence: 最后收到的序号（可选，用于断点续传）
    - model: 模型名称（可选）
    - temperature: 温度参数（可选）
    """
    logger.info(f"AgUI stream request - uid: {request.uid}, message_id: {request.message_id}, "
                f"authorization: {authorization is not None}, x_custom_header: {x_custom_header}")
    
    if request.content and not request.message_id:
        request.message_id = await agui_chat_service.chat(
            content=request.content,
            uid=request.uid
        )
    
    return StreamingResponse(
        agui_sse_manager.stream_generator(
            uid=request.uid,
            message_id=request.message_id,
            last_sequence=request.last_sequence,
            timeout=120
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.delete("/api/agui/user/{uid}")
async def agui_cleanup_user(uid: str):
    """AgUI 协议 - 清理用户所有缓存"""
    await agui_sse_manager.cleanup_user(uid)
    return JSONResponse(content={"status": "ok"})


@app.delete("/api/agui/message/{uid}/{message_id}")
async def agui_cleanup_message(uid: str, message_id: str):
    """AgUI 协议 - 清理指定消息缓存"""
    await agui_sse_manager.cleanup_message(uid, message_id)
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