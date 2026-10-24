<template>
  <span class="badge" :style="style">
    <span class="badge-dot" :style="{ background: color }"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  level: { type: String, default: null }, // low | moderate | high | critical | null
});

const colors = {
  low: "#2f9e44",
  moderate: "#e8a400",
  high: "#e8590c",
  critical: "#c92a2a",
};

const color = computed(() => colors[props.level] || "#9499ab");
const label = computed(() => (props.level ? props.level.toUpperCase() : "UNASSESSED"));
const style = computed(() => ({
  color: color.value,
  background: `${color.value}18`,
}));
</script>
