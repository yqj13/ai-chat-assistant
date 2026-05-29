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


class AguiEventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    
    THINKING_START = "THINKING_START"
    THINKING_END = "THINKING_END"
    
    THINKING_TEXT_MESSAGE_START = "THINKING_TEXT_MESSAGE_START"
    THINKING_TEXT_MESSAGE_CONTENT = "THINKING_TEXT_MESSAGE_CONTENT"
    THINKING_TEXT_MESSAGE_END = "THINKING_TEXT_MESSAGE_END"
    
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    MESSAGES_SNAPSHOT = "MESSAGES_SNAPSHOT"


class AguiMessage(BaseModel):
    type: AguiEventType
    runId: Optional[str] = None
    messageId: Optional[str] = None
    role: Optional[str] = None
    delta: Optional[str] = None
    content: Optional[str] = None
    toolCallId: Optional[str] = None
    toolCallName: Optional[str] = None
    error: Optional[str] = None


class AguiChatRequest(BaseModel):
    content: str
    uid: str
    run_id: Optional[str] = None
