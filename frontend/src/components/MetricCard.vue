<template>
  <div class="card card-pad metric-card">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value" :style="{ color: accent }">{{ value }}</div>
    <div v-if="hint" class="metric-hint text-muted text-sm">{{ hint }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: "" },
  accent: { type: String, default: "#1f2333" },
});
</script>

<style scoped>
.metric-card {
  min-width: 0;
}
.metric-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 10px;
}
.metric-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}
.metric-hint {
  margin-top: 8px;
}
</style>
