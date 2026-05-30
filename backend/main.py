from fastapi import FastAPI, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
from sqlalchemy.orm import Session

from chat_service import chat_service
from sse_manager import sse_manager
from agui_chat_service import agui_chat_service
from agui_sse_manager import agui_sse_manager
from database import init_db, get_db
from db_service import db_service
from config import settings

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")


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


class LoginRequest(BaseModel):
    uid: str
    username: Optional[str] = None


class CredentialLoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class SessionCreateRequest(BaseModel):
    uid: str
    session_id: Optional[str] = None
    title: Optional[str] = None


class SessionUpdateRequest(BaseModel):
    title: str


@app.post("/api/user/register")
async def user_register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册接口"""
    user = db_service.create_user(db, request.username, request.password)
    if not user:
        return JSONResponse(status_code=400, content={"error": "Username already exists"})
    return JSONResponse(content={
        "user_id": user.id,
        "uid": user.uid,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


@app.post("/api/user/login")
async def user_login(request: CredentialLoginRequest, db: Session = Depends(get_db)):
    """用户登录接口（用户名密码）"""
    user = db_service.login_user(db, request.username, request.password)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid username or password"})
    return JSONResponse(content={
        "user_id": user.id,
        "uid": user.uid,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


@app.post("/api/user/login/uid")
async def user_login_by_uid(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录/自动注册接口（通过uid）"""
    user = db_service.get_or_create_user(db, request.uid, request.username)
    return JSONResponse(content={
        "user_id": user.id,
        "uid": user.uid,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


@app.get("/api/user/{uid}")
async def get_user(uid: str, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db_service.get_user_by_uid(db, uid)
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return JSONResponse(content={
        "user_id": user.id,
        "uid": user.uid,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


@app.post("/api/session")
async def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
    """创建新会话"""
    user = db_service.get_user_by_uid(db, request.uid)
    if not user:
        user = db_service.get_or_create_user(db, request.uid)
    session = db_service.create_session(db, user.id, request.session_id, request.title)
    return JSONResponse(content={
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None
    })


@app.get("/api/sessions/{uid}")
async def get_user_sessions(uid: str, db: Session = Depends(get_db)):
    """获取用户的所有会话"""
    user = db_service.get_user_by_uid(db, uid)
    if not user:
        return JSONResponse(content=[])
    sessions = db_service.get_user_sessions(db, user.id)
    return JSONResponse(content=[
        {
            "session_id": s.session_id,
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in sessions
    ])


@app.get("/api/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取会话详情"""
    session = db_service.get_session_by_id(db, session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content={
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None
    })


@app.put("/api/session/{session_id}")
async def update_session(session_id: str, request: SessionUpdateRequest, db: Session = Depends(get_db)):
    """更新会话标题"""
    session = db_service.update_session_title(db, session_id, request.title)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content={
        "session_id": session.session_id,
        "title": session.title,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None
    })


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    success = db_service.delete_session(db, session_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content={"status": "ok"})


@app.get("/api/messages/{session_id}")
async def get_session_messages(session_id: str, limit: Optional[int] = None, db: Session = Depends(get_db)):
    """获取会话的所有消息"""
    messages = db_service.get_session_messages(db, session_id, limit)
    return JSONResponse(content=[
        {
            "message_id": m.message_id,
            "role": m.role,
            "content": m.content,
            "prompt": m.prompt,
            "reasoning_content": m.reasoning_content,
            "tool_name": m.tool_name,
            "tool_input": m.tool_input,
            "tool_output": m.tool_output,
            "message_type": m.message_type,
            "time": m.time.isoformat() if m.time else None,
            "sequence": m.sequence,
            "finish_status": m.finish_status
        }
        for m in messages
    ])


@app.delete("/api/message/{message_id}")
async def delete_message(message_id: str, db: Session = Depends(get_db)):
    """删除消息"""
    success = db_service.delete_message(db, message_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Message not found"})
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