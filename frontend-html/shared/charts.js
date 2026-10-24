/*
 * Plain-JS port of frontend/src/utils/chartSetup.js + frontend/src/components/charts/*.vue.
 * Uses Chart.js directly (UMD build) instead of vue-chartjs, since there is no
 * bundler here. Needs the Chart.js CDN script loaded first (exposes window.Chart).
 */
(function () {
  Chart.register(
    Chart.ArcElement,
    Chart.BarElement,
    Chart.CategoryScale,
    Chart.LinearScale,
    Chart.LineElement,
    Chart.PointElement,
    Chart.Legend,
    Chart.Tooltip,
  );

  const RISK_COLORS = {
    low: "#2f9e44",
    moderate: "#e8a400",
    high: "#e8590c",
    critical: "#c92a2a",
    unassessed: "#9499ab",
  };

  // Base for every chart component: owns the canvas + Chart.js instance
  // lifecycle (create on mount, recreate whenever `items` changes, destroy on
  // unmount) so each concrete chart only has to provide buildConfig(items).
  const chartBase = {
    props: { items: { type: Array, required: true } },
    data() {
      return { chart: null };
    },
    mounted() {
      this.render();
    },
    beforeUnmount() {
      if (this.chart) this.chart.destroy();
    },
    watch: {
      items: {
        deep: true,
        handler() {
          this.render();
        },
      },
    },
    methods: {
      render() {
        if (this.chart) this.chart.destroy();
        this.chart = new Chart(this.$refs.canvas, this.buildConfig());
      },
    },
    template: `<canvas ref="canvas"></canvas>`,
  };

  const ProgressionChart = {
    ...chartBase,
    methods: {
      ...chartBase.methods,
      buildConfig() {
        return {
          type: "bar",
          data: {
            labels: this.items.map((i) => i.period),
            datasets: [
              {
                label: "Average CGPA",
                data: this.items.map((i) => i.average_cgpa),
                backgroundColor: "#8c1d2b",
                yAxisID: "y",
                borderRadius: 4,
              },
              {
                label: "At-risk students",
                data: this.items.map((i) => i.at_risk_count),
                backgroundColor: "#e8a400",
                yAxisID: "y1",
                borderRadius: 4,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } } },
            scales: {
              y: { type: "linear", position: "left", title: { display: true, text: "CGPA" }, min: 0, max: 10 },
              y1: { type: "linear", position: "right", title: { display: true, text: "At-risk count" }, grid: { drawOnChartArea: false } },
            },
          },
        };
      },
    },
  };

  const RiskDistributionChart = {
    ...chartBase,
    methods: {
      ...chartBase.methods,
      buildConfig() {
        return {
          type: "doughnut",
          data: {
            labels: this.items.map((i) => i.risk_level),
            datasets: [
              {
                data: this.items.map((i) => i.count),
                backgroundColor: this.items.map((i) => RISK_COLORS[i.risk_level] || "#9499ab"),
                borderWidth: 0,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "62%",
            plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } } },
          },
        };
      },
    },
  };

  const RISK_LEVELS = ["low", "moderate", "high", "critical"];
  const RiskTrendChart = {
    ...chartBase,
    methods: {
      ...chartBase.methods,
      buildConfig() {
        return {
          type: "bar",
          data: {
            labels: this.items.map((i) => i.period),
            datasets: RISK_LEVELS.map((level) => ({
              label: level,
              data: this.items.map((i) => i[level] || 0),
              backgroundColor: RISK_COLORS[level],
              stack: "risk",
              borderRadius: 3,
            })),
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } } } },
            scales: {
              x: { stacked: true },
              y: { stacked: true, beginAtZero: true },
            },
          },
        };
      },
    },
  };

  window.Charts = { RISK_COLORS, ProgressionChart, RiskDistributionChart, RiskTrendChart };
})();
