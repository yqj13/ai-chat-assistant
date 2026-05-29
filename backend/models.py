from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType:
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
    status: bool = False
    content: str = ""
    message_id: str = ""
    type: int = MessageType.TEXT
    finish_reason: Optional[str] = None
    finish_status: Optional[bool] = False
    reasoning_content: Optional[str] = None
    sequence: Optional[int] = None


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
