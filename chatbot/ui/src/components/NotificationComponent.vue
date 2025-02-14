<template>
  <div class="fixed top-4 right-4 space-y-2 z-50">
    <div
      v-for="notification in notifications"
      :key="notification.id"
      :class="[
        'flex items-center px-4 py-2 rounded shadow-lg',
        notification.type === 'error' && 'bg-red-100 text-red-800 border-red-500',
        notification.type === 'success' && 'bg-green-100 text-green-800 border-green-500',
        notification.type === 'info' && 'bg-blue-100 text-blue-800 border-blue-500',
        notification.type === 'warning' && 'bg-yellow-100 text-yellow-800 border-yellow-500',
      ]"
    >
      <span class="flex-1">{{ notification.message }}</span>
      <button
        class="ml-4 text-gray-500 hover:text-gray-800"
        @click="handleDismiss(notification.id)"
      >
        &times;
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>

import type { Notification } from '@/types/notification';

const props = defineProps({
  notifications: {
    type: Array as () => Notification[],
    default: () => [],
  },
});

const emit = defineEmits(['dismiss']);

const handleDismiss = (id: number) => {
  emit('dismiss', id);
};
</script>
