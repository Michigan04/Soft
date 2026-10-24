<template>
  <div class="app-shell">
    <Sidebar :open="sidebarOpen" @close="sidebarOpen = false" />
    <div class="main-col">
      <Header @toggle-sidebar="sidebarOpen = !sidebarOpen" />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Sidebar from "@/components/layout/Sidebar.vue";
import Header from "@/components/layout/Header.vue";

const sidebarOpen = ref(false);
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
}
.main-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
}
</style>
