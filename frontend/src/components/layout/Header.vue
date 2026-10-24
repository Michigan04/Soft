<template>
  <header class="topbar">
    <button class="hamburger" aria-label="Toggle navigation" @click="$emit('toggle-sidebar')">
      <span></span><span></span><span></span>
    </button>

    <div class="spacer"></div>

    <router-link :to="{ name: 'notifications' }" class="icon-btn" title="Notifications">
      <span>Notifications</span>
      <span v-if="unread > 0" class="unread-dot">{{ unread > 9 ? "9+" : unread }}</span>
    </router-link>

    <div class="user-menu">
      <div class="avatar">{{ initials }}</div>
      <div class="user-info">
        <div class="user-name">{{ auth.user?.full_name }}</div>
        <div class="user-role text-muted">{{ auth.role }}</div>
      </div>
      <button class="btn btn-secondary btn-sm" @click="signOut">Sign out</button>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";

defineEmits(["toggle-sidebar"]);

const auth = useAuthStore();
const notifications = useNotificationsStore();
const router = useRouter();

const unread = computed(() => notifications.unreadCount);
const initials = computed(() =>
  (auth.user?.full_name || "?")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase(),
);

onMounted(() => {
  notifications.fetch().catch(() => {});
});

function signOut() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.topbar {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 18px;
  position: sticky;
  top: 0;
  z-index: 20;
}
.spacer {
  flex: 1;
}
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
}
.hamburger span {
  width: 20px;
  height: 2px;
  background: var(--color-text);
  display: block;
}
.icon-btn {
  position: relative;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
}
.icon-btn:hover {
  color: var(--color-primary);
  text-decoration: none;
}
.unread-dot {
  background: var(--risk-critical);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 999px;
  min-width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 6px;
  padding: 0 4px;
}
.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name {
  font-size: 13px;
  font-weight: 600;
}
.user-role {
  font-size: 11px;
  text-transform: capitalize;
}

@media (max-width: 900px) {
  .hamburger {
    display: flex;
  }
  .user-info {
    display: none;
  }
}
</style>
