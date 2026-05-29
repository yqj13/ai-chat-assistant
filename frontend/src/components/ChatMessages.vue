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
            title: !msg.collapsed ? '思考中' : '思考完成',
            text: msg.reasoningContent
          }"
          :collapsed="msg.collapsed || false"
          :status="msg.collapsed? 'complete': 'pending'"
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
              :content="getToolContent(tool)"
              :status="index < msg.toolCalls.length - 1 ? 'default' : 'process'"
            />
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
import { Steps as TSteps, StepItem as TStepItem } from 'tdesign-vue-next'
import { Robot2Icon, UserIcon } from 'tdesign-icons-vue-next'

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
  console.log('tool:', tool)
  const toolNameMap = {
    'weather_query': '天气查询',
    'time_query': '时间查询',
    'web_search': '联网查询',
    'calculator': '计算器',
  }
  
  return `工具调用: ${toolNameMap[tool?.data?.tool] || tool.type}`
}

const getToolContent = (tool) => {
  if (!tool || !tool.data) return ''
  try {
    const { params, result } = tool.data
    if (params) {
      return '参数: ' + JSON.stringify(params, null, 2)
    }
    if (result) {
      return '结果: ' + JSON?.stringify(result, null, 2)?.replaceAll('##', '')?.replaceAll('\\n', ' ')?.replace('content=', '') || ' '
    }
    return JSON.stringify(tool.data, null, 2)
  } catch (e) {
    return String(tool.data)
  }
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
  padding-bottom: 40px;
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