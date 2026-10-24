import { defineStore } from "pinia";
import * as notificationsApi from "@/api/notifications";

export const useNotificationsStore = defineStore("notifications", {
  state: () => ({
    items: [],
    loaded: false,
  }),
  getters: {
    unreadCount: (state) => state.items.filter((n) => !n.is_read).length,
  },
  actions: {
    async fetch() {
      const response = await notificationsApi.listNotifications();
      this.items = response.data;
      this.loaded = true;
    },
    async markRead(id) {
      await notificationsApi.markNotificationRead(id);
      const item = this.items.find((n) => n.id === id);
      if (item) item.is_read = true;
    },
  },
});
