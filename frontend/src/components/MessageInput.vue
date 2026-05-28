<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  disabled: Boolean
})

const emit = defineEmits(['send'])

const inputText = ref('')
const textareaRef = ref(null)

const handleSend = () => {
  if (!inputText.value.trim() || props.disabled) return
  
  emit('send', inputText.value)
  inputText.value = ''
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

watch(() => props.disabled, (newVal) => {
  if (!newVal && textareaRef.value) {
    textareaRef.value.focus()
  }
})
</script>

<template>
  <div class="message-input-container">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="message-input"
        :disabled="disabled"
        placeholder="输入消息，按 Enter 发送，Shift+Enter 换行"
        rows="1"
        @keydown="handleKeydown"
      ></textarea>
      
      <button 
        class="send-btn"
        :disabled="!inputText.trim() || disabled"
        @click="handleSend"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </button>
    </div>
    
    <div class="input-footer">
      <span class="tip">支持 Markdown 格式</span>
    </div>
  </div>
</template>

<style scoped>
.message-input-container {
  background: #fff;
  border-top: 1px solid #e8e8e8;
  padding: 16px 24px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  min-height: 44px;
  max-height: 200px;
  overflow-y: auto;
}

.message-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.message-input::placeholder {
  color: #999;
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #1890ff;
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.send-btn svg {
  width: 18px;
  height: 18px;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.tip {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .message-input-container {
    padding: 12px 16px;
    padding-bottom: calc(12px + env(safe-area-inset-bottom));
  }
  
  .input-wrapper {
    gap: 8px;
  }
}
</style>