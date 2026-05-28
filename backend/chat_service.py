import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
import random
import string
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from config import settings
from models import ChatMessage, StreamChunk, MessageRole, MessageType
from tools import create_tools
from sse_manager import sse_manager

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.tools = create_tools()
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            openai_api_key=settings.API_KEY,
            openai_api_base=settings.API_URL,
            temperature=0.7
        )
        self.checkpointer = MemorySaver()
        self.agent = create_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )
        self.conversation_history: Dict[str, List] = {}
    
    def _generate_message_id(self, length: int = 10) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _get_tool_type(self, tool_name: str) -> int:
        if 'search' in tool_name.lower() or 'web' in tool_name.lower():
            return MessageType.SEARCH_START
        return MessageType.TOOL_START
    
    def _get_tool_end_type(self, tool_name: str) -> int:
        if 'search' in tool_name.lower() or 'web' in tool_name.lower():
            return MessageType.SEARCH_END
        return MessageType.TOOL_END
    
    async def chat_stream(
        self,
        content: str,
        uid: str,
        context_id: Optional[str] = None,
        last_message_id: Optional[str] = None,
    ) -> str:
        message_id = self._generate_message_id()
        
        if last_message_id:
            cached = await sse_manager.get_cached_messages(uid, last_message_id)
            if cached:
                logger.info(f"Resuming from cached messages for user {uid}")
                return last_message_id
        
        history_key = context_id or uid
        if history_key not in self.conversation_history:
            self.conversation_history[history_key] = []
        
        asyncio.create_task(self._execute_stream(
            content,
            uid,
            message_id,
            history_key
        ))
        
        self.conversation_history[history_key].append(HumanMessage(content=content))
        
        return message_id
    
    async def _execute_stream(
        self,
        input_text: str,
        uid: str,
        message_id: str,
        history_key: str
    ):
        try:
            config: RunnableConfig = {"configurable": {"thread_id": history_key}}
            
            await sse_manager.send_message(
                uid,
                message_id,
                json.dumps({"status": False, "content": "", "message_id": message_id, "type": MessageType.TEXT}, ensure_ascii=False)
            )
            
            current_content = ""
            
            async for event in self.agent.astream_events(
                {"messages": [{"role": "user", "content": input_text}]},
                config=config,
                version="v1"
            ):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        if isinstance(chunk.content, str):
                            current_content += chunk.content
                            
                            stream_chunk = StreamChunk(
                                status=False,
                                content=chunk.content,
                                message_id=message_id,
                                type=MessageType.TEXT
                            )
                            
                            await sse_manager.send_message(
                                uid,
                                message_id,
                                json.dumps(stream_chunk.dict(), ensure_ascii=False)
                            )
                        elif isinstance(chunk.content, list):
                            for part in chunk.content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text = part.get("text", "")
                                    current_content += text
                                    
                                    stream_chunk = StreamChunk(
                                        status=False,
                                        content=text,
                                        message_id=message_id,
                                        type=MessageType.TEXT
                                    )
                                    
                                    await sse_manager.send_message(
                                        uid,
                                        message_id,
                                        json.dumps(stream_chunk.dict(), ensure_ascii=False)
                                    )
                
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    tool_inputs = event["data"].get("input", {})
                    tool_type = self._get_tool_type(tool_name)
                    
                    tool_msg = f"正在调用工具: {tool_name}"
                    
                    stream_chunk = StreamChunk(
                        status=False,
                        content=json.dumps({"tool": tool_name, "params": tool_inputs}, ensure_ascii=False),
                        message_id=message_id,
                        type=tool_type
                    )
                    
                    await sse_manager.send_message(
                        uid,
                        message_id,
                        json.dumps(stream_chunk.dict(), ensure_ascii=False)
                    )
                
                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    tool_name = event.get("name", "")
                    tool_end_type = self._get_tool_end_type(tool_name)
                    
                    if isinstance(tool_output, str):
                        if "content=" in tool_output and "name=" in tool_output:
                            content_start = tool_output.find("content='") + 9
                            content_end = tool_output.find("'", content_start)
                            if content_start > 8 and content_end > content_start:
                                extracted_content = tool_output[content_start:content_end]
                                tool_msg = f"工具执行完成\n\n{extracted_content}\n"
                            else:
                                tool_msg = f"工具执行完成\n\n{tool_output}\n"
                        else:
                            tool_msg = f"工具执行完成\n\n{tool_output}\n"
                    else:
                        tool_msg = "工具执行完成\n"
                    
                    stream_chunk = StreamChunk(
                        status=False,
                        content=json.dumps({"tool": tool_name, "result": tool_msg.strip()}, ensure_ascii=False),
                        message_id=message_id,
                        type=tool_end_type
                    )
                    
                    await sse_manager.send_message(
                        uid,
                        message_id,
                        json.dumps(stream_chunk.dict(), ensure_ascii=False)
                    )
            
            if current_content:
                self.conversation_history[history_key].append(AIMessage(content=current_content))
            
            finish_chunk = StreamChunk(
                status=True,
                content="",
                message_id=message_id,
                finish_reason="stop",
                type=MessageType.TEXT
            )
            
            await sse_manager.send_message(
                uid,
                message_id,
                json.dumps(finish_chunk.dict(), ensure_ascii=False)
            )
            
            logger.info(f"Agent execution completed for user {uid}")
            
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)
            
            error_chunk = StreamChunk(
                status=True,
                content=f"\n执行出错: {str(e)}",
                message_id=message_id,
                finish_reason="error",
                type=MessageType.TEXT
            )
            
            await sse_manager.send_message(
                uid,
                message_id,
                json.dumps(error_chunk.dict(), ensure_ascii=False)
            )
    
    async def cleanup_context(self, context_id: str):
        if context_id in self.conversation_history:
            del self.conversation_history[context_id]
            logger.info(f"Cleaned up context {context_id}")


chat_service = ChatService()
