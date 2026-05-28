<template>
  <div class="chat-message" :class="{ 'is-user': message.role === 'user' }">
    <div class="avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else>🤖</span>
    </div>
    <div class="message-content">
      <div v-if="message.toolName" class="tool-info">
        <div class="tool-status" :class="{ 'is-loading': !message.toolResult }">
          <span class="tool-icon" v-if="!message.toolResult">⚙️</span>
          <span class="tool-icon" v-else>✅</span>
          <span class="tool-name">{{ getToolDisplayName(message.toolName) }}</span>
          <span v-if="!message.toolResult" class="tool-loading">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </span>
        </div>
        <div v-if="message.toolParams && !message.toolResult" class="tool-params">
          <code>{{ formatParams(message.toolParams) }}</code>
        </div>
        <div v-if="message.toolResult && message.toolResult !== '工具执行完成'" class="tool-result">
          <div class="result-label">查询结果：</div>
          <div class="result-content" v-html="renderMarkdown(message.toolResult)"></div>
        </div>
      </div>
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
  time: '时间查询',
  time_query: '时间查询',
  search_web: '联网搜索'
}

const getToolName = (toolUsed) => {
  return toolNames[toolUsed] || toolUsed
}

const getToolDisplayName = (toolName) => {
  return toolNames[toolName] || toolName
}

const formatParams = (params) => {
  if (typeof params === 'string') {
    try {
      params = JSON.parse(params)
    } catch {
      return params
    }
  }
  return JSON.stringify(params, null, 2)
}

const renderMarkdown = (content) => {
  let text = content || ''
  
  text = text.replace(/\\n/g, '\n')
  
  text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  
  text = text.replace(/^- (.*$)/gim, '<li>$1</li>')
  text = text.replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
  
  text = text.replace(/\n/g, '<br>')
  
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  
  return text
}

const renderedContent = computed(() => {
  return renderMarkdown(props.message.content)
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

.tool-info {
  margin-bottom: 12px;
  padding: 12px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  border-left: 3px solid #667eea;
}

.is-user .tool-info {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: rgba(255, 255, 255, 0.5);
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 8px;
}

.is-user .tool-status {
  color: white;
}

.tool-icon {
  font-size: 16px;
}

.tool-loading {
  display: flex;
  gap: 2px;
  margin-left: 4px;
}

.tool-params {
  font-size: 12px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow-x: auto;
}

.is-user .tool-params {
  background: rgba(0, 0, 0, 0.1);
}

.tool-params code {
  font-family: 'Monaco', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.tool-result {
  margin-top: 8px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.is-user .tool-result {
  background: rgba(0, 0, 0, 0.1);
}

.result-label {
  font-size: 12px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 4px;
}

.is-user .result-label {
  color: rgba(255, 255, 255, 0.9);
}

.result-content {
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}

.is-user .result-content {
  color: rgba(255, 255, 255, 0.9);
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
