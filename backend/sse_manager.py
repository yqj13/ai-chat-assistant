import asyncio
import json
from typing import Dict, Optional, AsyncGenerator
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        # uid -> message_id -> [messages]
        self.message_cache: Dict[str, Dict[str, list]] = defaultdict(dict)
        # uid -> current active message_id
        self.current_message: Dict[str, str] = {}
        # uid -> message_id -> sequence
        self.message_sequences: Dict[str, Dict[str, int]] = defaultdict(dict)
        # uid -> asyncio.Event (通知有新消息)
        self.new_message_events: Dict[str, asyncio.Event] = {}
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _get_event(self, uid: str) -> asyncio.Event:
        if uid not in self.new_message_events:
            self.new_message_events[uid] = asyncio.Event()
        return self.new_message_events[uid]

    async def send_message(
        self,
        uid: str,
        message_id: str,
        content: str
    ) -> None:
        async with self.locks[uid]:
            if message_id not in self.message_cache[uid]:
                self.message_cache[uid][message_id] = []
                self.message_sequences[uid][message_id] = 0

            self.message_sequences[uid][message_id] += 1
            sequence = self.message_sequences[uid][message_id]

            # 注入 sequence 到消息中
            try:
                msg_data = json.loads(content)
                msg_data["sequence"] = sequence
                content = json.dumps(msg_data, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

            self.message_cache[uid][message_id].append(content)
            self.current_message[uid] = message_id

            logger.debug(f"Cached message for user {uid}, message_id {message_id}, seq {sequence}")

        # 通知 stream_generator 有新消息
        event = self._get_event(uid)
        event.set()

    async def get_cached_messages(
        self,
        uid: str,
        message_id: str,
        from_sequence: int = 0
    ) -> list:
        """获取某个 message_id 从 from_sequence 开始的缓存消息"""
        async with self.locks[uid]:
            if uid not in self.message_cache:
                return []
            messages = self.message_cache[uid].get(message_id, [])
            # from_sequence 是基于1的，列表索引基于0
            if from_sequence > 0 and from_sequence <= len(messages):
                return messages[from_sequence - 1:]
            return messages

    async def stream_generator(
        self,
        uid: str,
        message_id: Optional[str] = None,
        last_sequence: int = 0,
        timeout: int = 120
    ) -> AsyncGenerator[str, None]:
        """
        SSE 流生成器
        - message_id: 如果提供，表示断点续传，从该 message_id 的 last_sequence 之后开始
        - last_sequence: 客户端已收到的最后一个 sequence
        """
        start_time = asyncio.get_event_loop().time()
        last_index = 0
        current_message_id = message_id
        event = self._get_event(uid)

        # 断点续传：回放缓存消息
        if current_message_id and last_sequence > 0:
            async with self.locks[uid]:
                messages = self.message_cache[uid].get(current_message_id, [])
                # 从 last_sequence 之后开始发送
                last_index = last_sequence
                for i in range(last_sequence, len(messages)):
                    msg = messages[i]
                    yield f"data: {msg}\n\n"
                    last_index = i + 1

                    # 检查是否已完成
                    try:
                        msg_data = json.loads(msg)
                        if msg_data.get("status") is True:
                            logger.info(f"Stream completed (cached) for user {uid}")
                            return
                    except json.JSONDecodeError:
                        pass
        elif current_message_id:
            # 有 message_id 但 last_sequence=0，回放所有消息
            async with self.locks[uid]:
                messages = self.message_cache[uid].get(current_message_id, [])
                for i in range(len(messages)):
                    msg = messages[i]
                    yield f"data: {msg}\n\n"
                    last_index = i + 1

                    try:
                        msg_data = json.loads(msg)
                        if msg_data.get("status") is True:
                            logger.info(f"Stream completed (full replay) for user {uid}")
                            return
                    except json.JSONDecodeError:
                        pass

        # 实时推送新消息
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"Stream timeout for user {uid}")
                break

            # 等待新消息通知，带超时
            try:
                await asyncio.wait_for(event.wait(), timeout=1.0)
                event.clear()
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield f": heartbeat\n\n"
                continue

            # 读取新消息
            async with self.locks[uid]:
                if not current_message_id:
                    current_message_id = self.current_message.get(uid)
                    if not current_message_id:
                        continue
                    last_index = 0

                # 检查是否切换了 message_id
                active_message_id = self.current_message.get(uid)
                if active_message_id and active_message_id != current_message_id:
                    # 新的对话开始了，切换到新的 message_id
                    current_message_id = active_message_id
                    last_index = 0

                messages = self.message_cache[uid].get(current_message_id, [])

                while last_index < len(messages):
                    msg = messages[last_index]
                    yield f"data: {msg}\n\n"
                    last_index += 1

                    try:
                        msg_data = json.loads(msg)
                        if msg_data.get("status") is True:
                            logger.info(f"Stream completed for user {uid}")
                            return
                    except json.JSONDecodeError:
                        pass

    async def cleanup_message(self, uid: str, message_id: str) -> None:
        async with self.locks[uid]:
            if uid in self.message_cache and message_id in self.message_cache[uid]:
                del self.message_cache[uid][message_id]
                if message_id in self.message_sequences.get(uid, {}):
                    del self.message_sequences[uid][message_id]
                logger.info(f"Cleaned up message {message_id} for user {uid}")

    async def cleanup_user(self, uid: str) -> None:
        async with self.locks[uid]:
            if uid in self.message_cache:
                del self.message_cache[uid]
            if uid in self.current_message:
                del self.current_message[uid]
            if uid in self.message_sequences:
                del self.message_sequences[uid]
            if uid in self.new_message_events:
                del self.new_message_events[uid]
            logger.info(f"Cleaned up all messages for user {uid}")


sse_manager = SSEManager()