<template>
  <div class="chat-messages" ref="messagesContainer">
    <div
      v-for="msg in messages"
      :key="msg.id"
      :class="['message-item', msg.role]"
    >
      <div class="message-avatar">
        <span v-if="msg.role === 'user'">👤</span>
        <span v-else>🤖</span>
      </div>

      <div class="message-bubble">
        <!-- 思考过程 -->
        <div v-if="msg.reasoningContent" class="reasoning-block">
          <details open>
            <summary>💭 思考过程</summary>
            <div class="reasoning-content">
              <StreamMarkdown
                :content="msg.reasoningContent"
                :typing="!msg.finished && isStreaming"
                :speed="15"
                :cursor="false"
              />
            </div>
          </details>
        </div>

        <!-- Loading 状态 -->
        <div v-if="msg.loading && !msg.content && !msg.reasoningContent" class="loading-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>

        <!-- 助手消息 -->
        <div v-if="msg.content && msg.role === 'assistant'" class="message-content">
          <StreamMarkdown
            :content="msg.content"
            :typing="!msg.finished && isStreaming && msg.id === currentStreamingId"
            :speed="25"
            :cursor="!msg.finished && isStreaming && msg.id === currentStreamingId"
            :cursor-remove-on-complete="true"
            :enable-latex="true"
            :enable-mermaid="true"
            @complete="handleComplete(msg)"
            @step="handleStep"
          />
        </div>

        <!-- 用户消息 -->
        <div v-if="msg.content && msg.role === 'user'" class="message-content user-text">
          {{ msg.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import StreamMarkdown from './StreamMarkdown.vue'

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

const messagesContainer = ref(null)

const handleComplete = (msg) => {
  console.log('消息渲染完成:', msg.id)
}

const handleStep = () => {
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(
  () => props.messages,
  () => scrollToBottom(),
  { deep: true }
)

watch(
  () => props.messages.length,
  () => scrollToBottom()
)

onMounted(() => scrollToBottom())
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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

.message-item.user .message-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
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
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-bottom-right-radius: 4px;
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

/* Loading */
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

.loading-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.loading-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 思考过程 */
.reasoning-block {
  margin-bottom: 12px;
  padding: 12px 14px;
  background: #f0f7ff;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #d6e8fa;
}

.reasoning-block summary {
  cursor: pointer;
  color: #555;
  font-weight: 500;
}

.reasoning-content {
  margin-top: 8px;
  color: #666;
}
</style>