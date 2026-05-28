from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
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

app = FastAPI(title="AI Chat Assistant API", version="2.0.0")

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
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[Message]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"
    temperature: float = 0.3

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None

conversation_contexts: Dict[str, dict] = {}

TOOLS_JSON_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'等"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索相关信息，获取实时数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行数学计算，支持基本运算和常用数学函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如'2+3*4'、'sin(3.14)'等"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前系统时间和日期",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

TOOL_MAP = {}

def register_tool(name: str, func):
    TOOL_MAP[name] = func

async def get_weather(city: str) -> str:
    try:
        url = f"http://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "results" in data:
                r = data["results"][0]
                city_name = r["location"]["name"]
                now = r["now"]
                text = now["text"]
                temp = now["temperature"]
                humidity = now["humidity"]
                wind = now["windspeedKmph"]
                return f"{city_name}当前天气：{text}，气温 {temp}°C，湿度 {humidity}%，风速 {wind} km/h"
            else:
                return "查询失败：未获取到天气数据"
        else:
            return f"查询失败：HTTP状态码 {resp.status_code}"
    except Exception as e:
        return f"异常：{e}"

async def web_search(query: str) -> str:
    try:
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            for item in soup.find_all('li', class_='b_algo')[:5]:
                title = item.find('h2').get_text() if item.find('h2') else ""
                link = item.find('a')['href'] if item.find('a') else ""
                desc = item.find('p').get_text() if item.find('p') else ""
                if title and link:
                    results.append(f"- [{title}]({link})\n  {desc[:80]}...")
            if results:
                return "\n\n".join(results)
            else:
                return "未找到相关搜索结果"
        else:
            return f"搜索失败：HTTP状态码 {resp.status_code}"
    except Exception as e:
        return f"异常：{e}"

async def calculator(expression: str) -> str:
    try:
        allowed_funcs = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'sqrt': math.sqrt, 'abs': abs,
            'pi': math.pi, 'e': math.e,
            'pow': pow, 'exp': math.exp
        }
        result = eval(expression, {"__builtins__": None}, allowed_funcs)
        return f"计算结果：{expression} = {result}"
    except SyntaxError:
        return f"语法错误：无法解析表达式 '{expression}'"
    except Exception as e:
        return f"计算异常：{e}"

async def get_current_time() -> str:
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}，星期{now.strftime('%A')}"

register_tool("get_weather", get_weather)
register_tool("web_search", web_search)
register_tool("calculator", calculator)
register_tool("get_current_time", get_current_time)

def generate_message_id() -> str:
    return hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:10]

def generate_context_id() -> str:
    return hashlib.md5(f"ctx_{time.time()}{random.random()}".encode()).hexdigest()[:16]

def generate_completion_id() -> str:
    return f"chatcmpl-{hashlib.md5(f'{time.time()}'.encode()).hexdigest()[:24]}"

def detect_need_tool(messages: List[Dict[str, str]]) -> bool:
    last_message = messages[-1]["content"].lower() if messages else ""
    
    tool_triggers = [
        ("天气", "get_weather"),
        ("搜索", "web_search"),
        ("查找", "web_search"),
        ("查询", "web_search"),
        ("计算", "calculator"),
        ("加", "calculator"),
        ("减", "calculator"),
        ("乘", "calculator"),
        ("除", "calculator"),
        ("等于", "calculator"),
        ("时间", "get_current_time"),
        ("几点", "get_current_time")
    ]
    
    for trigger, tool_name in tool_triggers:
        if trigger in last_message:
            return True, tool_name
    
    return False, None

def parse_tool_arguments(user_message: str, tool_name: str) -> Dict[str, Any]:
    user_message = user_message.lower()
    
    if tool_name == "get_weather":
        import re
        city_pattern = r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆|天津|苏州|郑州|长沙|沈阳|青岛|济南|哈尔滨|佛山|东莞|无锡|宁波|合肥|大连|厦门|福州|长春|石家庄)"
        match = re.search(city_pattern, user_message)
        return {"city": match.group(1) if match else "北京"}
    
    elif tool_name == "web_search":
        query = user_message.replace("搜索", "").replace("查找", "").replace("查询", "").strip()
        return {"query": query if query else user_message}
    
    elif tool_name == "calculator":
        expression = user_message
        for char in ["计算", "算一下", "等于", "是多少", "?", "？"]:
            expression = expression.replace(char, "")
        return {"expression": expression.strip()}
    
    elif tool_name == "get_current_time":
        return {}
    
    return {}

async def simulate_model_decision(messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    need_tool, tool_name = detect_need_tool(messages)
    
    if need_tool and tools:
        arguments = parse_tool_arguments(messages[-1]["content"], tool_name)
        
        return {
            "tool_calls": [{
                "id": generate_message_id(),
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }]
        }
    else:
        return {"content": "这是一个普通对话回复。"}

@app.get("/")
async def root():
    return {"message": "AI Chat Assistant API v2.0 is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/tools")
async def list_tools():
    return {"tools": TOOLS_JSON_SCHEMA}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    completion_id = generate_completion_id()
    created = int(time.time())
    
    messages_dict = [m.dict() for m in request.messages]
    
    model_decision = await simulate_model_decision(messages_dict, request.tools)
    
    if "tool_calls" in model_decision:
        tool_call = model_decision["tool_calls"][0]
        function_name = tool_call["function"]["name"]
        function_args = tool_call["function"]["arguments"]
        
        if function_name in TOOL_MAP:
            tool_result = await TOOL_MAP[function_name](**function_args)
            
            tool_message = Message(
                role="tool",
                content=tool_result,
                name=function_name,
                tool_call_id=tool_call["id"]
            )
            
            messages_dict.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            messages_dict.append(tool_message.dict())
            
            final_response = await simulate_model_decision(messages_dict, None)
            
            return ChatCompletionResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_response.get("content", "工具调用完成")
                    },
                    "finish_reason": "tool_calls"
                }]
            )
        else:
            return ChatCompletionResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"未知工具: {function_name}"
                    },
                    "finish_reason": "stop"
                }]
            )
    else:
        return ChatCompletionResponse(
            id=completion_id,
            created=created,
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": model_decision["content"]
                },
                "finish_reason": "stop"
            }]
        )

@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(request: ChatCompletionRequest):
    completion_id = generate_completion_id()
    created = int(time.time())
    
    messages_dict = [m.dict() for m in request.messages]
    
    async def event_generator():
        model_decision = await simulate_model_decision(messages_dict, request.tools)
        
        if "tool_calls" in model_decision:
            tool_call = model_decision["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            
            yield {
                "event": "thinking",
                "data": json.dumps({
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [tool_call]
                        },
                        "finish_reason": None
                    }]
                })
            }
            
            if function_name in TOOL_MAP:
                function_args = tool_call["function"]["arguments"]
                tool_result = await TOOL_MAP[function_name](**function_args)
                
                messages_dict.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages_dict.append({
                    "role": "tool",
                    "content": tool_result,
                    "name": function_name,
                    "tool_call_id": tool_call["id"]
                })
                
                final_response = await simulate_model_decision(messages_dict, None)
                content = final_response.get("content", tool_result)
                
                for i, char in enumerate(content):
                    await asyncio.sleep(0.05)
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": char},
                                "finish_reason": None if i < len(content) - 1 else "stop"
                            }]
                        })
                    }
        else:
            content = model_decision["content"]
            for i, char in enumerate(content):
                await asyncio.sleep(0.05)
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": char},
                            "finish_reason": None if i < len(content) - 1 else "stop"
                        }]
                    })
                }
    
    return EventSourceResponse(event_generator())

@app.get("/connect")
async def connect(request: Request, uid: str, context_id: Optional[str] = None):
    if not context_id:
        context_id = generate_context_id()
    
    if uid not in conversation_contexts:
        conversation_contexts[uid] = {}
    
    if context_id not in conversation_contexts[uid]:
        conversation_contexts[uid][context_id] = {
            "messages": [],
            "status": "connected"
        }
    
    async def event_generator():
        yield {
            "event": "connected",
            "data": json.dumps({
                "context_id": context_id,
                "message": "SSE连接已建立"
            })
        }
        
        while True:
            await asyncio.sleep(1)
            if await request.is_disconnected():
                break
    
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)