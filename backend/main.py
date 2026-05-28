from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sse_starlette.sse import EventSourceResponse
import asyncio
import random
import time
import json
import hashlib
from datetime import datetime
import math
import requests
from bs4 import BeautifulSoup
import os

app = FastAPI(title="AI Chat Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "gpt-3.5-turbo"
    context_id: Optional[str] = None
    last_message_id: Optional[str] = None

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None

conversation_contexts: Dict[str, dict] = {}
message_cache: Dict[str, dict] = {}

tools = {
    "weather": {
        "description": "查询指定城市的天气信息",
        "parameters": {
            "city": {"type": "string", "description": "城市名称", "required": True}
        }
    },
    "search": {
        "description": "联网搜索相关信息",
        "parameters": {
            "query": {"type": "string", "description": "搜索关键词", "required": True}
        }
    },
    "calculator": {
        "description": "执行数学计算",
        "parameters": {
            "expression": {"type": "string", "description": "数学表达式", "required": True}
        }
    },
    "time": {
        "description": "获取当前时间",
        "parameters": {}
    }
}

def generate_message_id() -> str:
    return hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:10]

def generate_context_id() -> str:
    return hashlib.md5(f"ctx_{time.time()}{random.random()}".encode()).hexdigest()[:16]

async def mock_stream_response(user_message: str, context_id: str, last_message_id: str):
    responses = [
        "您好！我是AI助手，很高兴为您服务。",
        "您的问题很有趣，让我思考一下...",
        "根据我的分析，",
        "这个问题涉及多个方面，",
        "我来为您详细解答。",
        "\n\n首先，",
        "让我们看看问题的核心要点：",
        "1. 问题的背景和现状",
        "2. 可能的解决方案",
        "3. 实施建议",
        "\n\n总结一下，",
        "希望这些信息对您有帮助！"
    ]
    
    message_id = generate_message_id()
    reasoning_content = "正在分析用户问题，理解上下文，生成合适的回答..."
    
    for i, part in enumerate(responses):
        await asyncio.sleep(0.3)
        data = {
            "message_id": message_id,
            "context_id": context_id,
            "content": part,
            "reasoning_content": reasoning_content if i < 3 else "",
            "finish_status": i == len(responses) - 1,
            "sequence": i + 1
        }
        yield json.dumps(data)

async def tool_weather(city: str) -> ToolResult:
    try:
        url = f"http://wttr.in/{city}?format=j1"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current_condition = data['current_condition'][0]
            result = {
                "city": city,
                "temperature": current_condition['temp_C'],
                "weather": current_condition['weatherDesc'][0]['value'],
                "humidity": current_condition['humidity'],
                "wind": current_condition['windspeedKmph'] + " km/h"
            }
            return ToolResult(tool_name="weather", success=True, result=result)
        else:
            return ToolResult(tool_name="weather", success=False, error="无法获取天气信息")
    except Exception as e:
        return ToolResult(tool_name="weather", success=False, error=str(e))

async def tool_search(query: str) -> ToolResult:
    try:
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for item in soup.find_all('li', class_='b_algo')[:5]:
                title = item.find('h2').get_text() if item.find('h2') else ""
                link = item.find('a')['href'] if item.find('a') else ""
                desc = item.find('p').get_text() if item.find('p') else ""
                if title and link:
                    results.append({"title": title, "link": link, "description": desc})
            return ToolResult(tool_name="search", success=True, result=results)
        else:
            return ToolResult(tool_name="search", success=False, error="搜索失败")
    except Exception as e:
        return ToolResult(tool_name="search", success=False, error=str(e))

async def tool_calculator(expression: str) -> ToolResult:
    try:
        allowed_funcs = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'sqrt': math.sqrt, 'abs': abs,
            'pi': math.pi, 'e': math.e
        }
        result = eval(expression, {"__builtins__": None}, allowed_funcs)
        return ToolResult(tool_name="calculator", success=True, result={"expression": expression, "result": result})
    except Exception as e:
        return ToolResult(tool_name="calculator", success=False, error=str(e))

async def tool_time() -> ToolResult:
    now = datetime.now()
    result = {
        "datetime": now.isoformat(),
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A")
    }
    return ToolResult(tool_name="time", success=True, result=result)

async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
    if tool_name == "weather":
        return await tool_weather(arguments.get("city", ""))
    elif tool_name == "search":
        return await tool_search(arguments.get("query", ""))
    elif tool_name == "calculator":
        return await tool_calculator(arguments.get("expression", ""))
    elif tool_name == "time":
        return await tool_time()
    else:
        return ToolResult(tool_name=tool_name, success=False, error="未知工具")

def detect_tool_call(user_message: str) -> Optional[ToolCall]:
    user_message = user_message.lower()
    
    if "天气" in user_message:
        import re
        city_match = re.search(r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆|天津|苏州|郑州|长沙|沈阳|青岛|济南|哈尔滨|佛山|东莞|无锡|宁波|合肥|大连|厦门|福州|长春|石家庄|常州|泉州|南宁|贵阳|南昌|温州|金华|嘉兴|惠州|徐州|南通|太原|保定|珠海|中山|兰州|台州|烟台|绍兴|潍坊|临沂|唐山|漳州|呼和浩特|廊坊|扬州|洛阳|乌鲁木齐|盐城|汕头|昆明|镇江|盐城|泰州|济宁|盐城|宜昌|邯郸|芜湖|襄阳|淮安|揭阳|连云港|张家口|遵义|江门|湛江|上饶|柳州|舟山|咸阳|九江|衡阳|威海|宁德|阜阳|株洲|莆田|绵阳|宿迁|赣州|邢台|潮州|秦皇岛|肇庆|荆州|许昌|丽水|商丘|宜春|乐山|德阳|泰安|黄冈|蚌埠|新乡|湛江|岳阳|清远|南阳|衡阳|淮安|南充|滁州|龙岩|荆州|蚌埠|宝鸡|德州|安阳|运城|焦作|开封|许昌|平顶山|周口|商丘|信阳|驻马店|三门峡|漯河|鹤壁|濮阳|济源)", user_message)
        city = city_match.group(1) if city_match else "北京"
        return ToolCall(tool_name="weather", arguments={"city": city})
    
    if any(op in user_message for op in ["加", "减", "乘", "除", "等于", "+", "-", "*", "/", "计算", "算一下"]):
        expression = user_message
        for char in ["计算", "算一下", "等于", "是多少", "?"]:
            expression = expression.replace(char, "")
        return ToolCall(tool_name="calculator", arguments={"expression": expression.strip()})
    
    if "时间" in user_message or "几点" in user_message:
        return ToolCall(tool_name="time", arguments={})
    
    if "搜索" in user_message or "查找" in user_message or "查询" in user_message:
        query = user_message.replace("搜索", "").replace("查找", "").replace("查询", "").strip()
        if query:
            return ToolCall(tool_name="search", arguments={"query": query})
    
    return None

@app.get("/")
async def root():
    return {"message": "AI Chat Assistant API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/tools")
async def list_tools():
    return {"tools": tools}

@app.get("/connect")
async def connect(request: Request, uid: str, context_id: Optional[str] = None, last_message_id: Optional[str] = None):
    async def event_generator():
        nonlocal context_id, last_message_id
        
        if not context_id:
            context_id = generate_context_id()
        
        if uid not in conversation_contexts:
            conversation_contexts[uid] = {}
        
        if context_id not in conversation_contexts[uid]:
            conversation_contexts[uid][context_id] = {
                "messages": [],
                "last_message_id": None
            }
        
        context = conversation_contexts[uid][context_id]
        
        if last_message_id and last_message_id in message_cache:
            cached_message = message_cache[last_message_id]
            for i, part in enumerate(cached_message.get("parts", [])):
                await asyncio.sleep(0.1)
                data = {
                    "message_id": last_message_id,
                    "context_id": context_id,
                    "content": part,
                    "reasoning_content": "",
                    "finish_status": i == len(cached_message["parts"]) - 1,
                    "sequence": i + 1
                }
                yield json.dumps(data)
            
            last_message_id = None
        
        yield json.dumps({
            "message_id": generate_message_id(),
            "context_id": context_id,
            "content": "",
            "reasoning_content": "连接已建立，等待消息...",
            "finish_status": False,
            "sequence": 0
        })
        
        while True:
            await asyncio.sleep(1)
            if await request.is_disconnected():
                break
    
    return EventSourceResponse(event_generator())

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content
    context_id = request.context_id or generate_context_id()
    message_id = generate_message_id()
    
    tool_call = detect_tool_call(user_message)
    
    if tool_call:
        tool_result = await call_tool(tool_call.tool_name, tool_call.arguments)
        
        if tool_result.success:
            result_text = f"【工具调用结果】\n\n"
            if tool_call.tool_name == "weather":
                result = tool_result.result
                result_text += f"🌤️ {result['city']}天气信息\n"
                result_text += f"温度：{result['temperature']}°C\n"
                result_text += f"天气：{result['weather']}\n"
                result_text += f"湿度：{result['humidity']}%\n"
                result_text += f"风速：{result['wind']}"
            elif tool_call.tool_name == "calculator":
                result = tool_result.result
                result_text += f"🧮 计算结果\n"
                result_text += f"表达式：{result['expression']}\n"
                result_text += f"结果：{result['result']}"
            elif tool_call.tool_name == "time":
                result = tool_result.result
                result_text += f"🕐 当前时间\n"
                result_text += f"日期：{result['date']}\n"
                result_text += f"时间：{result['time']}\n"
                result_text += f"星期：{result['weekday']}"
            elif tool_call.tool_name == "search":
                results = tool_result.result
                result_text += f"🔍 搜索结果（共{len(results)}条）\n\n"
                for i, item in enumerate(results, 1):
                    result_text += f"{i}. [{item['title']}]({item['link']})\n"
                    result_text += f"   {item['description'][:100]}...\n\n"
            
            return {
                "reply": result_text,
                "message_id": message_id,
                "context_id": context_id,
                "tool_used": tool_call.tool_name
            }
        else:
            return {
                "reply": f"工具调用失败：{tool_result.error}",
                "message_id": message_id,
                "context_id": context_id,
                "tool_used": tool_call.tool_name,
                "tool_error": tool_result.error
            }
    
    reply_content = f"您好！这是AI助手的响应。您的消息是：{user_message}\n\n这是一个模拟回复，实际应用中会连接到真实的AI模型。"
    
    return {
        "reply": reply_content,
        "message_id": message_id,
        "context_id": context_id
    }

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content
    context_id = request.context_id or generate_context_id()
    last_message_id = request.last_message_id
    
    tool_call = detect_tool_call(user_message)
    
    async def event_generator():
        nonlocal context_id
        
        if tool_call:
            yield {
                "event": "thinking",
                "data": json.dumps({
                    "message_id": generate_message_id(),
                    "context_id": context_id,
                    "content": "",
                    "reasoning_content": f"正在调用{tools[tool_call.tool_name]['description']}...",
                    "finish_status": False,
                    "sequence": 0
                })
            }
            
            tool_result = await call_tool(tool_call.tool_name, tool_call.arguments)
            
            message_id = generate_message_id()
            parts = []
            
            if tool_result.success:
                if tool_call.tool_name == "weather":
                    result = tool_result.result
                    parts = [
                        f"【天气查询结果】\n\n",
                        f"🌤️ {result['city']}天气信息\n",
                        f"温度：{result['temperature']}°C\n",
                        f"天气：{result['weather']}\n",
                        f"湿度：{result['humidity']}%\n",
                        f"风速：{result['wind']}"
                    ]
                elif tool_call.tool_name == "calculator":
                    result = tool_result.result
                    parts = [
                        f"【计算结果】\n\n",
                        f"🧮 表达式：{result['expression']}\n",
                        f"结果：{result['result']}"
                    ]
                elif tool_call.tool_name == "time":
                    result = tool_result.result
                    parts = [
                        f"【当前时间】\n\n",
                        f"🕐 {result['date']} {result['time']}\n",
                        f"星期{result['weekday']}"
                    ]
                elif tool_call.tool_name == "search":
                    results = tool_result.result
                    if results:
                        parts = [f"【搜索结果】\n\n"]
                        for item in results[:3]:
                            parts.append(f"🔍 [{item['title']}]\n")
                            parts.append(f"   {item['description'][:50]}...\n\n")
                    else:
                        parts = ["未找到相关结果"]
            else:
                parts = [f"工具调用失败：{tool_result.error}"]
            
            for i, part in enumerate(parts):
                await asyncio.sleep(0.2)
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "message_id": message_id,
                        "context_id": context_id,
                        "content": part,
                        "reasoning_content": "",
                        "finish_status": i == len(parts) - 1,
                        "sequence": i + 1
                    })
                }
            
            message_cache[message_id] = {"parts": parts, "context_id": context_id}
        else:
            async for data in mock_stream_response(user_message, context_id, last_message_id):
                yield {"event": "message", "data": data}
    
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)