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
from database import get_db_sync
from db_service import db_service

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
        self.max_history_length = 20  # 最大历史对话轮数

    def _create_llm(self, deep_thinking: bool = False):
        llm_config = self.base_llm_config.copy()
        
        if deep_thinking:
            llm_config["extra_body"] = {
                "thinking": {"type": "enabled"}
            }
        else:
            llm_config["extra_body"] = {
                "thinking": {"type": "disabled"}
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

    def _build_messages_with_history(
        self,
        input_text: str,
        history_key: str,
        web_search: bool = False
    ) -> List[Dict]:
        """构建包含历史对话的消息列表"""
        system_prompt = """你是一个专业的AI助手，能够处理准确的答案。回答时返回markdown格式。
当涉及数学公式时，请使用KaTeX格式输出。行内公式使用 $公式$ 格式，块级公式使用 $$公式$$ 格式。
例如：行内公式 $E=mc^2$，块级公式：
$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话
        history = self.conversation_history.get(history_key, [])
        # 截取最近的历史记录
        if len(history) > self.max_history_length:
            history = history[-self.max_history_length:]
        
        for msg in history:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # 添加当前用户输入
        current_content = input_text
        if web_search:
            current_content = "[强制搜索] " + current_content
        messages.append({"role": "user", "content": current_content})
        
        return messages

    def _parse_tool_output(self, tool_output) -> Dict:
        """清洗工具输出，返回干净的字典格式"""
        if not tool_output:
            return {"raw": "", "error": "No output from tool"}
        
        if isinstance(tool_output, dict):
            return tool_output
        
        output_str = str(tool_output)
        
        if hasattr(tool_output, 'content'):
            content = tool_output.content
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    pass
            return {"content": str(content)}
        
        try:
            parsed = json.loads(output_str)
            if isinstance(parsed, dict):
                return parsed
            return {"raw": output_str}
        except (json.JSONDecodeError, TypeError):
            return {"raw": output_str}

    def _load_history_from_database(self, history_key: str, context_id: Optional[str] = None):
        """从数据库加载历史对话记录"""
        if context_id and history_key not in self.conversation_history:
            try:
                db = get_db_sync()
                messages = db_service.get_session_messages(db, context_id)
                db.close()
                
                history = []
                for msg in messages:
                    if msg.role == "user":
                        history.append(HumanMessage(content=msg.content or msg.prompt or ""))
                    elif msg.role == "assistant":
                        history.append(AIMessage(content=msg.content or ""))
                
                self.conversation_history[history_key] = history
                logger.info(f"Loaded {len(history)} history messages from database for {history_key}")
            except Exception as e:
                logger.error(f"Failed to load history from database: {e}")
                self.conversation_history[history_key] = []

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
        
        # 从数据库加载历史对话（如果内存中没有）
        self._load_history_from_database(history_key, context_id)
        
        # 添加新用户消息到历史
        self.conversation_history[history_key].append(HumanMessage(content=content))
        
        # 保存用户消息到数据库
        try:
            db = get_db_sync()
            user = db_service.get_or_create_user(db, uid)
            session_id = context_id
            if session_id:
                session = db_service.get_session_by_id(db, session_id)
                if not session:
                    session = db_service.create_session(db, user.id, session_id)
            else:
                session_id = message_id
                session = db_service.create_session(db, user.id, session_id, content[:50] if len(content) > 50 else content)
            
            # 创建用户消息
            user_msg_id = f"{message_id}_user"
            db_service.create_message(
                db,
                message_id=user_msg_id,
                session_id=session_id,
                user_id=user.id,
                role="user",
                content=content,
                prompt=content
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to save user message to DB: {e}")

        task = asyncio.create_task(self._execute_stream(
            content,
            uid,
            message_id,
            history_key,
            deep_thinking,
            web_search,
            context_id
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
        web_search: bool = False,
        context_id: Optional[str] = None
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

            # 构建包含历史对话的消息
            messages = self._build_messages_with_history(
                input_text=input_text,
                history_key=history_key,
                web_search=web_search
            )
            
            # If deep thinking is enabled, use direct OpenAI SDK to get reasoning_content
            if deep_thinking:
                await self._execute_deep_thinking_stream(
                    messages,
                    uid,
                    message_id,
                    history_key,
                    context_id
                )
            else:
                # Otherwise use the normal agent with tools
                await self._execute_agent_stream(
                    messages,
                    uid,
                    message_id,
                    history_key,
                    web_search,
                    context_id
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
        history_key: str,
        context_id: Optional[str] = None
    ):
        """Execute stream with deep thinking using direct OpenAI SDK"""
        client = AsyncOpenAI(
            base_url=settings.API_URL,
            api_key=settings.API_KEY
        )
        
        current_content = ""
        current_reasoning_content = ""
        
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
                    current_reasoning_content += delta.reasoning_content
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
        
        # 保存 AI 消息到数据库
        try:
            db = get_db_sync()
            user = db_service.get_user_by_uid(db, uid)
            if user:
                session_id = context_id or message_id
                db_service.create_message(
                    db,
                    message_id=message_id,
                    session_id=session_id,
                    user_id=user.id,
                    role="assistant",
                    content=current_content,
                    reasoning_content=current_reasoning_content,
                    message_type=MessageType.TEXT,
                    finish_status="stop"
                )
            db.close()
        except Exception as e:
            logger.error(f"Failed to save AI message to DB: {e}")
        
        logger.info(f"Deep thinking execution completed for user {uid}, message_id {message_id}")

    async def _execute_agent_stream(
        self,
        messages: List[Dict],
        uid: str,
        message_id: str,
        history_key: str,
        web_search: bool,
        context_id: Optional[str] = None
    ):
        """Execute stream with agent and tools"""
        config: RunnableConfig = {"configurable": {"thread_id": history_key}}
        agent = self._create_agent(deep_thinking=False)
        current_content = ""
        current_reasoning_content = ""
        
        # 转换 OpenAI 格式的消息为 LangChain 格式的消息
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # 系统提示可以添加到消息中，或者我们可以单独处理
                continue
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        async for event in agent.astream_events(
            {"messages": langchain_messages},
            config=config,
            version="v2"
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
                            if isinstance(part, dict):
                                if part.get("type") == "text":
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
                            finish_status=False,
                            reasoning_content=None
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
                
                try:
                    db = get_db_sync()
                    user = db_service.get_user_by_uid(db, uid)
                    if user:
                        session_id = context_id or message_id
                        db_service.create_message(
                            db,
                            message_id=f"{message_id}_tool_{tool_name}_start",
                            session_id=session_id,
                            user_id=user.id,
                            role="tool",
                            tool_name=tool_name,
                            tool_input=json.dumps(tool_inputs, ensure_ascii=False),
                            message_type=tool_type,
                            finish_status="running"
                        )
                    db.close()
                except Exception as e:
                    logger.error(f"Failed to save tool start to DB: {e}")

            elif kind == "on_tool_end":
                tool_output = event["data"].get("output", "")
                tool_name = event.get("name", "")
                tool_end_type = self._get_tool_end_type(tool_name)
                
                cleaned_result = self._parse_tool_output(tool_output)
                tool_result = cleaned_result.get("content") or cleaned_result.get("raw") or str(tool_output)

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
                
                try:
                    db = get_db_sync()
                    user = db_service.get_user_by_uid(db, uid)
                    if user:
                        session_id = context_id or message_id
                        db_service.create_message(
                            db,
                            message_id=f"{message_id}_tool_{tool_name}_end",
                            session_id=session_id,
                            user_id=user.id,
                            role="tool",
                            tool_name=tool_name,
                            tool_output=tool_result,
                            message_type=tool_end_type,
                            finish_status="completed"
                        )
                    db.close()
                except Exception as e:
                    logger.error(f"Failed to save tool end to DB: {e}")

            elif kind == "on_agent_finish":
                final_output = event["data"].get("output", "")
                if final_output:
                    final_text = (
                        str(final_output.content) 
                        if hasattr(final_output, 'content') 
                        else str(final_output)
                    )
                    if final_text and final_text != current_content:
                        current_content += final_text
                        stream_chunk = StreamChunk(
                            status=False,
                            content=final_text,
                            message_id=message_id,
                            type=MessageType.TEXT,
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
        
        # 保存 AI 消息到数据库
        try:
            db = get_db_sync()
            user = db_service.get_user_by_uid(db, uid)
            if user:
                session_id = context_id or message_id
                db_service.create_message(
                    db,
                    message_id=message_id,
                    session_id=session_id,
                    user_id=user.id,
                    role="assistant",
                    content=current_content,
                    reasoning_content=current_reasoning_content,
                    message_type=MessageType.TEXT,
                    finish_status="stop"
                )
            db.close()
        except Exception as e:
            logger.error(f"Failed to save AI message to DB: {e}")

        logger.info(f"Agent execution completed for user {uid}, message_id {message_id}")

    async def cleanup_context(self, context_id: str):
        if context_id in self.conversation_history:
            del self.conversation_history[context_id]
            logger.info(f"Cleaned up context {context_id}")


chat_service = ChatService()
