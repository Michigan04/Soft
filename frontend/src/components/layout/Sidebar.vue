<template>
  <div>
    <div v-if="open" class="sidebar-scrim" @click="$emit('close')"></div>
    <aside class="sidebar" :class="{ open }">
      <div class="brand">
        <div class="crest">IM</div>
        <div class="brand-text">
          <div class="brand-title">IIT Madras</div>
          <div class="brand-sub">Risk &amp; Intervention Platform</div>
        </div>
      </div>

      <nav class="nav">
        <router-link
          v-for="item in visibleItems"
          :key="item.label"
          :to="item.route"
          class="nav-item"
          active-class="active"
          @click="$emit('close')"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <div class="sidebar-footer text-sm">Dev / Demo Build</div>
    </aside>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";

defineProps({ open: { type: Boolean, default: false } });
defineEmits(["close"]);

const auth = useAuthStore();

const allItems = computed(() => [
  { to: "dashboard", label: "Dashboard", roles: ["admin", "faculty", "ta", "student"] },
  { to: "students", label: "Students", roles: ["admin", "faculty", "ta"] },
  {
    to: "student-profile",
    label: "My Profile",
    roles: ["student"],
    params: { id: auth.user?.student_id },
  },
  { to: "registration-checker", label: "Registration Checker", roles: ["admin", "faculty", "ta", "student"] },
  { to: "projects", label: "Projects & CGPA", roles: ["admin", "faculty", "ta", "student"] },
  { to: "interventions", label: "Interventions", roles: ["admin", "faculty", "ta"] },
  { to: "assignments", label: "Staff Assignments", roles: ["admin"] },
  { to: "notifications", label: "Notifications", roles: ["admin", "faculty", "ta", "student"] },
  { to: "reports", label: "Reports", roles: ["admin", "faculty", "ta"] },
  { to: "rules", label: "Rules & Policies", roles: ["admin"] },
  { to: "imports", label: "Data Import", roles: ["admin"] },
  { to: "audit-logs", label: "Audit Logs", roles: ["admin"] },
]);

const visibleItems = computed(() =>
  allItems.value
    .filter((item) => item.roles.includes(auth.role))
    .filter((item) => item.to !== "student-profile" || auth.user?.student_id)
    .map((item) => ({ ...item, route: { name: item.to, params: item.params || {} } })),
);
</script>

<style scoped>
.sidebar {
  width: 230px;
  flex-shrink: 0;
  background: var(--color-sidebar-bg);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.crest {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.brand-title {
  color: #fff;
  font-weight: 700;
  font-size: 13.5px;
}
.brand-sub {
  color: var(--color-sidebar-text);
  font-size: 11px;
  margin-top: 2px;
}
.nav {
  flex: 1;
  padding: 12px 10px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  color: var(--color-sidebar-text);
  text-decoration: none;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  border-left: 3px solid transparent;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  text-decoration: none;
}
.nav-item.active {
  background: rgba(140, 29, 43, 0.35);
  color: var(--color-sidebar-text-active);
  border-left-color: var(--color-primary-light);
  font-weight: 700;
}
.sidebar-footer {
  padding: 14px 16px;
  color: #595e74;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-scrim {
  display: none;
}

@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    z-index: 110;
    left: 0;
    top: 0;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: var(--shadow-md);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .sidebar-scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(16, 18, 30, 0.45);
    z-index: 105;
  }
}
</style>
