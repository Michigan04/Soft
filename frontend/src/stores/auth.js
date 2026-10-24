import { defineStore } from "pinia";
import * as authApi from "@/api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("access_token") || null,
    user: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    role: (state) => state.user?.role || null,
    isAdmin: (state) => state.user?.role === "admin",
    isStaff: (state) => state.user?.role === "faculty" || state.user?.role === "ta",
    isStudent: (state) => state.user?.role === "student",
  },
  actions: {
    async login(email, password) {
      const response = await authApi.login(email, password);
      this.token = response.data.access_token;
      localStorage.setItem("access_token", this.token);
      await this.loadMe();
    },
    async loadMe() {
      if (!this.token) return;
      this.loading = true;
      try {
        const response = await authApi.fetchMe();
        this.user = response.data;
      } finally {
        this.loading = false;
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("access_token");
    },
  },
});
