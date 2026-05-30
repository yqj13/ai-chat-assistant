<template>
  <div class="chat-messages" ref="chatMessages">
    <div v-for="msg in messages" :key="msg.id" :class="['message-item', msg.role]">
      <div class="message-avatar">
        <div v-if="msg.role === 'user'">
          <user-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2"/>
        </div>
        <div v-else>
          <robot-2-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2"/>
        </div>
      </div>

      <div class="message-bubble">
        <t-chat-thinking
          v-if="msg.reasoningContent"
          :content="{
            title: msg.thinking ? '思考中' : '思考完成',
            text: msg.reasoningContent
          }"
          :collapsed="msg.collapsed || false"
          :status="msg.thinking? 'pending': 'complete'"
          @collapsed-change="collapsedChangeHandle(msg)"
        >
          <template #header>
            <div class="reasoning-header">💭 思考过程</div>
          </template>
        </t-chat-thinking>

        <div v-if="msg.loading && !msg.content && !msg.reasoningContent" class="loading-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>

        <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-calls-section">
          <div class="tool-calls-header">🔧 工具调用</div>
          <div class="icon"  @click="toggleToolCalls(msg)">
            <component :is="msg.toolCallsCollapsed ? ChevronDownSIcon : ChevronUpIcon" :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2" />
          </div>
          <t-steps :current="msg.toolCalls.length - 1" :readonly="true" layout="vertical" v-if="!msg.toolCallsCollapsed">
            <t-step-item
              v-for="(tool, index) in msg.toolCalls"
              :key="index"
              :title="getToolTitle(tool)"
              :status="index < msg.toolCalls.length - 1 ? 'default' : 'process'"
            >
              <template #content>
                <div v-if="getToolContent(tool)" class="tool-content-wrapper">
                  <div v-if="getToolContent(tool).type === 'params'" class="tool-params-section">
                    <div class="tool-section-title">参数信息</div>
                    <t-table :data="getParamsTableData(tool)" :columns="getParamsColumns(tool)" :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #paramValue="{ row }">
                        <code class="param-value">{{ row.paramValue }}</code>
                      </template>
                    </t-table>
                  </div>
                  
                  <div v-else-if="getToolContent(tool).type === 'result'" class="tool-result-section">
                    <div class="tool-section-title">执行结果</div>
                    <div v-if="tool.data.tool === 'weather_query'" class="result-table">
                      <t-table :data="getWeatherTableData(tool)" :columns="getWeatherColumns()" :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                        <template #value="{ row }">
                          <span class="result-value">{{ row.value }}</span>
                        </template>
                      </t-table>
                    </div>
                    <div v-else-if="tool.data.tool === 'time_query'" class="result-table">
                      <t-table :data="getTimeTableData(tool)" :columns="getTimeColumns()" :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                        <template #value="{ row }">
                          <span class="result-value">{{ row.value }}</span>
                        </template>
                      </t-table>
                    </div>
                    <div v-else-if="tool.data.tool === 'calculator'" class="result-table">
                      <t-table :data="getCalculatorTableData(tool)" :columns="getCalculatorColumns()" :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                        <template #value="{ row }">
                          <span class="result-value">{{ row.value }}</span>
                        </template>
                      </t-table>
                    </div>
                    <div v-else-if="tool.data.tool === 'web_search'" class="result-table">
                      <div v-for="(item, idx) in getSearchTableData(tool)" :key="idx" class="search-result-item">
                        <div class="search-result-title">
                          <a :href="item.url" target="_blank" class="search-link">{{ item.title }}</a>
                          <span v-if="item.siteName" class="site-name">{{ item.siteName }}</span>
                        </div>
                        <div v-if="item.snippet" class="search-result-snippet">{{ item.snippet }}</div>
                      </div>
                    </div>
                    <div v-else class="result-json">
                      <pre>{{ JSON.stringify(getToolContent(tool).data, null, 2) }}</pre>
                    </div>
                  </div>
                </div>
              </template>
            </t-step-item>
          </t-steps>
        </div>

        <div v-if="msg.content && msg.role === 'assistant'" class="message-content">
          <t-chat-markdown :content="msg.content" :options="options" />
        </div>

        <div v-if="msg.content && msg.role === 'user'" class="message-content">
          {{ msg.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { Steps as TSteps, StepItem as TStepItem, Table as TTable } from 'tdesign-vue-next'
import { Robot2Icon, UserIcon, ChevronDownSIcon, ChevronUpIcon } from 'tdesign-icons-vue-next'

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

const getWeatherColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getTimeTableData = (tool) => {
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

const getTimeColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getCalculatorTableData = (tool) => {
  const data = tool.data?.result?.data
  if (!data) return []
  return [
    { index: 1, property: '表达式', value: data.expression || '-' },
    { index: 2, property: '计算结果', value: data.result !== undefined ? String(data.result) : '-' }
  ]
}

const getCalculatorColumns = () => [
  { colKey: 'index', title: '序号', width: '60px' },
  { colKey: 'property', title: '属性', width: '120px' },
  { colKey: 'value', title: '值', cell: 'value' }
]

const getSearchTableData = (tool) => {
  const data = tool.data?.result?.data
  if (!data || !data.results) return []
  return data.results.map(item => ({
    title: item.title || '无标题',
    url: item.url || '#',
    snippet: item.snippet || '',
    siteName: item.site_name || ''
  }))
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
  console.log('折叠状态变化:', msg.collapsed)
}

const toggleToolCalls = (msg) => {
  msg.toolCallsCollapsed = !msg.toolCallsCollapsed;
  console.log('工具调用折叠状态变化:', msg.toolCallsCollapsed)
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
}

.message-item.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-item.assistant {
  margin-right: auto;
}

.message-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e8e8e8;
  font-size: 18px;
  flex-shrink: 0;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-width: 60px;
  word-break: break-word;
  max-width: 100%;
}

.message-item.user .message-bubble {
  border-bottom-right-radius: 6px;
}

.message-item.assistant .message-bubble {
  background: #fff;
  border-bottom-left-radius: 4px;
}

.user-text {
  white-space: pre-wrap;
  font-size: 15px;
  line-height: 1.6;
}

.message-content {
  font-size: 15px;
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
  background-color: #aaa;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.reasoning-header {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.tool-calls-section {
  margin: 12px 0;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  position: relative;
}

.tool-content-wrapper {
  width: 100%;
}

.tool-params-section,
.tool-result-section {
  margin-top: 12px;
}

.tool-section-title {
  font-size: 13px;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.param-value {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.result-value {
  color: #333;
}

.result-table {
  margin-top: 8px;
}

.result-json {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.result-json pre {
  margin: 0;
  font-size: 12px;
  color: #333;
}

.search-result-item {
  margin-bottom: 12px;
  padding: 10px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
}

.search-result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.search-link {
  color: #0057d9;
  text-decoration: none;
  font-weight: 500;
}

.search-link:hover {
  text-decoration: underline;
}

.site-name {
  font-size: 12px;
  color: #888;
}

.search-result-snippet {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}


.tool-calls-header {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  margin-bottom: 12px;
}

.icon {
  position: absolute;
  top: 8px;
  right: 8px;
  cursor: pointer;
}



.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: #d4d4d4;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background-color: #aaa;
}
</style>