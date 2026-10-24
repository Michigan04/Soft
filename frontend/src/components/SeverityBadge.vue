<template>
  <span class="badge" :style="style">{{ severity }}</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ severity: { type: String, required: true } });

const colors = { info: "#1c7ed6", warning: "#e8a400", critical: "#c92a2a" };
const color = computed(() => colors[props.severity] || "#9499ab");
const style = computed(() => ({ color: color.value, background: `${color.value}18` }));
</script>
