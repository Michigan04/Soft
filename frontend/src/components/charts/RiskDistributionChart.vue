<template>
  <Doughnut :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from "vue";
import { Doughnut } from "vue-chartjs";
import { RISK_COLORS } from "@/utils/chartSetup";

const props = defineProps({
  items: { type: Array, required: true }, // [{ risk_level, count }]
});

const chartData = computed(() => ({
  labels: props.items.map((i) => i.risk_level),
  datasets: [
    {
      data: props.items.map((i) => i.count),
      backgroundColor: props.items.map((i) => RISK_COLORS[i.risk_level] || "#9499ab"),
      borderWidth: 0,
    },
  ],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: "62%",
  plugins: {
    legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } },
  },
};
</script>
