import asyncio
import json
from typing import Dict, Optional, AsyncGenerator
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        self.message_cache: Dict[str, Dict[str, list]] = defaultdict(dict)
        self.current_message: Dict[str, str] = {}
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def send_message(
        self, 
        uid: str, 
        message_id: str, 
        content: str
    ) -> None:
        async with self.locks[uid]:
            if message_id not in self.message_cache[uid]:
                self.message_cache[uid][message_id] = []
            
            self.message_cache[uid][message_id].append(content)
            self.current_message[uid] = message_id
            
            logger.info(f"Cached message for user {uid}, message_id {message_id}")
    
    async def get_cached_messages(
        self, 
        uid: str, 
        last_message_id: Optional[str] = None
    ) -> list:
        async with self.locks[uid]:
            if uid not in self.message_cache:
                return []
            
            current_id = self.current_message.get(uid)
            if not current_id:
                return []
            
            if last_message_id and last_message_id == current_id:
                return self.message_cache[uid].get(current_id, [])
            
            return []
    
    async def stream_generator(
        self, 
        uid: str, 
        message_id: str,
        timeout: int = 60
    ) -> AsyncGenerator[str, None]:
        start_time = asyncio.get_event_loop().time()
        last_index = 0
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"Stream timeout for user {uid}")
                break
            
            async with self.locks[uid]:
                messages = self.message_cache[uid].get(message_id, [])
                
                while last_index < len(messages):
                    msg = messages[last_index]
                    yield f"data: {msg}\n\n"
                    last_index += 1
                    
                    try:
                        msg_data = json.loads(msg)
                        if msg_data.get("finish_status") or msg_data.get("status"):
                            logger.info(f"Stream completed for user {uid}")
                            return
                    except json.JSONDecodeError:
                        pass
            
            await asyncio.sleep(0.1)
    
    async def cleanup_message(self, uid: str, message_id: str) -> None:
        async with self.locks[uid]:
            if uid in self.message_cache and message_id in self.message_cache[uid]:
                del self.message_cache[uid][message_id]
                logger.info(f"Cleaned up message {message_id} for user {uid}")
    
    async def cleanup_user(self, uid: str) -> None:
        async with self.locks[uid]:
            if uid in self.message_cache:
                del self.message_cache[uid]
            if uid in self.current_message:
                del self.current_message[uid]
            logger.info(f"Cleaned up all messages for user {uid}")


sse_manager = SSEManager()