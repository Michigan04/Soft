<template>
  <Bar :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import { RISK_COLORS } from "@/utils/chartSetup";

const props = defineProps({
  items: { type: Array, required: true }, // [{ period, low, moderate, high, critical }]
});

const levels = ["low", "moderate", "high", "critical"];

const chartData = computed(() => ({
  labels: props.items.map((i) => i.period),
  datasets: levels.map((level) => ({
    label: level,
    data: props.items.map((i) => i[level] || 0),
    backgroundColor: RISK_COLORS[level],
    stack: "risk",
    borderRadius: 3,
  })),
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } } },
  scales: {
    x: { stacked: true },
    y: { stacked: true, beginAtZero: true },
  },
};
</script>
