<template>
  <Bar :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from "vue";
import { Bar } from "vue-chartjs";

const props = defineProps({
  items: { type: Array, required: true }, // [{ period, average_cgpa, at_risk_count, total_students }]
});

const chartData = computed(() => ({
  labels: props.items.map((i) => i.period),
  datasets: [
    {
      label: "Average CGPA",
      data: props.items.map((i) => i.average_cgpa),
      backgroundColor: "#8c1d2b",
      yAxisID: "y",
      borderRadius: 4,
    },
    {
      label: "At-risk students",
      data: props.items.map((i) => i.at_risk_count),
      backgroundColor: "#e8a400",
      yAxisID: "y1",
      borderRadius: 4,
    },
  ],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } } },
  scales: {
    y: { type: "linear", position: "left", title: { display: true, text: "CGPA" }, min: 0, max: 10 },
    y1: { type: "linear", position: "right", title: { display: true, text: "At-risk count" }, grid: { drawOnChartArea: false } },
  },
};
</script>
