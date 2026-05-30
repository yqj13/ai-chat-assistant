import asyncio
from chat_service import ChatService

async def test_agent():
    print("=== 测试Agent工具调用 ===")
    
    chat_service = ChatService()
    print(f"可用工具: {[tool.name for tool in chat_service.tools]}")
    
    print("\n测试时间查询:")
    message_id = await chat_service.chat_stream(
        content="现在几点了？",
        uid="debug_user"
    )
    print(f"消息ID: {message_id}")
    
    await asyncio.sleep(3)
    
    print("\n测试计算器:")
    message_id = await chat_service.chat_stream(
        content="计算 sqrt(16) + 10",
        uid="debug_user"
    )
    print(f"消息ID: {message_id}")
    
    await asyncio.sleep(3)
    
    print("\n测试完成")

if __name__ == "__main__":
    asyncio.run(test_agent())