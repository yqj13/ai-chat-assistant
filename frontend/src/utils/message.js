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
