<script setup>
import { ref, watch } from 'vue'
import { Button as TButton } from 'tdesign-vue-next';
import { InternetIcon, SystemSumIcon } from 'tdesign-icons-vue-next'

const props = defineProps({
  disabled: Boolean
})

const activeR1 = ref(false)
const activeSearch = ref(false)

const emit = defineEmits(['send'])

const inputText = ref('')
const textareaRef = ref(null)

const handleSend = () => {
  if (!inputText.value.trim() || props.disabled) return

  emit('send', {
    content: inputText.value,
    deepThinking: activeR1.value,
    webSearch: activeSearch.value
  })
  inputText.value = ''
  activeR1.value = false
  activeSearch.value = false
}

const onStop = () => {
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
      <t-chat-sender v-login v-model="inputText" :loading="loading" :textarea-props="{
        placeholder: '请输入消息...',
      }" @send="handleSend" @stop="onStop" @keydown="handleKeydown">
        <template #footer-prefix>
          <div class="block">

            <t-button variant="outline" shape="round" :theme="activeR1 ? 'primary' : 'default'"
              @click="activeR1 = !activeR1">
              <template #icon>
                <SystemSumIcon />
              </template>
              深度思考
            </t-button>
            <t-button variant="outline" :theme="activeSearch ? 'primary' : 'default'" shape="round"
              @click="activeSearch = !activeSearch">
              <template #icon>
                <internet-icon />
              </template>
              联网查询
            </t-button>
          </div>
        </template>
      </t-chat-sender>
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

.block {
  display: flex;
  align-items: center;
  gap: 8px;
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