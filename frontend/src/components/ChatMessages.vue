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
                    :columns="getParamsColumns()" :bordered="true" :stripe="true" size="small"
                    row-key="index" :max-height="250" sticky-header>
                    <template #paramValue="{ row }">
                      <code class="param-value">{{ row.paramValue }}</code>
                    </template>
                  </t-table>
                </div>

                <div v-if="part.result" class="tool-result-section">
                  <div class="tool-section-title">执行结果</div>
                  <div v-if="part.result.tool === 'weather_query'" class="result-table">
                    <t-table :data="getWeatherTableData({ data: part.result })" :columns="getTableColumns()"
                      :bordered="true" :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #value="{ row }">
                        <span class="result-value">{{ row.value }}</span>
                      </template>
                    </t-table>
                  </div>
                  <div v-else-if="part.result.tool === 'time_query'" class="result-table">
                    <t-table :data="getTimeTableData({ data: part.result })" :columns="getTableColumns()" :bordered="true"
                      :stripe="true" size="small" row-key="index" :max-height="250" sticky-header>
                      <template #value="{ row }">
                        <span class="result-value">{{ row.value }}</span>
                      </template>
                    </t-table>
                  </div>
                  <div v-else-if="part.result.tool === 'calculator'" class="result-table">
                    <t-table :data="getCalculatorTableData({ data: part.result })" :columns="getTableColumns()"
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
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Table as TTable } from 'tdesign-vue-next'
import { ChevronDownSIcon, ChevronUpIcon, AiToolIcon } from 'tdesign-icons-vue-next'
import 'katex/dist/katex.min.css'
import 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js'
import userAvatar from '../assets/user-avatar.png'
import aiAvatar from '../assets/ai-avatar.png'
import { formatTime, getToolCallTitle, getParamsTableData, getParamsColumns, getWeatherTableData, getTimeTableData, getCalculatorTableData, getSearchTableData, getTableColumns } from '../utils'

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
const enableKatex = ref(true)

const options = computed(() => ({
  engine: {
    syntax: enableKatex.value ? {
      mathBlock: { engine: 'katex' },
      inlineMath: { engine: 'katex' },
    } : undefined,
  },
}))

const toggleToolCallCard = (part) => {
  if (part.type === 'tool_call') {
    part.collapsed = !part.collapsed
  }
}

const collapsedChangeHandle = (msg) => {
  msg.collapsed = !msg.collapsed
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

watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  }
)

watch(
  () => props.messages.map(msg => ({
    reasoningContent: msg.reasoningContent,
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

.tool-call-item {
  margin: 14px 0;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-call-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.tool-call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.tool-call-icon {
  width: 20px;
  height: 20px;
}

.tool-call-content {
  margin-top: 14px;
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
}

.search-date {
  font-size: 12px;
  color: #94a3b8;
}
</style>
