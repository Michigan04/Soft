<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Notifications</div>
        <div class="page-subtitle">{{ unreadCount }} unread of {{ store.items.length }} total.</div>
      </div>
      <div class="flex gap-8">
        <button class="btn btn-secondary btn-sm" :class="{ active: filter === 'all' }" @click="filter = 'all'">All</button>
        <button class="btn btn-secondary btn-sm" :class="{ active: filter === 'unread' }" @click="filter = 'unread'">Unread</button>
      </div>
    </div>

    <LoadingState v-if="loading" :rows="6" />
    <EmptyState v-else-if="filtered.length === 0" title="No notifications" message="You're all caught up." />
    <div v-else class="card">
      <div v-for="n in filtered" :key="n.id" class="notif-row" :class="{ unread: !n.is_read }">
        <SeverityBadge :severity="n.severity" />
        <div style="flex: 1">
          <div style="font-weight: 600; font-size: 13.5px">{{ n.title }}</div>
          <div class="text-sm" style="margin: 2px 0">{{ n.message }}</div>
          <div class="text-muted text-sm">
            {{ new Date(n.created_at).toLocaleString() }} &middot;
            <span style="text-transform: capitalize">{{ n.notification_type.replace("_", " ") }}</span>
          </div>
        </div>
        <button v-if="!n.is_read" class="btn btn-secondary btn-sm" @click="store.markRead(n.id)">Mark read</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useNotificationsStore } from "@/stores/notifications";
import SeverityBadge from "@/components/SeverityBadge.vue";
import LoadingState from "@/components/LoadingState.vue";
import EmptyState from "@/components/EmptyState.vue";

const store = useNotificationsStore();
const loading = ref(true);
const filter = ref("all");

const unreadCount = computed(() => store.unreadCount);
const filtered = computed(() =>
  filter.value === "unread" ? store.items.filter((n) => !n.is_read) : store.items,
);

onMounted(async () => {
  await store.fetch();
  loading.value = false;
});
</script>

<style scoped>
.notif-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}
.notif-row:last-child {
  border-bottom: none;
}
.notif-row.unread {
  background: #faf5f6;
}
</style>
