<script setup>
import { computed } from 'vue';
import { UserIcon, LogoutIcon, DeleteIcon } from 'tdesign-icons-vue-next';
import logoImage from '../assets/logo-1.png';
import { formatTimeShort } from '../utils';

const props = defineProps({
  collapsed: Boolean,
  conversations: Array,
  currentConversation: Object,
  currentUser: Object
});

const emit = defineEmits(['toggle', 'select', 'new', 'delete', 'logout']);

const displayName = computed(() => {
  if (!props.currentUser) return '';
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
  <aside class="sidebar" :class="{ 'sidebar-collapsed': collapsed }">
    <div class="sidebar-header">
      <div v-if="!collapsed" class="logo">
        <img :src="logoImage" alt="Chat with AI" class="logo-icon" />
        <span class="logo-text">Chat with AI</span>
      </div>
      <div v-else class="logo-mini">
        <img :src="logoImage" alt="Chat with AI" class="logo-icon-mini" />
      </div>
    </div>
    
    <div class="new-conversation-wrapper" :class="{ 'new-conversation-wrapper-collapsed': collapsed }">
      <button 
        v-login
        class="new-conversation-btn"
        :class="{ 'new-conversation-btn-collapsed': collapsed }"
        @click="emit('new')"
      >
        <svg v-if="!collapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 5v14"/>
          <path d="M5 12h14"/>
        </svg>
        <span v-if="!collapsed">新建对话</span>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14"/>
          <path d="M5 12h14"/>
        </svg>
      </button>
      <span v-if="collapsed" class="new-conversation-text">新建对话</span>
    </div>
    
    <div v-if="!collapsed" class="conversation-list">
      <div v-if="!conversations || conversations.length === 0" class="empty-conv">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="empty-text">开始新的对话</div>
        <div class="empty-hint">点击上方按钮创建第一个会话</div>
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
          <div class="conv-preview">{{ conv.lastMessage || '暂无消息' }}</div>
        </div>
        <div class="conv-time">{{ formatTimeShort(conv.timestamp) }}</div>
        <button class="conv-delete-btn" title="删除会话" @click="handleDelete(conv, $event)">
          <delete-icon :fill-color='"transparent"' :stroke-color='"currentColor"' :stroke-width="2" />
        </button>
      </div>
    </div>
    
    <div v-else class="conversation-list-mini">
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
    
    <button class="toggle-btn" @click="emit('toggle')">
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
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  box-shadow: 2px 0 16px rgba(0, 0, 0, 0.04);
}

.sidebar-collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.logo-icon,
.logo-icon-mini {
  object-fit: contain;
  transition: all 0.3s ease;
}

.logo-icon {
  width: 40px;
  height: 40px;
}

.logo-icon:hover {
  transform: scale(1.05);
}

.logo-text {
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.3px;
  font-size: 17px;
}

.logo-mini {
  display: flex;
  justify-content: center;
  color: #1890ff;
}

.logo-icon-mini {
  width: 36px;
  height: 36px;
}

.logo-icon-mini:hover {
  transform: scale(1.05);
}

.new-conversation-wrapper {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.new-conversation-wrapper-collapsed {
  align-items: center;
  gap: 6px;
}

.new-conversation-btn {
  margin: 16px;
  padding: 14px;
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.new-conversation-wrapper-collapsed .new-conversation-btn {
  margin: 8px 0 0 0;
}

.new-conversation-btn:hover {
  background: linear-gradient(135deg, #40a9ff 0%, #69c0ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(24, 144, 255, 0.4);
}

.new-conversation-btn:active {
  transform: translateY(0);
}

.new-conversation-btn svg {
  width: 18px;
  height: 18px;
}

.new-conversation-btn-collapsed {
  padding: 0;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1.5px solid #1890ff;
  border-radius: 50%;
  color: #1890ff;
  box-shadow: none;
}

.new-conversation-btn-collapsed:hover {
  background: #1890ff;
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.new-conversation-btn-collapsed svg {
  width: 14px;
  height: 14px;
  stroke-width: 2;
}

.new-conversation-text {
  font-size: 11px;
  color: #64748b;
  text-align: center;
  white-space: nowrap;
  line-height: 1.2;
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
  padding: 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 6px;
  position: relative;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: #e2e8f0;
}

.conversation-item:hover .conv-delete-btn {
  opacity: 1;
  transform: translateY(-50%) scale(1);
}

.conversation-item.active {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border-color: #91d5ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.conv-delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%) scale(0.8);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.conv-delete-btn:hover {
  background: #fff2f0;
  color: #f5222d;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.15);
}

.conv-delete-btn svg {
  width: 18px;
  height: 18px;
}

.empty-conv {
  padding: 48px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f0f5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  margin-bottom: 8px;
}

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.empty-hint {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.conv-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f0ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.conversation-item:hover .conv-icon {
  transform: scale(1.05);
  background: linear-gradient(135deg, #e6f0ff 0%, #d9ebff 100%);
}

.conversation-item.active .conv-icon {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: white;
  box-shadow: 0 3px 10px rgba(24, 144, 255, 0.3);
}

.conv-icon svg {
  width: 22px;
  height: 22px;
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
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.conversation-item-mini {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f0ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.conversation-item-mini:hover {
  background: linear-gradient(135deg, #e6f0ff 0%, #d9ebff 100%);
  transform: scale(1.1);
  border-color: #91d5ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);
}

.conversation-item-mini.active {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: #fff;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4);
  transform: scale(1.1);
}

.conversation-item-mini svg {
  width: 22px;
  height: 22px;
}

.user-section {
  padding: 16px;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.25s ease;
  border: 1px solid transparent;
}

.user-info:hover {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-color: #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 3px 10px rgba(24, 144, 255, 0.3);
  transition: all 0.25s ease;
}

.user-info:hover .user-avatar {
  transform: scale(1.05);
  box-shadow: 0 4px 14px rgba(24, 144, 255, 0.4);
}

.user-avatar svg {
  width: 22px;
  height: 22px;
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
  right: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.toggle-btn:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: #1890ff;
  border-color: #1890ff;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.toggle-btn svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 768px) {
  .sidebar {
    z-index: 100;
  }
}
</style>
