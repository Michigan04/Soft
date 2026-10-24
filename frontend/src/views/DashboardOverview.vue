<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Program Dashboard</div>
        <div class="page-subtitle">Program-wide risk and progression overview, updated live from student records.</div>
      </div>
      <div class="flex gap-8">
        <select v-model="academicLevel" class="input" style="width: auto">
          <option :value="null">All levels</option>
          <option value="foundation">Foundation</option>
          <option value="diploma">Diploma</option>
          <option value="degree">Degree</option>
        </select>
      </div>
    </div>

    <LoadingState v-if="loading" :rows="6" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else>
      <div class="grid grid-4" style="margin-bottom: 20px">
        <MetricCard label="Total Students" :value="summary.total_students" />
        <MetricCard label="At-Risk Students" :value="summary.at_risk_students" accent="var(--risk-moderate)" />
        <MetricCard label="High Risk" :value="summary.high_risk_students" accent="var(--risk-high)" />
        <MetricCard label="Critical Risk" :value="summary.critical_risk_students" accent="var(--risk-critical)" />
      </div>
      <div class="grid grid-2" style="margin-bottom: 20px">
        <MetricCard label="Pending Interventions" :value="summary.pending_interventions" />
        <MetricCard label="Overdue Follow-ups" :value="summary.overdue_followups" accent="var(--risk-critical)" />
      </div>

      <div class="grid grid-2" style="margin-bottom: 20px; align-items: stretch">
        <div class="card card-pad">
          <h3 style="margin-bottom: 14px">Risk Distribution</h3>
          <div style="height: 260px">
            <RiskDistributionChart v-if="riskDistribution.length" :items="riskDistribution" />
            <EmptyState v-else title="No assessments yet" message="Run risk assessments to see distribution." />
          </div>
        </div>
        <div class="card card-pad">
          <h3 style="margin-bottom: 14px">Academic Progression by Level</h3>
          <div style="height: 260px">
            <ProgressionChart v-if="progression.length" :items="progression" />
            <EmptyState v-else title="No data" message="No students found for this filter." />
          </div>
        </div>
      </div>

      <div class="grid grid-2" style="align-items: start">
        <div class="card card-pad">
          <h3 style="margin-bottom: 14px">Students Requiring Attention</h3>
          <div v-if="attentionStudents.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Risk</th>
                  <th>Primary Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="s in attentionStudents"
                  :key="s.id"
                  class="clickable"
                  @click="$router.push({ name: 'student-profile', params: { id: s.id } })"
                >
                  <td>
                    <div style="font-weight: 600">{{ s.full_name }}</div>
                    <div class="text-muted text-sm">{{ s.student_identifier }}</div>
                  </td>
                  <td><RiskBadge :level="s.latest_risk_level" /></td>
                  <td class="text-sm">{{ s.primary_risk_reason || "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState v-else title="All clear" message="No students currently flagged as at-risk." />
        </div>

        <div class="card card-pad">
          <h3 style="margin-bottom: 14px">Recent Alerts</h3>
          <div v-if="recentAlerts.length" class="alert-list">
            <div v-for="n in recentAlerts" :key="n.id" class="alert-item">
              <SeverityBadge :severity="n.severity" />
              <div class="flex-col" style="flex: 1">
                <div style="font-weight: 600; font-size: 13px">{{ n.title }}</div>
                <div class="text-muted text-sm">{{ n.message }}</div>
                <div class="text-muted text-sm">{{ new Date(n.created_at).toLocaleString() }}</div>
              </div>
            </div>
          </div>
          <EmptyState v-else title="No recent alerts" message="You're all caught up." />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import * as dashboardApi from "@/api/dashboard";
import * as studentsApi from "@/api/students";
import * as notificationsApi from "@/api/notifications";
import { apiErrorMessage } from "@/api/client";
import MetricCard from "@/components/MetricCard.vue";
import RiskBadge from "@/components/RiskBadge.vue";
import SeverityBadge from "@/components/SeverityBadge.vue";
import LoadingState from "@/components/LoadingState.vue";
import ErrorState from "@/components/ErrorState.vue";
import EmptyState from "@/components/EmptyState.vue";
import RiskDistributionChart from "@/components/charts/RiskDistributionChart.vue";
import ProgressionChart from "@/components/charts/ProgressionChart.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const loading = ref(true);
const error = ref("");
const academicLevel = ref(null);

const summary = ref({});
const riskDistribution = ref([]);
const progression = ref([]);
const attentionStudents = ref([]);
const recentAlerts = ref([]);

async function load() {
  loading.value = true;
  error.value = "";
  const params = academicLevel.value ? { academic_level: academicLevel.value } : {};
  try {
    const [summaryRes, distRes, progRes, alertsRes] = await Promise.all([
      dashboardApi.getSummary(params),
      dashboardApi.getRiskDistribution(params),
      dashboardApi.getProgressionTrends(params),
      notificationsApi.listNotifications(),
    ]);
    summary.value = summaryRes.data;
    riskDistribution.value = distRes.data.filter((d) => d.count > 0 && d.risk_level !== "unassessed");
    progression.value = progRes.data;
    recentAlerts.value = alertsRes.data.slice(0, 6);

    if (!auth.isStudent) {
      const studentsRes = await studentsApi.listStudents({ page: 1, page_size: 5, sort_by: "risk_score", sort_dir: "desc", ...params });
      attentionStudents.value = studentsRes.data.items.filter((s) => s.latest_risk_level && s.latest_risk_level !== "low");
    }
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(academicLevel, load);
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.alert-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
</style>
