<template>
  <div class="chat-message" :class="{ 'is-user': message.role === 'user' }">
    <div class="avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else>🤖</span>
    </div>
    <div class="message-content">
      <div v-if="message.thinking && !message.finished" class="thinking">
        <span class="thinking-icon">🧠</span>
        <span>{{ message.thinking }}</span>
        <span class="dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
      </div>
      <div class="markdown-content" v-html="renderedContent"></div>
      <div v-if="message.toolUsed" class="tool-tag">
        🛠️ 使用工具: {{ getToolName(message.toolUsed) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const toolNames = {
  get_weather: '天气查询',
  web_search: '联网搜索',
  calculator: '计算器',
  get_current_time: '时间查询',
  weather: '天气查询',
  search: '联网搜索',
  time: '时间查询'
}

const getToolName = (toolUsed) => {
  return toolNames[toolUsed] || toolUsed
}

const renderedContent = computed(() => {
  let content = props.message.content || ''
  
  content = content.replace(/\\n/g, '\n')
  
  content = content.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  content = content.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  content = content.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  content = content.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  content = content.replace(/`([^`]+)`/g, '<code>$1</code>')
  
  content = content.replace(/^- (.*$)/gim, '<li>$1</li>')
  content = content.replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
  
  content = content.replace(/\n/g, '<br>')
  
  content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  
  return content
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.is-user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.is-user .avatar {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  background: #f1f3f4;
  position: relative;
}

.is-user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.markdown-content {
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin: 8px 0;
  font-weight: 600;
}

.markdown-content h1 {
  font-size: 18px;
}

.markdown-content h2 {
  font-size: 16px;
}

.markdown-content h3 {
  font-size: 14px;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.is-user .markdown-content code {
  background: rgba(255, 255, 255, 0.2);
}

.markdown-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin: 4px 0;
}

.markdown-content a {
  color: #667eea;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.is-user .markdown-content a {
  color: #fff;
  text-decoration: underline;
}

.thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 13px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #ddd;
}

.is-user .thinking {
  color: rgba(255, 255, 255, 0.8);
  border-bottom-color: rgba(255, 255, 255, 0.3);
}

.thinking-icon {
  font-size: 16px;
}

.dots {
  display: flex;
  gap: 2px;
}

.dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #999;
  animation: blink 1s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

.is-user .dot {
  background: rgba(255, 255, 255, 0.6);
}

.tool-tag {
  font-size: 12px;
  color: #888;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #ddd;
}

.is-user .tool-tag {
  color: rgba(255, 255, 255, 0.7);
  border-top-color: rgba(255, 255, 255, 0.3);
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

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0.3;
  }
}
</style>