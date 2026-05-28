from tools import create_tools, get_current_time, calculate, get_weather, search_web

print("=== 直接测试工具函数 ===")

print("\n1. 测试时间查询工具:")
result = get_current_time()
print("结果:", result)

print("\n2. 测试计算器工具:")
result = calculate("sqrt(16) + 10")
print("结果:", result)

print("\n3. 测试天气查询工具:")
result = get_weather("北京")
print("结果:", result)

print("\n4. 测试搜索工具:")
result = search_web("人工智能")
print("结果:", result)

print("\n=== 测试LangChain工具封装 ===")
tools = create_tools()
print(f"\n创建的工具列表:")
for tool in tools:
    print(f"- {tool.name}: {tool.description}")

print("\n=== 测试工具调用 ===")
time_tool = None
for tool in tools:
    if tool.name == "time_query":
        time_tool = tool
        break

if time_tool:
    print(f"调用工具: {time_tool.name}")
    try:
        result = time_tool.run({})
        print("工具返回:", result)
    except Exception as e:
        print("工具调用失败:", str(e))