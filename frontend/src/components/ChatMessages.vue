<template>
  <div class="chat-messages" ref="chatMessages">
    <div v-for="msg in messages" :key="msg.id" :class="['message-item', msg.role]">
      <div class="message-avatar">
        <img v-if="msg.role === 'user'" :src="userAvatar" alt="用户头像" class="avatar-image" />
        <img v-else :src="aiAvatar" alt="AI头像" class="avatar-image" />
      </div>

      <div class="message-bubble">
        <t-chat-thinking v-if="msg.reasoningContent" :content="{
          title: msg.thinking ? '思考中' : '思考完成',
          text: msg.reasoningContent
        }" :collapsed="msg.collapsed || false" :status="msg.thinking ? 'pending' : 'complete'"
          @collapsed-change="collapsedChangeHandle(msg)">
        </t-chat-thinking>

        <div v-if="msg.loading && (!msg.parts || msg.parts.length === 0) && !msg.reasoningContent"
          class="loading-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>

        <template v-if="msg.parts && msg.parts.length > 0">
          <div v-for="(part, index) in msg.parts" :key="index" class="message-part">
            <div v-if="part.type === 'text'" class="message-content">
              <t-chat-markdown :content="part.content" :options="options" />
            </div>

            <div v-else-if="part.type === 'tool_call'" class="tool-call-item" @click="toggleToolCallCard(part)">
              <div class="tool-call-header">
                <div><ai-tool-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2"
                    style="margin-right: 8px;" />
                  {{ getToolCallTitle(part) }}</div>
                <component :is="part.collapsed ? ChevronDownSIcon : ChevronUpIcon" :fill-color='"transparent"'
                  :stroke-color='"currentColor"' :stroke-width="2" class="tool-call-icon" />
              </div>
              <div v-show="!part.collapsed" class="tool-call-content">
                <div v-if="part.params" class="tool-params-section">
                  <div class="tool-section-title">参数信息</div>
                  <t-table :data="getParamsTableData({ data: part.params })"
                    :columns="getParamsColumns({ data: part.params })" :bordered="true" :stripe="true" size="small"
                    row-key="index" :max-height="250" sticky-header>
                    <template #paramValue="{ row }">
                      <code class="param-value">{{ row.paramValue }}</code>
                    </template>
                  </t-table>
                </div>

                <div v-if="part.result" class="tool-result-section">
                  <div class="tool-section-title">执行结果</div>
                  <div v-if="part.result.tool === 'weather_query'" class="result-table">
                    <t-table :data="getWeatherTableData({ data: part.result })" :columns="getWeatherColumns()"
                      :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #value="{ row }">
                        <span class="result-value">{{ row.value }}</span>
                      </template>
                    </t-table>
                  </div>
                  <div v-else-if="part.result.tool === 'time_query'" class="result-table">
                    <t-table :data="getTimeTableData({ data: part.result })" :columns="getTimeColumns()" :bordered="true"
                      :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #value="{ row }">
                        <span class="result-value">{{ row.value }}</span>
                      </template>
                    </t-table>
                  </div>
                  <div v-else-if="part.result.tool === 'calculator'" class="result-table">
                    <t-table :data="getCalculatorTableData({ data: part.result })" :columns="getCalculatorColumns()"
                      :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #value="{ row }">
                        <span class="result-value">{{ row.value }}</span>
                      </template>
                    </t-table>
                  </div>
                  <div v-else-if="part.result.tool === 'web_search'" class="result-table">
                    <div v-for="(item, idx) in getSearchTableData({ data: part.result })" :key="idx"
                      class="search-result-item">
                      <div class="search-result-title">
                        <a :href="item.url" target="_blank" class="search-link">{{ item.title }}</a>
                        <span v-if="item.siteName" class="site-name">{{ item.siteName }}</span>
                        <span v-if="item.date" class="search-date">{{ item.date }}</span>
                      </div>
                      <div v-if="item.snippet" class="search-result-snippet">{{ item.snippet }}</div>
                    </div>
                  </div>
                  <div v-else class="result-json">
                    <pre>{{ JSON.stringify(part.result, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-if="!msg.parts && msg.content && msg.role === 'assistant'" class="message-content">
          <t-chat-markdown :content="msg.content" :options="options" />
        </div>

        <div v-if="msg.content && msg.role === 'user'" class="message-content">
          {{ msg.content }}
        </div>

        <div class="message-time">
          {{ formatTime(msg.timestamp) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { Steps as TSteps, StepItem as TStepItem, Table as TTable } from 'tdesign-vue-next'
import { Robot2Icon, UserIcon, ChevronDownSIcon, ChevronUpIcon, AiToolIcon } from 'tdesign-icons-vue-next'
import userAvatar from '../assets/user-avatar.png'
import aiAvatar from '../assets/ai-avatar.png'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  currentStreamingId: {
    type: String,
    default: null
  }
})


const chatMessages = ref(null)

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return Math.floor(diff / 60000) + '分钟前'
  } else if (diff < 86400000) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `今天 ${hours}:${minutes}`
  } else if (diff < 172800000) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `昨天 ${hours}:${minutes}`
  } else {
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${month}/${day} ${hours}:${minutes}`
  }
}

const options = ref({
  engine: {
    syntax: {
      mathBlock: {
        engine: 'KaTeX',
      },
      inlineMath: {
        engine: 'KaTeX',
      },
    }
  },
})

const getToolTitle = (tool) => {
  const toolNameMap = {
    'weather_query': '天气查询',
    'time_query': '时间查询',
    'web_search': '联网查询',
    'calculator': '计算器',
  }

  return `工具调用: ${toolNameMap[tool?.data?.tool] || tool.type}`
}

const getToolContent = (tool) => {
  if (!tool || !tool.data) return null
  try {
    const { params, result } = tool.data
    if (params) {
      return { type: 'params', data: params }
    }
    if (result) {
      return { type: 'result', data: result }
    }
    return null
  } catch (e) {
    return null
  }
}

const formatValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  return String(value)
}

const getParamsTableData = (tool) => {
  const params = tool.data?.params
  if (!params) return []
  return Object.entries(params).map(([key, value], index) => ({
    index: index + 1,
    paramName: key,
    paramValue: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
}

const getParamsColumns = (tool) => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'paramName', title: '参数名', width: '120px' },
  { colKey: 'paramValue', title: '参数值', cell: 'paramValue' }
]

const getWeatherTableData = (tool) => {
  const resultData = tool.data?.result

  if (!resultData) return []

  if (typeof resultData === 'string') {
    return parseMarkdownWeatherData(resultData)
  }

  const data = tool.data?.result?.data
  if (!data) return []
  const weatherFields = [
    { label: '城市', key: 'city' },
    { label: '省份', key: 'province' },
    { label: '天气', key: 'weather' },
    { label: '最高温度', key: 'temp_high', suffix: '°C' },
    { label: '最低温度', key: 'temp_low', suffix: '°C' },
    { label: '当前温度', key: 'current_temp', suffix: '°C' },
    { label: '体感温度', key: 'feels_like', suffix: '°C' },
    { label: '湿度', key: 'humidity', suffix: '%' },
    { label: '气压', key: 'pressure', suffix: 'hPa' },
    { label: '风向', key: 'wind_direction' },
    { label: '风力', key: 'wind_level' },
    { label: '更新时间', key: 'update_time' }
  ]
  return weatherFields
    .filter(field => data[field.key])
    .map((field, index) => ({
      index: index + 1,
      property: field.label,
      value: data[field.key] + (field.suffix || '')
    }))
}

const parseMarkdownWeatherData = (markdown) => {
  if (!markdown) return []

  const results = []
  const lines = markdown.split('\n')
  const weatherData = {}

  for (const line of lines) {
    const trimmedLine = line.trim()

    if (trimmedLine.startsWith('- ')) {
      const match = trimmedLine.match(/^- (.+?):\s*(.+)$/)
      if (match) {
        const key = match[1]
        const value = match[2]

        const keyMapping = {
          '城市': 'city',
          '国家': 'country',
          '省份': 'province',
          '天气': 'weather',
          '最高温度': 'temp_high',
          '最低温度': 'temp_low',
          '当前温度': 'current_temp',
          '体感温度': 'feels_like',
          '湿度': 'humidity',
          '气压': 'pressure',
          '风向': 'wind_direction',
          '风力': 'wind_level',
          '降水量': 'precipitation',
          '经纬度': 'coordinates',
          '更新时间': 'update_time'
        }

        const mappedKey = keyMapping[key]
        if (mappedKey) {
          weatherData[mappedKey] = value
        }
      }
    }
  }

  const weatherFields = [
    { label: '城市', key: 'city' },
    { label: '国家', key: 'country' },
    { label: '省份', key: 'province' },
    { label: '天气', key: 'weather' },
    { label: '最高温度', key: 'temp_high', suffix: '°C' },
    { label: '最低温度', key: 'temp_low', suffix: '°C' },
    { label: '当前温度', key: 'current_temp', suffix: '°C' },
    { label: '体感温度', key: 'feels_like', suffix: '°C' },
    { label: '湿度', key: 'humidity', suffix: '%' },
    { label: '气压', key: 'pressure', suffix: 'hPa' },
    { label: '风向', key: 'wind_direction' },
    { label: '风力', key: 'wind_level' },
    { label: '降水量', key: 'precipitation' },
    { label: '经纬度', key: 'coordinates' },
    { label: '更新时间', key: 'update_time' }
  ]

  return weatherFields
    .filter(field => weatherData[field.key])
    .map((field, index) => ({
      index: index + 1,
      property: field.label,
      value: weatherData[field.key] + (field.suffix || '')
    }))
}

const getWeatherColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getTimeColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getCalculatorTableData = (tool) => {
  const resultData = tool.data?.result

  if (!resultData) return []

  if (typeof resultData === 'string') {
    return parseMarkdownCalculatorData(resultData)
  }

  const data = tool.data?.result?.data
  if (!data) return []
  return [
    { index: 1, property: '表达式', value: data.expression || '-' },
    { index: 2, property: '计算结果', value: data.result !== undefined ? String(data.result) : '-' }
  ]
}

const parseMarkdownCalculatorData = (markdown) => {
  if (!markdown) return []

  const lines = markdown.split('\n')
  const result = []
  let index = 1

  for (const line of lines) {
    const trimmedLine = line.trim()

    if (trimmedLine.startsWith('- ')) {
      const match = trimmedLine.match(/^-\s*(.+?):\s*(.+)$/)
      if (match) {
        result.push({
          index: index++,
          property: match[1].trim(),
          value: match[2].trim()
        })
      }
    } else if (trimmedLine && !trimmedLine.startsWith('#')) {
      result.push({
        index: index++,
        property: '结果',
        value: trimmedLine
      })
    }
  }

  return result.length > 0 ? result : [{ index: 1, property: '结果', value: markdown.trim() }]
}

const getTimeTableData = (tool) => {
  const resultData = tool.data?.result

  if (!resultData) return []

  if (typeof resultData === 'string') {
    return parseMarkdownTimeData(resultData)
  }

  const data = tool.data?.result?.data
  if (!data) return []
  const timeFields = [
    { label: '日期', key: 'date' },
    { label: '时间', key: 'time' },
    { label: '星期', key: 'weekday' },
    { label: '时区', key: 'timezone' }
  ]
  return timeFields
    .filter(field => data[field.key])
    .map((field, index) => ({
      index: index + 1,
      property: field.label,
      value: data[field.key]
    }))
}

const parseMarkdownTimeData = (markdown) => {
  if (!markdown) return []

  const lines = markdown.split('\n')
  const timeData = {}

  for (const line of lines) {
    const trimmedLine = line.trim()

    if (trimmedLine.startsWith('- ')) {
      const match = trimmedLine.match(/^-\s*(.+?):\s*(.+)$/)
      if (match) {
        const key = match[1]
        const value = match[2]

        const keyMapping = {
          '日期': 'date',
          '时间': 'time',
          '星期': 'weekday',
          '时区': 'timezone',
          '年': 'year',
          '月': 'month',
          '日': 'day',
          '小时': 'hour',
          '分钟': 'minute',
          '秒': 'second'
        }

        const mappedKey = keyMapping[key]
        if (mappedKey) {
          timeData[mappedKey] = value
        }
      }
    }
  }

  const timeFields = [
    { label: '日期', key: 'date' },
    { label: '时间', key: 'time' },
    { label: '星期', key: 'weekday' },
    { label: '时区', key: 'timezone' }
  ]

  return timeFields
    .filter(field => timeData[field.key])
    .map((field, index) => ({
      index: index + 1,
      property: field.label,
      value: timeData[field.key]
    }))
}

const getCalculatorColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getSearchTableData = (tool) => {
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
    siteName: item.site_name || ''
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

const scrollToBottom = async () => {
  await nextTick()
  if (chatMessages.value) {
    const children = chatMessages.value.children
    const lastMessage = children[children.length - 1]
    if (lastMessage) {
      lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }
}

const collapsedChangeHandle = (msg) => {
  msg.collapsed = !msg.collapsed;
  console.log('思考内容折叠状态变化:', msg.collapsed)
}

const toggleToolCalls = (msg) => {
  msg.toolCallsCollapsed = !msg.toolCallsCollapsed;
  console.log('工具调用折叠状态变化:', msg.toolCallsCollapsed)
}

const toggleToolCallCard = (part) => {
  if (part.type === 'tool_call') {
    part.collapsed = !part.collapsed
  }
}

const getToolCallTitle = (part) => {
  if (part.type === 'tool_call') {
    if (part.params && part.result) {
      return `工具调用：${getToolName(part.params)}`
    } else if (part.params) {
      return `正在调用：${getToolName(part.params)}`
    } else if (part.result) {
      return `工具执行完成：${getToolName(part.result)}`
    }
  }
  return '工具调用'
}

const getToolName = (toolData) => {
  if (!toolData) return ''
  const toolNameMap = {
    'weather_query': '天气查询',
    'time_query': '时间查询',
    'web_search': '联网查询',
    'calculator': '计算器',
  }
  return toolNameMap[toolData.tool] || toolData.tool || '未知工具'
}



const handleComplete = (msg) => {
  console.log('消息渲染完成:', msg.id)
  scrollToBottom()
}

watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  }
)



watch(
  () => props.messages.map(msg => ({
    reasoningContent: msg.reasoningContent,
    toolCalls: msg.toolCalls,
    content: msg.content,
  })),
  () => {
    scrollToBottom()
  },
  { deep: true }
)

onMounted(() => {
  scrollToBottom()
})

defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  padding-bottom: 60px;
  scroll-behavior: smooth;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 88%;
  animation: messageSlideIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-item.assistant {
  margin-right: auto;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-item:hover .message-avatar {
  transform: scale(1.05);
}


.message-bubble {
  padding: 16px 20px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
  min-width: 60px;
  word-break: break-word;
  max-width: 100%;
  transition: box-shadow 0.3s ease, transform 0.2s ease;
}

.message-item:hover .message-bubble {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1), 0 2px 6px rgba(0, 0, 0, 0.06);
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: white;
  border-bottom-right-radius: 6px;
}

.message-item.assistant .message-bubble {
  background: #ffffff;
  border-bottom-left-radius: 6px;
  border: 1px solid #f0f0f0;
}

.user-text {
  white-space: pre-wrap;
  font-size: 15px;
  line-height: 1.7;
}

.message-content {
  font-size: 15px;
  line-height: 1.7;
  color: #1e293b;
}

.message-item.user .message-content {
  color: white;
}

.message-time {
  margin-top: 10px;
  font-size: 11px;
  color: #94a3b8;
  text-align: right;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.message-item.user .message-time {
  color: rgba(255, 255, 255, 0.8);
  text-align: right;
}

.message-item.assistant .message-time {
  color: #94a3b8;
  text-align: left;
}

.message-item:hover .message-time {
  opacity: 1;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 4px;
}

.loading-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #1890ff;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.reasoning-header {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tool-calls-section {
  margin: 14px 0;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  position: relative;
}

.tool-content-wrapper {
  width: 100%;
}

.tool-params-section,
.tool-result-section {
  margin-top: 14px;
}

.tool-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.param-value {
  background: #e2e8f0;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 12px;
  color: #1e293b;
}

.result-value {
  color: #1e293b;
  font-weight: 500;
}

.result-table {
  margin-top: 10px;
}

.result-json {
  background: #1e293b;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.result-json pre {
  margin: 0;
  font-size: 12px;
  color: #e2e8f0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
}

.search-result-item {
  margin-bottom: 14px;
  padding: 14px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.search-result-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.search-result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.search-link {
  color: #1890ff;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.search-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

.site-name {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}

.search-date {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 8px;
  padding-left: 8px;
  border-left: 1px solid #e2e8f0;
}

.search-result-snippet {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
}

.message-part {
  margin-bottom: 14px;
}

.message-part:last-child {
  margin-bottom: 0;
}

.tool-call-item {
  margin: 14px 0;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.tool-call-header {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

.tool-call-header:hover {
  color: #1e293b;
}

.tool-call-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.25s ease;
}

.tool-call-item:hover {
  border-color: #cbd5e1;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.tool-call-content {
  margin-top: 14px;
  animation: expandDown 0.2s ease;
}

@keyframes expandDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tool-params-section,
.tool-result-section {
  margin-top: 14px;
}

.tool-params-section:first-child,
.tool-result-section:first-child {
  margin-top: 0;
}

.tool-params-section + .tool-result-section {
  border-top: 1px dashed #cbd5e1;
  padding-top: 14px;
  margin-top: 18px;
}

.tool-calls-header {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 14px;
}

.icon {
  position: absolute;
  top: 12px;
  right: 12px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.icon:hover {
  transform: scale(1.1);
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background-color: #94a3b8;
}

.chat-messages::-webkit-scrollbar-thumb:active {
  background-color: #64748b;
}
</style>