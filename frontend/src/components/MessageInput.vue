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
  background: transparent;
  border-top: none;
  padding: 20px 24px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 14px 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 52px;
  max-height: 220px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.message-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.95);
}

.message-input::placeholder {
  color: #94a3b8;
}

.message-input:disabled {
  background: rgba(241, 245, 249, 0.8);
  cursor: not-allowed;
  border-color: #e2e8f0;
}

.send-btn {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #40a9ff 0%, #69c0ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(24, 144, 255, 0.4);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
}

.send-btn svg {
  width: 20px;
  height: 20px;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.tip {
  font-size: 12px;
  color: #94a3b8;
}

.block {
  display: flex;
  align-items: center;
  gap: 10px;
}


@media (max-width: 768px) {
  .message-input-container {
    padding: 16px;
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
  }

  .input-wrapper {
    gap: 10px;
  }

  .message-input {
    padding: 12px 16px;
    min-height: 48px;
    border-radius: 14px;
  }

  .send-btn {
    width: 48px;
    height: 48px;
    border-radius: 14px;
  }

  .send-btn svg {
    width: 18px;
    height: 18px;
  }

  .block {
    gap: 8px;
    flex-wrap: wrap;
  }
}
</style>