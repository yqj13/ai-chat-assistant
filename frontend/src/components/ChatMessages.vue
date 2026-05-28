<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: Array,
  isStreaming: Boolean
})

const messagesContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.isStreaming, (newVal) => {
  if (newVal) {
    scrollToBottom()
  }
})

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="chat-messages" ref="messagesContainer">
    <div 
      v-for="(message, index) in messages" 
      :key="message.id"
      class="message-wrapper"
      :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }"
    >
      <div class="message-avatar">
        <svg v-if="message.role === 'user'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 15s1.5-2 4-2 4 2 4 2"/>
          <path d="M9 9h.01"/>
          <path d="M15 9h.01"/>
        </svg>
      </div>
      
      <div class="message-content">
        <div class="message-header">
          <span class="message-name">
            {{ message.role === 'user' ? '我' : 'AI Assistant' }}
          </span>
          <span class="message-time">{{ formatTime(message.timestamp) }}</span>
        </div>
        
        <div class="message-bubble">
          <p>{{ message.content }}</p>
        </div>
        
        <div v-if="index === messages.length - 1 && isStreaming && message.role === 'assistant'" class="typing-indicator">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>
    </div>
    
    <div v-if="messages.length === 0" class="welcome-message">
      <div class="welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 15s1.5-2 4-2 4 2 4 2"/>
          <path d="M9 9h.01"/>
          <path d="M15 9h.01"/>
        </svg>
      </div>
      <h2>欢迎使用 AI Assistant</h2>
      <p>我可以帮助你解答问题、编写代码、提供建议等</p>
      <div class="quick-tips">
        <span>试试问我：</span>
        <div class="tip-tags">
          <span class="tip-tag">Python 入门教程</span>
          <span class="tip-tag">如何学习机器学习</span>
          <span class="tip-tag">推荐一本好书</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  align-items: flex-end;
}

.user-message .message-bubble {
  background: #1890ff;
  color: #fff;
  border-radius: 16px 16px 4px 16px;
}

.assistant-message .message-bubble {
  background: #fff;
  color: #333;
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #1890ff;
}

.message-avatar svg {
  width: 20px;
  height: 20px;
}

.message-avatar svg {
  color: #666;
}

.user-message .message-avatar svg {
  color: #fff;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.user-message .message-name {
  color: #1890ff;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.message-bubble {
  padding: 12px 16px;
  line-height: 1.6;
}

.message-bubble p {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  background: #fff;
  border-radius: 16px;
  margin-top: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    opacity: 0.4;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #666;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
  color: #1890ff;
}

.welcome-icon svg {
  width: 100%;
  height: 100%;
}

.welcome-message h2 {
  margin-bottom: 8px;
  font-size: 24px;
  color: #333;
}

.welcome-message p {
  margin-bottom: 24px;
  font-size: 14px;
}

.quick-tips {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.tip-tag {
  padding: 6px 16px;
  background: #f0f5ff;
  color: #1890ff;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.tip-tag:hover {
  background: #e6f0ff;
}

@media (max-width: 768px) {
  .chat-messages {
    padding: 16px;
  }
  
  .message-content {
    max-width: 85%;
  }
}
</style>