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
from models import AguiEventType
from tools import create_tools
from agui_sse_manager import agui_sse_manager

logger = logging.getLogger(__name__)


class AguiChatService:
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
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def _generate_run_id(self, length: int = 12) -> str:
        return 'run_' + ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_message_id(self, length: int = 10) -> str:
        return 'msg_' + ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_tool_call_id(self, length: int = 8) -> str:
        return 'tool_' + ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    async def _send_agui_message(self, uid: str, message_id: str, event_type: AguiEventType, **kwargs):
        message = {"type": event_type.value}
        message.update(kwargs)
        await agui_sse_manager.send_message(
            uid,
            message_id,
            json.dumps(message, ensure_ascii=False)
        )

    async def chat(
        self,
        content: str,
        uid: str,
        run_id: Optional[str] = None,
    ) -> str:
        message_id = self._generate_message_id()
        
        if run_id:
            task_key = f"{uid}:{run_id}"
            if task_key in self.active_tasks and not self.active_tasks[task_key].done():
                logger.info(f"AgUI task still running for {task_key}, returning existing message_id")
                return message_id
            
            cached = await agui_sse_manager.get_cached_messages(uid, run_id)
            if cached:
                logger.info(f"AgUI returning cached message_id {run_id} for replay")
                return run_id

        task = asyncio.create_task(self._execute_stream(
            content,
            uid,
            message_id
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
    ):
        try:
            run_id = self._generate_run_id()
            logger.info(f"AgUI starting run {run_id} for user {uid}")

            await self._send_agui_message(
                uid,
                message_id,
                AguiEventType.RUN_STARTED,
                runId=run_id
            )

            await self._send_agui_message(
                uid,
                message_id,
                AguiEventType.TEXT_MESSAGE_START,
                messageId=message_id,
                role="assistant"
            )

            current_content = ""

            async for event in self.agent.astream_events(
                {"messages": [{"role": "user", "content": input_text}]},
                config={"configurable": {"thread_id": uid}},
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
                            await self._send_agui_message(
                                uid,
                                message_id,
                                AguiEventType.TEXT_MESSAGE_CONTENT,
                                messageId=message_id,
                                delta=text_content
                            )

                        if reasoning_content:
                            await self._send_agui_message(
                                uid,
                                message_id,
                                AguiEventType.THINKING_TEXT_MESSAGE_CONTENT,
                                messageId=message_id,
                                delta=reasoning_content
                            )

                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    tool_inputs = event["data"].get("input", {})
                    tool_call_id = self._generate_tool_call_id()

                    await self._send_agui_message(
                        uid,
                        message_id,
                        AguiEventType.TOOL_CALL_START,
                        toolCallId=tool_call_id,
                        toolCallName=tool_name
                    )

                    args_json = json.dumps(tool_inputs, ensure_ascii=False)
                    await self._send_agui_message(
                        uid,
                        message_id,
                        AguiEventType.TOOL_CALL_ARGS,
                        toolCallId=tool_call_id,
                        delta=args_json
                    )

                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    tool_name = event.get("name", "")
                    tool_call_id = self._generate_tool_call_id()

                    await self._send_agui_message(
                        uid,
                        message_id,
                        AguiEventType.TOOL_CALL_END,
                        toolCallId=tool_call_id
                    )

                    if isinstance(tool_output, str):
                        tool_result = tool_output
                    else:
                        tool_result = str(tool_output)

                    await self._send_agui_message(
                        uid,
                        message_id,
                        AguiEventType.TOOL_CALL_RESULT,
                        toolCallId=tool_call_id,
                        content=tool_result
                    )

            await self._send_agui_message(
                uid,
                message_id,
                AguiEventType.TEXT_MESSAGE_END,
                messageId=message_id
            )

            await self._send_agui_message(
                uid,
                message_id,
                AguiEventType.RUN_FINISHED,
                runId=run_id
            )

            logger.info(f"AgUI run {run_id} completed for user {uid}")

        except Exception as e:
            logger.error(f"AgUI agent execution error: {str(e)}", exc_info=True)

            await self._send_agui_message(
                uid,
                message_id,
                AguiEventType.RUN_ERROR,
                runId=self._generate_run_id(),
                error=str(e)
            )


agui_chat_service = AguiChatService()