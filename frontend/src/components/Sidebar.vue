<script setup>import { computed } from 'vue';
import { Robot2Icon, UserIcon, LogoutIcon, DeleteIcon } from 'tdesign-icons-vue-next';
const props = defineProps({
 collapsed: Boolean,
 conversations: Array,
 currentConversation: Object,
 currentUser: Object
});
const emit = defineEmits(['toggle', 'select', 'new', 'delete', 'logout']);
const formatTime = (timestamp) => {
 const date = new Date(timestamp);
 const now = new Date();
 const diff = now.getTime() - date.getTime();
 if (diff < 60000) {
 return '刚刚';
 }
 else if (diff < 3600000) {
 return Math.floor(diff / 60000) + '分钟前';
 }
 else if (diff < 86400000) {
 return Math.floor(diff / 3600000) + '小时前';
 }
 else if (diff < 604800000) {
 return Math.floor(diff / 86400000) + '天前';
 }
 else {
 return date.getMonth() + 1 + '/' + date.getDate();
 }
};
const displayName = computed(() => {
 if (!props.currentUser)
 return '';
 return props.currentUser.username || props.currentUser.uid || '用户';
});
const handleDelete = (conv, event) => {
 event.stopPropagation();
 if (window.confirm(`确认删除会话 "${conv.title}"？该操作不可恢复。`)) {
 emit('delete', conv);
 }
};
</script>

<template>
  <aside 
    class="sidebar"
    :class="{ 'sidebar-collapsed': collapsed }"
  >
    <div class="sidebar-header">
      <div class="logo" v-if="!collapsed">
       <robot-2-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2"/>
        <span>AI 聊天助手</span>
      </div>
      <div class="logo-mini" v-else>
        <robot-2-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2"/>
      </div>
    </div>
    
    <button 
      class="new-conversation-btn"
      @click="emit('new')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M12 5v14"/>
        <path d="M5 12h14"/>
      </svg>
      <span v-if="!collapsed">新建对话</span>
    </button>
    
    <div class="conversation-list" v-if="!collapsed">
      <div v-if="!conversations || conversations.length === 0" class="empty-conv">
        暂无会话，点击上方"新建对话"开始
      </div>
      <div 
        v-for="conv in conversations" 
        :key="conv.id"
        class="conversation-item"
        :class="{ 'active': currentConversation?.id === conv.id }"
        @click="emit('select', conv)"
      >
        <div class="conv-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="conv-info">
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-preview">
            {{ conv.lastMessage || '暂无消息' }}
          </div>
        </div>
        <div class="conv-time">
          {{ formatTime(conv.timestamp) }}
        </div>
        <button class="conv-delete-btn" title="删除会话" @click="handleDelete(conv, $event)">
          <delete-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2" />
        </button>
      </div>
    </div>
    
    <div class="conversation-list-mini" v-else>
      <div 
        v-for="conv in conversations" 
        :key="conv.id"
        class="conversation-item-mini"
        :class="{ 'active': currentConversation?.id === conv.id }"
        :title="conv.title"
        @click="emit('select', conv)"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
    </div>

    <div v-if="currentUser" class="user-section">
      <div v-if="!collapsed" class="user-info" @click="emit('logout')">
        <div class="user-avatar">
          <user-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2" />
        </div>
        <div class="user-details">
          <div class="user-name">{{ displayName }}</div>
          <div class="logout-text">点击退出登录</div>
        </div>
      </div>
      <button v-else class="logout-btn-mini" @click="emit('logout')" title="退出登录">
        <logout-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2" />
      </button>
    </div>
    
    <button 
      class="toggle-btn"
      @click="emit('toggle')"
    >
      <svg v-if="!collapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M9 18l6-6-6-6"/>
      </svg>
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 260px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  z-index: 100;
}

.sidebar-collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.logo svg,
.logo-mini svg {
  width: 32px;
  height: 32px;
}

.logo-mini {
  display: flex;
  justify-content: center;
  color: #1890ff;
}

.new-conversation-btn {
  margin: 16px;
  padding: 12px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.new-conversation-btn:hover {
  background: #40a9ff;
}

.new-conversation-btn svg {
  width: 18px;
  height: 18px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
  position: relative;
}

.conversation-item:hover {
  background: #f5f5f5;
}

.conversation-item:hover .conv-delete-btn {
  opacity: 1;
}

.conversation-item.active {
  background: #e6f7ff;
}

.conv-delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}

.conv-delete-btn:hover {
  background: #fff2f0;
  color: #f5222d;
}

.conv-delete-btn svg {
  width: 16px;
  height: 16px;
}

.empty-conv {
  padding: 16px;
  font-size: 12px;
  color: #bbb;
  text-align: center;
}

.conv-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  flex-shrink: 0;
}

.conv-icon svg {
  width: 20px;
  height: 20px;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-preview {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 12px;
  color: #ccc;
  flex-shrink: 0;
}

.conversation-list-mini {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.conversation-item-mini {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item-mini:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.conversation-item-mini.active {
  background: #1890ff;
  color: #fff;
}

.conversation-item-mini svg {
  width: 20px;
  height: 20px;
}

.user-section {
  padding: 12px 16px;
  border-top: 1px solid #e8e8e8;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f5f5;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
}

.user-avatar svg {
  width: 18px;
  height: 18px;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-text {
  font-size: 12px;
  color: #999;
}

.logout-btn-mini {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f5f5;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 auto;
}

.logout-btn-mini:hover {
  background: #fff2f0;
  color: #f5222d;
}

.logout-btn-mini svg {
  width: 18px;
  height: 18px;
}

.toggle-btn {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  border: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
  transition: all 0.2s;
  z-index: 10;
}

.toggle-btn:hover {
  background: #f5f5f5;
  color: #666;
}

.toggle-btn svg {
  width: 14px;
  height: 14px;
}

@media (max-width: 768px) {
  .sidebar {
    z-index: 100;
  }
  
  .sidebar-collapsed {
    width: 64px;
  }
}
</style>