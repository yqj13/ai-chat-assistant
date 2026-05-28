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

from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent

app = FastAPI(title="AI Chat Assistant API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BAILIAN_API_KEY = "sk-14641f425c314266ae08926dd641296a"
BAILIAN_API_BASE = "https://api.qnaigc.com/v1"

llm = ChatOpenAI(
    model="qwen-7b-chat",
    api_key=BAILIAN_API_KEY,
    base_url=BAILIAN_API_BASE,
    temperature=0.3,
    streaming=True
)

conversation_contexts: Dict[str, dict] = {}
message_cache: Dict[str, dict] = {}

class GetWeatherTool(BaseTool):
    name = "get_weather"
    description = "获取指定城市的当前天气信息"

    def _run(self, city: str) -> str:
        try:
            url = f"http://wttr.in/{city}?format=j1"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "results" in data and len(data["results"]) > 0:
                    r = data["results"][0]
                    city_name = r["location"]["name"]
                    current = r["current_condition"][0]
                    return f"## 🌤️ {city_name}天气信息\n\n- **温度**: {current['temp_C']}°C\n- **天气**: {current['weatherDesc'][0]['value']}\n- **湿度**: {current['humidity']}%\n- **风速**: {current['windspeedKmph']} km/h"
                else:
                    return "❌ 查询失败：未获取到天气数据"
            else:
                return f"❌ 查询失败：HTTP状态码 {resp.status_code}"
        except Exception as e:
            return f"❌ 异常：{e}"

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "联网搜索相关信息，获取实时数据"

    def _run(self, query: str) -> str:
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
                        results.append(f"- [{title}]({link})\n  {desc[:100]}...")
                if results:
                    return f"## 🔍 搜索结果（{query}）\n\n" + "\n\n".join(results)
                else:
                    return "❌ 未找到相关搜索结果"
            else:
                return f"❌ 搜索失败：HTTP状态码 {resp.status_code}"
        except Exception as e:
            return f"❌ 异常：{e}"

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算，支持基本运算和常用数学函数"

    def _run(self, expression: str) -> str:
        try:
            allowed_funcs = {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'sqrt': math.sqrt, 'abs': abs,
                'pi': math.pi, 'e': math.e,
                'pow': pow, 'exp': math.exp
            }
            result = eval(expression, {"__builtins__": None}, allowed_funcs)
            return f"## 🧮 计算结果\n\n`{expression}` = **{result}**"
        except SyntaxError:
            return f"❌ 语法错误：无法解析表达式 `{expression}`"
        except Exception as e:
            return f"❌ 计算异常：{e}"

class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "获取当前系统时间和日期"

    def _run(self) -> str:
        now = datetime.now()
        return f"## 🕐 当前时间\n\n- **日期**: {now.strftime('%Y年%m月%d日')}\n- **时间**: {now.strftime('%H:%M:%S')}\n- **星期**: {now.strftime('%A')}"

tools = [
    GetWeatherTool(),
    WebSearchTool(),
    CalculatorTool(),
    GetCurrentTimeTool()
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手。使用提供的工具来回答问题。"),
    ("user", "{input}"),
    ("agent_info", "{agent_info}")
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def generate_message_id() -> str:
    return hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:10]

def generate_context_id() -> str:
    return hashlib.md5(f"ctx_{time.time()}{random.random()}".encode()).hexdigest()[:16]

def generate_completion_id() -> str:
    return f"chatcmpl-{hashlib.md5(f'{time.time()}'.encode()).hexdigest()[:24]}"

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "qwen-7b-chat"
    messages: List[Message]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"
    temperature: float = 0.3
    context_id: Optional[str] = None
    last_message_id: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "AI Chat Assistant API v3.0 (LangChain + 阿里百炼)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/tools")
async def list_tools():
    tool_list = []
    for tool in tools:
        tool_list.append({
            "name": tool.name,
            "description": tool.description
        })
    return {"tools": tool_list}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    completion_id = generate_completion_id()
    created = int(time.time())
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content
    
    try:
        result = await agent_executor.ainvoke({"input": user_message})
        reply_content = result.get("output", "暂无响应")
        
        return ChatCompletionResponse(
            id=completion_id,
            created=created,
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_content
                },
                "finish_reason": "stop"
            }]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(request: ChatCompletionRequest):
    completion_id = generate_completion_id()
    created = int(time.time())
    context_id = request.context_id or generate_context_id()
    last_message_id = request.last_message_id
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content
    
    if last_message_id and last_message_id in message_cache:
        cached_message = message_cache[last_message_id]
        
        async def replay_cache():
            for i, part in enumerate(cached_message.get("parts", [])):
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": request.model,
                        "context_id": context_id,
                        "message_id": last_message_id,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": part},
                            "finish_reason": None if i < len(cached_message["parts"]) - 1 else "stop"
                        }]
                    })
                }
                await asyncio.sleep(0.05)
        return EventSourceResponse(replay_cache())
    
    async def event_generator():
        nonlocal context_id
        
        try:
            full_response = ""
            parts = []
            
            async for chunk in agent_executor.astream({"input": user_message}):
                if "output" in chunk:
                    content = chunk["output"]
                    if content:
                        delta = content[len(full_response):]
                        if delta:
                            full_response = content
                            parts.append(delta)
                            
                            yield {
                                "event": "message",
                                "data": json.dumps({
                                    "id": completion_id,
                                    "object": "chat.completion.chunk",
                                    "created": created,
                                    "model": request.model,
                                    "context_id": context_id,
                                    "message_id": completion_id[:10],
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": delta},
                                        "finish_reason": None
                                    }]
                                })
                            }
                            await asyncio.sleep(0.05)
            
            if full_response:
                message_cache[completion_id[:10]] = {
                    "parts": parts,
                    "context_id": context_id,
                    "full_content": full_response,
                    "timestamp": time.time()
                }
                
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": request.model,
                        "context_id": context_id,
                        "message_id": completion_id[:10],
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    })
                }
        
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e)
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
                "message": "SSE连接已建立",
                "available_tools": [tool.name for tool in tools]
            })
        }
        
        while True:
            await asyncio.sleep(1)
            if await request.is_disconnected():
                break
    
    return EventSourceResponse(event_generator())

@app.get("/context/{uid}")
async def get_context(uid: str):
    if uid in conversation_contexts:
        return conversation_contexts[uid]
    else:
        return {"error": "Context not found"}

@app.delete("/context/{uid}/{context_id}")
async def delete_context(uid: str, context_id: str):
    if uid in conversation_contexts and context_id in conversation_contexts[uid]:
        del conversation_contexts[uid][context_id]
        return {"message": "Context deleted"}
    else:
        raise HTTPException(status_code=404, detail="Context not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)