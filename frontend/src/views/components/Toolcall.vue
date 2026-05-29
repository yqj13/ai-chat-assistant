<template>
  <div class="tool-call-container">
    <div class="tool-call-header">
      <span class="tool-icon">⚙️</span>
      <span class="tool-name">{{ toolCall.name }}</span>
      <span :class="['tool-status', status]">{{ statusText }}</span>
    </div>
    <div class="tool-call-content">
      <div class="tool-call-params">
        <pre>{{ JSON.stringify(toolCall, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  },
  status: {
    type: String,
    default: 'pending'
  }
});

const statusText = computed(() => {
  const statusMap = {
    pending: '执行中',
    success: '成功',
    error: '失败'
  };
  return statusMap[props.status] || props.status;
});
</script>

<style scoped>
.tool-call-container {
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  border: 1px solid #d1d9e0;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.tool-icon {
  font-size: 14px;
}

.tool-name {
  font-weight: 600;
  color: #24292f;
  font-size: 14px;
}

.tool-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.tool-status.pending {
  background: #fff3cd;
  color: #856404;
}

.tool-status.success {
  background: #d4edda;
  color: #155724;
}

.tool-status.error {
  background: #f8d7da;
  color: #721c24;
}

.tool-call-content {
  margin-top: 8px;
}

.tool-call-params pre {
  margin: 0;
  padding: 8px;
  background: #1e1e2e;
  border-radius: 4px;
  color: #cdd6f4;
  font-size: 12px;
  overflow-x: auto;
}
</style>
