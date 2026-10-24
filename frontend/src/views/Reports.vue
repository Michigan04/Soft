<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Reports &amp; Analytics</div>
        <div class="page-subtitle">Program-wide trends, progression, and intervention outcomes.</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 20px">
      <div class="filters-row">
        <div class="field" style="margin-bottom: 0">
          <label>From</label>
          <input v-model="startDate" type="date" class="input" @change="loadAll" />
        </div>
        <div class="field" style="margin-bottom: 0">
          <label>To</label>
          <input v-model="endDate" type="date" class="input" @change="loadAll" />
        </div>
        <div class="field" style="margin-bottom: 0">
          <label>Academic level</label>
          <select v-model="academicLevel" class="input" @change="loadAll">
            <option :value="null">All levels</option>
            <option value="foundation">Foundation</option>
            <option value="diploma">Diploma</option>
            <option value="degree">Degree</option>
          </select>
        </div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 20px">
      <div class="flex items-center justify-between" style="margin-bottom: 14px">
        <h3>Risk Level Trends (historical)</h3>
        <button class="btn btn-secondary btn-sm" @click="downloadReportCsv('risk-trends', params)">Export CSV</button>
      </div>
      <div style="height: 280px">
        <RiskTrendChart v-if="riskTrends.length" :items="riskTrends" />
        <EmptyState v-else title="No data" message="No risk assessments in this range." />
      </div>
    </div>

    <div class="grid grid-2" style="align-items: start; margin-bottom: 20px">
      <div class="card card-pad">
        <div class="flex items-center justify-between" style="margin-bottom: 10px">
          <h3>Progression by Level</h3>
          <button class="btn btn-secondary btn-sm" @click="downloadReportCsv('progression', { academic_level: academicLevel })">Export CSV</button>
        </div>
        <table class="data-table">
          <thead><tr><th>Level</th><th>Students</th><th>Avg CGPA</th></tr></thead>
          <tbody>
            <tr v-for="p in progression" :key="p.academic_level">
              <td style="text-transform: capitalize">{{ p.academic_level }}</td>
              <td>{{ p.student_count }}</td>
              <td>{{ p.average_cgpa ?? "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card card-pad">
        <div class="flex items-center justify-between" style="margin-bottom: 10px">
          <h3>Intervention Outcomes</h3>
          <button class="btn btn-secondary btn-sm" @click="downloadReportCsv('intervention-outcomes', params)">Export CSV</button>
        </div>
        <table class="data-table">
          <thead><tr><th>Outcome</th><th>Count</th></tr></thead>
          <tbody>
            <tr v-for="o in interventionOutcomes" :key="o.outcome">
              <td style="text-transform: capitalize">{{ o.outcome.replace("_", " ") }}</td>
              <td>{{ o.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card card-pad">
      <div class="flex items-center justify-between" style="margin-bottom: 10px">
        <h3>Overdue Follow-ups</h3>
        <button class="btn btn-secondary btn-sm" @click="downloadReportCsv('overdue-followups')">Export CSV</button>
      </div>
      <EmptyState v-if="overdueFollowups.length === 0" title="None overdue" message="No overdue follow-ups right now." />
      <table v-else class="data-table">
        <thead><tr><th>Intervention</th><th>Status</th><th>Follow-up Date</th><th>Days Overdue</th></tr></thead>
        <tbody>
          <tr v-for="f in overdueFollowups" :key="f.intervention_id">
            <td>{{ f.intervention_id.slice(0, 8) }}</td>
            <td style="text-transform: capitalize">{{ f.status }}</td>
            <td>{{ f.follow_up_date }}</td>
            <td>{{ f.days_overdue }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import * as reportsApi from "@/api/reports";
import { downloadReportCsv } from "@/api/reports";
import RiskTrendChart from "@/components/charts/RiskTrendChart.vue";
import EmptyState from "@/components/EmptyState.vue";

const startDate = ref("");
const endDate = ref("");
const academicLevel = ref(null);

const riskTrends = ref([]);
const progression = ref([]);
const interventionOutcomes = ref([]);
const overdueFollowups = ref([]);

const params = computed(() => ({
  start_date: startDate.value || undefined,
  end_date: endDate.value || undefined,
  academic_level: academicLevel.value || undefined,
}));

async function loadAll() {
  const [trendsRes, progRes, outcomesRes, overdueRes] = await Promise.all([
    reportsApi.getRiskTrends(params.value),
    reportsApi.getProgression({ academic_level: academicLevel.value || undefined }),
    reportsApi.getInterventionOutcomes(params.value),
    reportsApi.getOverdueFollowups(),
  ]);
  riskTrends.value = trendsRes.data;
  progression.value = progRes.data;
  interventionOutcomes.value = outcomesRes.data;
  overdueFollowups.value = overdueRes.data;
}

onMounted(loadAll);
</script>

<style scoped>
.filters-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
</style>
