import { defineStore } from 'pinia';
import type { Notification } from '@/types/notification';

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [] as Notification[],
  }),
  actions: {
    addNotification(notification: Omit<Notification, 'id'>) {
      const id = Date.now();
      this.notifications.push({ ...notification, id });
      setTimeout(() => this.dismissNotification(id), 5000); // Auto-dismiss after 5 seconds
    },
    dismissNotification(id: number) {
      this.notifications = this.notifications.filter((n) => n.id !== id);
    },
  },
});
