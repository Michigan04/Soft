<template>
  <div class="loading-wrap">
    <div class="skeleton" v-for="n in rows" :key="n" :style="{ height: '18px', marginBottom: '10px' }"></div>
  </div>
</template>

<script setup>
defineProps({ rows: { type: Number, default: 4 } });
</script>

<style scoped>
.loading-wrap {
  padding: 4px 0;
}
</style>
