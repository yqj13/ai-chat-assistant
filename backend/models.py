from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(int, Enum):
    TEXT = 0
    TOOL_START = 1
    TOOL_END = 2
    SEARCH_START = 3
    SEARCH_END = 4


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    message_id: Optional[str] = None
    finish_status: Optional[bool] = None


class ChatRequest(BaseModel):
    content: str
    uid: str
    context_id: Optional[str] = None
    last_message_id: Optional[str] = None


class StreamChunk(BaseModel):
    status: bool
    content: Optional[str] = None
    message_id: Optional[str] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    type: Optional[int] = Field(default=0, description="消息类型：0=普通文本, 1=工具调用中, 2=工具调用完成, 3=联网搜索中, 4=联网搜索完成")


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
