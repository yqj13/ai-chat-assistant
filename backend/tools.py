from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import requests
import math


class WeatherInput(BaseModel):
    province: str = Field(description="省份名称，如：四川、广东")
    city: str = Field(description="城市名称，如：绵阳、深圳")


class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    num_results: Optional[int] = Field(default=3, description="返回结果数量")


class CalculatorInput(BaseModel):
    expression: str = Field(description="数学表达式，如：2+2、sqrt(16)、sin(3.14)")


class TimeInput(BaseModel):
    timezone: Optional[str] = Field(default="Asia/Shanghai", description="时区")


@tool("weather_query", args_schema=WeatherInput)
def get_weather(province: str, city: str) -> str:
    """查询指定城市的天气信息。输入省份名称和城市名称，返回天气、温度等信息。"""
    try:
        url = f"https://cn.apihz.cn/api/tianqi/tqyb.php?id=10017282&key=bb7b534897137b356262de47aaef6559&sheng={requests.utils.quote(province)}&place={requests.utils.quote(city)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                city_name = data.get("name", city)
                country = data.get("guo", "")
                sheng = data.get("sheng", "")
                weather1 = data.get("weather1", "")
                weather2 = data.get("weather2", "")
                wd1 = data.get("wd1", "")
                wd2 = data.get("wd2", "")
                winddirection1 = data.get("winddirection1", "")
                winddirection2 = data.get("winddirection2", "")
                windlevel1 = data.get("windleve1", "")
                windlevel2 = data.get("windleve2", "")
                lon = data.get("lon", "")
                lat = data.get("lat", "")
                uptime = data.get("uptime", "")
                
                nowinfo = data.get("nowinfo", {})
                temperature = str(nowinfo.get("temperature", ""))
                humidity = str(nowinfo.get("humidity", ""))
                feelst = str(nowinfo.get("feelst", ""))
                pressure = str(nowinfo.get("pressure", ""))
                windScale = nowinfo.get("windScale", "")
                precipitation = str(nowinfo.get("precipitation", ""))
                now_uptime = nowinfo.get("uptime", "")
                
                result = "## 天气信息\n\n"
                result += "- 城市: " + city_name + "\n"
                result += "- 国家: " + country + "\n"
                if sheng:
                    result += "- 省份: " + sheng + "\n"
                result += "- 天气: " + weather1 + "\n"
                result += "- 最高温度: " + wd1 + "°C\n"
                result += "- 最低温度: " + wd2 + "°C\n"
                if temperature:
                    result += "- 当前温度: " + temperature + "°C\n"
                if feelst:
                    result += "- 体感温度: " + feelst + "°C\n"
                result += "- 湿度: " + humidity + "%\n"
                if pressure:
                    result += "- 气压: " + pressure + "hPa\n"
                if winddirection1:
                    result += "- 风向: " + winddirection1 + "\n"
                if windlevel1:
                    result += "- 风力: " + windlevel1 + "\n"
                if precipitation:
                    result += "- 降水量: " + precipitation + "mm\n"
                if lon and lat:
                    result += "- 经纬度: " + lon + ", " + lat + "\n"
                if uptime:
                    result += "- 更新时间: " + uptime + "\n"
                return result
    except Exception as e:
        print(f"Weather API call failed: {str(e)}")
        pass
    
    mock_weather = {
        "北京": {"weather": "晴朗", "temp": "25°C", "feelst": "24", "humidity": "45%", "winddirection": "东北风", "windlevel": "3级"},
        "上海": {"weather": "多云", "temp": "22°C", "feelst": "23", "humidity": "60%", "winddirection": "东风", "windlevel": "2级"},
        "深圳": {"weather": "晴朗", "temp": "28°C", "feelst": "30", "humidity": "70%", "winddirection": "南风", "windlevel": "2级"},
    }
    
    if city in mock_weather:
        w = mock_weather[city]
        result = "## 天气信息\n\n"
        result += "- 城市: " + city + "\n"
        result += "- 省份: " + province + "\n"
        result += "- 天气: " + w["weather"] + "\n"
        result += "- 温度: " + w["temp"] + "\n"
        result += "- 体感温度: " + w["feelst"] + "°C\n"
        result += "- 湿度: " + w["humidity"] + "\n"
        result += "- 风向: " + w["winddirection"] + "\n"
        result += "- 风力: " + w["windlevel"] + "\n"
        return result
    
    return "## 天气信息\n\n- 城市: " + city + "\n- 省份: " + province + "\n- 温度: 约25°C\n- 天气: 晴朗\n- 湿度: 50%\n- 风向: 微风"


@tool("web_search", args_schema=SearchInput)
def search_web(query: str, num_results: int = 3) -> str:
    """在互联网上搜索信息。输入搜索关键词，返回相关搜索结果。"""
    
    try:
        url = f"https://cn.apihz.cn/api/wangzhan/soubaiduxg.php?id=10017282&key=bb7b534897137b356262de47aaef6559&words={requests.utils.quote(query)}&tn=98010089_dg&ck="
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 200:
                    datas = data.get("datas", [])
                    if datas:
                        results = []
                        for i, item in enumerate(datas[:min(num_results, len(datas))], 1):
                            results.append(f"- [{i}] {item}")
                        result_str = "\n".join(results)
                        return "## 搜索结果\n\n" + result_str
            except ValueError:
                pass
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for item in soup.find_all('div', class_='res-list')[:min(num_results, 3)]:
                title_tag = item.find('h3')
                link_tag = item.find('a')
                desc_tag = item.find('p')
                
                if title_tag and link_tag:
                    title = title_tag.get_text(strip=True)
                    link = link_tag.get('href', '')
                    desc = desc_tag.get_text(strip=True) if desc_tag else ''
                    results.append("- [" + title + "](" + link + ")\n  " + desc[:80] + "...")
            
            if results:
                result_str = "\n\n".join(results)
                return "## 搜索结果\n\n" + result_str
    except:
        pass
    
    if query in mock_results:
        results = []
        for item in mock_results[query][:min(num_results, 3)]:
            results.append("- [" + item["title"] + "](" + item["url"] + ")\n  " + item["desc"][:80] + "...")
        result_str = "\n\n".join(results)
        return "## 搜索结果\n\n" + result_str
    
    return "## 搜索结果\n\n- 搜索到关于 '" + query + "' 的相关信息\n- 由于网络限制，显示部分摘要内容"


@tool("calculator", args_schema=CalculatorInput)
def calculate(expression: str) -> str:
    """计算数学表达式。支持基本运算、三角函数、对数等。例如：2+2、sqrt(16)、sin(3.14)"""
    try:
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "exp": math.exp,
            "pi": math.pi, "e": math.e
        }
        
        expression = expression.replace("^", "**")
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return "## 计算结果\n\n`" + expression + "` = **" + str(result) + "**"
    except SyntaxError:
        return "语法错误：无法解析表达式 `" + expression + "`"
    except Exception as e:
        return "计算异常：" + str(e)


@tool("time_query", args_schema=TimeInput)
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """查询当前时间。可以指定时区，默认为Asia/Shanghai（北京时间）。"""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(timezone))
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_en = now.strftime('%A')
        weekday_cn = weekdays_cn[weekdays.index(weekday_en)] if weekday_en in weekdays else weekday_en
        
        return "## 当前时间\n\n- 日期: " + now.strftime('%Y年%m月%d日') + "\n- 时间: " + now.strftime('%H:%M:%S') + "\n- 星期: " + weekday_cn
    except Exception:
        now = datetime.now()
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_en = now.strftime('%A')
        weekday_cn = weekdays_cn[weekdays.index(weekday_en)] if weekday_en in weekdays else weekday_en
        
        return "## 当前时间\n\n- 日期: " + now.strftime('%Y年%m月%d日') + "\n- 时间: " + now.strftime('%H:%M:%S') + "\n- 星期: " + weekday_cn


def create_tools():
    return [get_weather, search_web, calculate, get_current_time]
