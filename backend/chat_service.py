import asyncio
import json
import logging
from typing import Optional, List, Dict
import random
import string
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from openai import AsyncOpenAI

from config import settings
from models import StreamChunk, MessageType
from tools import create_tools
from sse_manager import sse_manager

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.tools = create_tools()
        self.base_llm_config = {
            "model": settings.MODEL_NAME,
            "openai_api_key": settings.API_KEY,
            "openai_api_base": settings.API_URL,
            "temperature": 0.7
        }
        self.conversation_history: Dict[str, List] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def _create_llm(self, deep_thinking: bool = False):
        llm_config = self.base_llm_config.copy()
        
        if deep_thinking:
            llm_config["extra_body"] = {
                "thinking": {"type": "enabled"}
            }
        
        return ChatOpenAI(**llm_config)

    def _create_agent(self, deep_thinking: bool = False):
        llm = self._create_llm(deep_thinking)
        checkpointer = MemorySaver()
        return create_agent(
            llm,
            self.tools,
            checkpointer=checkpointer
        )

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

    async def chat(
        self,
        content: str,
        uid: str,
        context_id: Optional[str] = None,
        last_message_id: Optional[str] = None,
        deep_thinking: Optional[bool] = False,
        web_search: Optional[bool] = False,
    ) -> str:
        message_id = self._generate_message_id()

        if last_message_id:
            task_key = f"{uid}:{last_message_id}"
            if task_key in self.active_tasks and not self.active_tasks[task_key].done():
                logger.info(f"Task still running for {task_key}, returning existing message_id")
                return last_message_id
            cached = await sse_manager.get_cached_messages(uid, last_message_id)
            if cached:
                logger.info(f"Returning cached message_id {last_message_id} for replay")
                return last_message_id

        history_key = context_id or uid
        if history_key not in self.conversation_history:
            self.conversation_history[history_key] = []

        self.conversation_history[history_key].append(HumanMessage(content=content))

        task = asyncio.create_task(self._execute_stream(
            content,
            uid,
            message_id,
            history_key,
            deep_thinking,
            web_search
        ))

        task_key = f"{uid}:{message_id}"
        self.active_tasks[task_key] = task

        task.add_done_callback(lambda t: self.active_tasks.pop(task_key, None))

        return message_id

    async def _execute_stream(
        self,
        input_text: str,
        uid: str,
        message_id: str,
        history_key: str,
        deep_thinking: bool = False,
        web_search: bool = False
    ):
        try:
            init_chunk = StreamChunk(
                status=False,
                content="",
                message_id=message_id,
                type=MessageType.TEXT,
                finish_status=False
            )
            await sse_manager.send_message(
                uid,
                message_id,
                json.dumps(init_chunk.dict(), ensure_ascii=False)
            )

            system_prompt = """你是一个专业的AI助手，能够处理准确的答案。回答时返回markdown格式。
当涉及数学公式时，请使用KaTeX格式输出。行内公式使用 $公式$ 格式，块级公式使用 $$公式$$ 格式。
例如：行内公式 $E=mc^2$，块级公式：
$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ]
            
            if web_search:
                messages[1]["content"] = "[强制搜索] " + input_text
            
            # If deep thinking is enabled, use direct OpenAI SDK to get reasoning_content
            if deep_thinking:
                await self._execute_deep_thinking_stream(
                    messages,
                    uid,
                    message_id,
                    history_key
                )
            else:
                # Otherwise use the normal agent with tools
                await self._execute_agent_stream(
                    messages,
                    uid,
                    message_id,
                    history_key,
                    web_search
                )

        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)

            error_chunk = StreamChunk(
                status=True,
                content=f"\n执行出错: {str(e)}",
                message_id=message_id,
                finish_reason="error",
                type=MessageType.TEXT,
                finish_status=True
            )
            await sse_manager.send_message(
                uid,
                message_id,
                json.dumps(error_chunk.dict(), ensure_ascii=False)
            )

    async def _execute_deep_thinking_stream(
        self,
        messages: List[Dict],
        uid: str,
        message_id: str,
        history_key: str
    ):
        """Execute stream with deep thinking using direct OpenAI SDK"""
        client = AsyncOpenAI(
            base_url=settings.API_URL,
            api_key=settings.API_KEY
        )
        
        current_content = ""
        
        stream = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            extra_body={
                "thinking": {"type": "enabled"}
            },
            stream=True
        )
        
        async for chunk in stream:
            if len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                
                # Handle reasoning content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    stream_chunk = StreamChunk(
                        status=False,
                        content="",
                        reasoning_content=delta.reasoning_content,
                        message_id=message_id,
                        type=MessageType.TEXT,
                        finish_status=False
                    )
                    await sse_manager.send_message(
                        uid,
                        message_id,
                        json.dumps(stream_chunk.dict(), ensure_ascii=False)
                    )
                
                # Handle text content
                if hasattr(delta, "content") and delta.content:
                    current_content += delta.content
                    stream_chunk = StreamChunk(
                        status=False,
                        content=delta.content,
                        message_id=message_id,
                        type=MessageType.TEXT,
                        finish_status=False
                    )
                    await sse_manager.send_message(
                        uid,
                        message_id,
                        json.dumps(stream_chunk.dict(), ensure_ascii=False)
                    )
        
        # Save to conversation history
        if current_content:
            self.conversation_history[history_key].append(AIMessage(content=current_content))
        
        # Send finish chunk
        finish_chunk = StreamChunk(
            status=True,
            content="",
            message_id=message_id,
            finish_reason="stop",
            type=MessageType.TEXT,
            finish_status=True
        )
        await sse_manager.send_message(
            uid,
            message_id,
            json.dumps(finish_chunk.dict(), ensure_ascii=False)
        )
        
        logger.info(f"Deep thinking execution completed for user {uid}, message_id {message_id}")

    async def _execute_agent_stream(
        self,
        messages: List[Dict],
        uid: str,
        message_id: str,
        history_key: str,
        web_search: bool
    ):
        """Execute stream with agent and tools"""
        config: RunnableConfig = {"configurable": {"thread_id": history_key}}
        agent = self._create_agent(deep_thinking=False)
        current_content = ""
        
        async for event in agent.astream_events(
            {"messages": messages},
            config=config,
            version="v1"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                
                if hasattr(chunk, "content") and chunk.content:
                    if isinstance(chunk.content, str):
                        text_content = chunk.content
                    elif isinstance(chunk.content, list):
                        text_content = ""
                        for part in chunk.content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_content += part.get("text", "")
                    else:
                        text_content = ""
                    
                    if text_content:
                        current_content += text_content
                        stream_chunk = StreamChunk(
                            status=False,
                            content=text_content,
                            message_id=message_id,
                            type=MessageType.TEXT,
                            finish_status=False
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

                stream_chunk = StreamChunk(
                    status=False,
                    content=json.dumps({"tool": tool_name, "params": tool_inputs}, ensure_ascii=False),
                    message_id=message_id,
                    type=tool_type,
                    finish_status=False
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
                    tool_result = tool_output
                else:
                    tool_result = str(tool_output)

                stream_chunk = StreamChunk(
                    status=False,
                    content=json.dumps({"tool": tool_name, "result": tool_result}, ensure_ascii=False),
                    message_id=message_id,
                    type=tool_end_type,
                    finish_status=False
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
            type=MessageType.TEXT,
            finish_status=True
        )
        await sse_manager.send_message(
            uid,
            message_id,
            json.dumps(finish_chunk.dict(), ensure_ascii=False)
        )

        logger.info(f"Agent execution completed for user {uid}, message_id {message_id}")

    async def cleanup_context(self, context_id: str):
        if context_id in self.conversation_history:
            del self.conversation_history[context_id]
            logger.info(f"Cleaned up context {context_id}")


chat_service = ChatService()
