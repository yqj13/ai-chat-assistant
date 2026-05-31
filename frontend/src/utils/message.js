export const mapServerMessagesToLocal = (serverMessages) => {
  const grouped = new Map()

  for (const m of serverMessages) {
    const role = m.role
    const baseMsgId = (m.message_id || '').replace(/_(user|tool_.*_(start|end))$/, '')

    if (role === 'user') {
      grouped.set(m.message_id, {
        id: m.message_id,
        role: 'user',
        content: m.content || m.prompt || '',
        timestamp: m.time ? new Date(m.time).getTime() : Date.now()
      })
      continue
    }

    if (role === 'assistant') {
      let item = grouped.get(baseMsgId)
      if (!item) {
        item = {
          id: baseMsgId,
          role: 'assistant',
          parts: [],
          reasoningContent: m.reasoning_content || '',
          timestamp: m.time ? new Date(m.time).getTime() : Date.now(),
          loading: false,
          finished: true,
          collapsed: true,
          thinking: false
        }
        grouped.set(baseMsgId, item)
      }
      item.reasoningContent = m.reasoning_content || item.reasoningContent || ''
      if (m.content) {
        item.parts.push({
          type: 'text',
          content: m.content,
          timestamp: item.timestamp
        })
      }
      continue
    }

    if (role === 'tool') {
      let item = grouped.get(baseMsgId)
      if (!item) {
        item = {
          id: baseMsgId,
          role: 'assistant',
          parts: [],
          reasoningContent: '',
          timestamp: m.time ? new Date(m.time).getTime() : Date.now(),
          loading: false,
          finished: true,
          collapsed: true,
          thinking: false
        }
        grouped.set(baseMsgId, item)
      }
      const isStart = (m.message_id || '').endsWith('_start')
      if (isStart) {
        let params = null
        try { params = m.tool_input ? JSON.parse(m.tool_input) : null } catch (e) { params = { raw: m.tool_input } }
        item.parts.push({
          type: 'tool_call',
          params: { tool: m.tool_name, params },
          result: null,
          timestamp: Date.now(),
          collapsed: true
        })
      } else {
        const lastToolCall = item.parts.findLast
          ? item.parts.findLast(p => p.type === 'tool_call' && !p.result)
          : [...item.parts].reverse().find(p => p.type === 'tool_call' && !p.result)
        const result = { tool: m.tool_name, result: m.tool_output }
        if (lastToolCall) {
          lastToolCall.result = result
        } else {
          item.parts.push({
            type: 'tool_call',
            params: null,
            result,
            timestamp: Date.now(),
            collapsed: true
          })
        }
      }
    }
  }

  return Array.from(grouped.values()).sort((a, b) => a.timestamp - b.timestamp)
}

export const createUserMessage = (content, options = {}) => {
  return {
    id: 'msg_' + Date.now(),
    role: 'user',
    content: content.trim(),
    deepThinking: options.deepThinking || false,
    webSearch: options.webSearch || false,
    timestamp: Date.now()
  }
}

export const createAssistantMessage = (id = null) => {
  return {
    id: id || 'pending_' + Date.now(),
    role: 'assistant',
    parts: [],
    reasoningContent: '',
    timestamp: Date.now(),
    loading: true,
    finished: false
  }
}

export const createTextPart = (content) => {
  return {
    type: 'text',
    content,
    timestamp: Date.now()
  }
}

export const createToolCallPart = (params, result = null) => {
  return {
    type: 'tool_call',
    params,
    result,
    timestamp: Date.now(),
    collapsed: true
  }
}

export const extractTextFromMessage = (message) => {
  if (!message) return ''
  if (typeof message === 'string') return message
  if (message.content) return message.content
  if (message.parts) {
    return message.parts
      .filter(p => p.type === 'text')
      .map(p => p.content)
      .join('')
  }
  return ''
}

export const TOOL_NAME_MAP = {
  'weather_query': '天气查询',
  'time_query': '时间查询',
  'web_search': '联网查询',
  'calculator': '计算器',
}

export const getToolName = (toolData) => {
  if (!toolData) return ''
  return TOOL_NAME_MAP[toolData.tool] || toolData.tool || '未知工具'
}

export const formatValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  return String(value)
}

export const getToolCallTitle = (part) => {
  if (part.type !== 'tool_call') return '工具调用'
  if (part.params && part.result) {
    return `工具调用：${getToolName(part.params)}`
  } else if (part.params) {
    return `正在调用：${getToolName(part.params)}`
  } else if (part.result) {
    return `工具执行完成：${getToolName(part.result)}`
  }
  return '工具调用'
}

export const getParamsTableData = (tool) => {
  const params = tool.data?.params
  if (!params) return []
  return Object.entries(params).map(([key, value], index) => ({
    index: index + 1,
    paramName: key,
    paramValue: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
}

export const getParamsColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'paramName', title: '参数名', width: '120px' },
  { colKey: 'paramValue', title: '参数值', cell: 'paramValue' }
]

const parseMarkdownData = (markdown, fieldMapping = {}) => {
  if (!markdown) return {}
  const data = {}
  const lines = markdown.split('\n')
  
  for (const line of lines) {
    const trimmedLine = line.trim()
    if (trimmedLine.startsWith('- ')) {
      const match = trimmedLine.match(/^-\s*(.+?):\s*(.+)$/)
      if (match) {
        const key = match[1]
        const value = match[2]
        const mappedKey = fieldMapping[key] || key
        data[mappedKey] = value
      }
    } else if (trimmedLine && !trimmedLine.startsWith('#') && trimmedLine.startsWith('-')) {
      const cleanLine = trimmedLine.substring(1).trim()
      if (cleanLine && !Object.keys(data).length) {
        data.result = cleanLine
      }
    }
  }
  return data
}

export const getWeatherTableData = (tool) => {
  const resultData = tool.data?.result
  if (!resultData) return []

  if (typeof resultData === 'string') {
    const data = parseMarkdownData(resultData, {
      '城市': 'city', '国家': 'country', '省份': 'province', '天气': 'weather',
      '最高温度': 'temp_high', '最低温度': 'temp_low', '当前温度': 'current_temp',
      '体感温度': 'feels_like', '湿度': 'humidity', '气压': 'pressure',
      '风向': 'wind_direction', '风力': 'wind_level', '降水量': 'precipitation',
      '经纬度': 'coordinates', '更新时间': 'update_time'
    })
    return formatTableData(data, [
      { label: '城市', key: 'city' }, { label: '国家', key: 'country' },
      { label: '省份', key: 'province' }, { label: '天气', key: 'weather' },
      { label: '最高温度', key: 'temp_high', suffix: '°C' },
      { label: '最低温度', key: 'temp_low', suffix: '°C' },
      { label: '当前温度', key: 'current_temp', suffix: '°C' },
      { label: '体感温度', key: 'feels_like', suffix: '°C' },
      { label: '湿度', key: 'humidity', suffix: '%' },
      { label: '气压', key: 'pressure', suffix: 'hPa' },
      { label: '风向', key: 'wind_direction' }, { label: '风力', key: 'wind_level' },
      { label: '降水量', key: 'precipitation' }, { label: '经纬度', key: 'coordinates' },
      { label: '更新时间', key: 'update_time' }
    ])
  }

  const data = tool.data?.result?.data
  if (!data) return []
  return formatTableData(data, [
    { label: '城市', key: 'city' }, { label: '天气', key: 'weather' },
    { label: '最高温度', key: 'temp_high', suffix: '°C' },
    { label: '最低温度', key: 'temp_low', suffix: '°C' },
    { label: '当前温度', key: 'current_temp', suffix: '°C' },
    { label: '体感温度', key: 'feels_like', suffix: '°C' },
    { label: '湿度', key: 'humidity', suffix: '%' }, { label: '气压', key: 'pressure', suffix: 'hPa' },
    { label: '风向', key: 'wind_direction' }, { label: '风力', key: 'wind_level' },
    { label: '更新时间', key: 'update_time' }
  ])
}

export const getTimeTableData = (tool) => {
  const resultData = tool.data?.result
  if (!resultData) return []

  if (typeof resultData === 'string') {
    const data = parseMarkdownData(resultData, {
      '日期': 'date', '时间': 'time', '星期': 'weekday', '时区': 'timezone',
      '年': 'year', '月': 'month', '日': 'day', '小时': 'hour', '分钟': 'minute', '秒': 'second'
    })
    return formatTableData(data, [
      { label: '日期', key: 'date' }, { label: '时间', key: 'time' },
      { label: '星期', key: 'weekday' }, { label: '时区', key: 'timezone' }
    ])
  }

  const data = tool.data?.result?.data
  if (!data) return []
  return formatTableData(data, [
    { label: '日期', key: 'date' }, { label: '时间', key: 'time' },
    { label: '星期', key: 'weekday' }, { label: '时区', key: 'timezone' }
  ])
}

export const getCalculatorTableData = (tool) => {
  const resultData = tool.data?.result
  if (!resultData) return []

  if (typeof resultData === 'string') {
    const data = parseMarkdownData(resultData)
    if (Object.keys(data).length) {
      return Object.entries(data).map(([key, value], index) => ({
        index: index + 1,
        property: key,
        value: String(value)
      }))
    }
    return [{ index: 1, property: '结果', value: resultData.trim() }]
  }

  const data = tool.data?.result?.data
  if (!data) return []
  return [
    { index: 1, property: '表达式', value: data.expression || '-' },
    { index: 2, property: '计算结果', value: data.result !== undefined ? String(data.result) : '-' }
  ]
}

export const getSearchTableData = (tool) => {
  const resultData = tool.data?.result
  if (!resultData) return []

  if (typeof resultData === 'string') {
    return parseMarkdownSearchResults(resultData)
  }

  const data = tool.data?.result?.data
  if (!data || !data.results) return []
  return data.results.map(item => ({
    title: item.title || '无标题',
    url: item.url || '#',
    snippet: item.snippet || '',
    siteName: item.site_name || '',
    date: item.date || ''
  }))
}

const formatTableData = (data, fields) => {
  return fields
    .filter(field => data[field.key])
    .map((field, index) => ({
      index: index + 1,
      property: field.label,
      value: data[field.key] + (field.suffix || '')
    }))
}

const parseMarkdownSearchResults = (markdown) => {
  if (!markdown) return []
  const results = []
  const lines = markdown.split('\n')
  let currentItem = null

  for (const line of lines) {
    const trimmedLine = line.trim()
    
    if (trimmedLine.startsWith('- [')) {
      if (currentItem && currentItem.title) {
        results.push(currentItem)
      }
      const fullMatch = trimmedLine.match(/^- \[([^\]]+)\]\(([^)]+)\)(?:\s*\(([^)]+)\))?(?:\s*·\s*(\d{4}-\d{2}-\d{2}))?$/)
      
      if (fullMatch) {
        currentItem = {
          title: fullMatch[1] || '无标题',
          url: fullMatch[2] || '#',
          siteName: fullMatch[3] || '',
          snippet: '',
          date: fullMatch[4] || ''
        }
      }
    } else if (trimmedLine.startsWith('  ') && currentItem) {
      const snippetPart = trimmedLine.substring(2).trim()
      if (snippetPart) {
        currentItem.snippet = (currentItem.snippet + ' ' + snippetPart).trim()
      }
    }
  }

  if (currentItem && currentItem.title) {
    results.push(currentItem)
  }

  return results.slice(0, 10)
}

export const getTableColumns = (type = 'default') => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: type === 'default' ? 'property' : 'paramName', title: type === 'default' ? '属性' : '参数名', width: '120px' },
  { colKey: type === 'default' ? 'value' : 'paramValue', title: type === 'default' ? '值' : '参数值', cell: type === 'default' ? 'value' : 'paramValue' }
]
