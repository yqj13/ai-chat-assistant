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

from config import settings
from models import StreamChunk, MessageType
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
        # 追踪正在执行的任务，防止重复执行
        self.active_tasks: Dict[str, asyncio.Task] = {}

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
    ) -> str:
        """
        发送消息接口 - 类似 Java 版的 /chat 接口
        只负责触发 agent 执行，不负责 SSE 推送
        """
        message_id = self._generate_message_id()

        # 如果有 last_message_id，说明是断点续传场景
        # 检查该消息是否还在执行中
        if last_message_id:
            task_key = f"{uid}:{last_message_id}"
            if task_key in self.active_tasks and not self.active_tasks[task_key].done():
                # 任务还在执行，直接返回原 message_id，让前端通过 SSE 获取
                logger.info(f"Task still running for {task_key}, returning existing message_id")
                return last_message_id
            # 任务已完成但消息可能还在缓存中，直接返回让前端通过 SSE 回放
            cached = await sse_manager.get_cached_messages(uid, last_message_id)
            if cached:
                logger.info(f"Returning cached message_id {last_message_id} for replay")
                return last_message_id

        history_key = context_id or uid
        if history_key not in self.conversation_history:
            self.conversation_history[history_key] = []

        # 先添加用户消息到历史
        self.conversation_history[history_key].append(HumanMessage(content=content))

        # 启动异步任务执行 agent
        task = asyncio.create_task(self._execute_stream(
            content,
            uid,
            message_id,
            history_key
        ))

        # 追踪任务
        task_key = f"{uid}:{message_id}"
        self.active_tasks[task_key] = task

        # 任务完成后清理
        task.add_done_callback(lambda t: self.active_tasks.pop(task_key, None))

        return message_id

    async def _execute_stream(
        self,
        input_text: str,
        uid: str,
        message_id: str,
        history_key: str
    ):
        """执行 agent 并通过 sse_manager 缓存消息"""
        try:
            config: RunnableConfig = {"configurable": {"thread_id": history_key}}

            # 发送初始消息（类似 Java 版的第一条消息）
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
                        text_content = ""
                        reasoning_content = ""

                        if isinstance(chunk.content, str):
                            text_content = chunk.content
                        elif isinstance(chunk.content, list):
                            for part in chunk.content:
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        text_content += part.get("text", "")
                                    elif part.get("type") == "thinking":
                                        reasoning_content += part.get("thinking", "")

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

                        if reasoning_content:
                            stream_chunk = StreamChunk(
                                status=False,
                                content="",
                                reasoning_content=reasoning_content,
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

            # 保存 AI 回复到历史
            if current_content:
                self.conversation_history[history_key].append(AIMessage(content=current_content))

            # 发送完成消息 - 关键：status=True 表示结束
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

    async def cleanup_context(self, context_id: str):
        if context_id in self.conversation_history:
            del self.conversation_history[context_id]
            logger.info(f"Cleaned up context {context_id}")


chat_service = ChatService()