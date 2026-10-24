<template>
  <div class="page">
    <LoadingState v-if="loading" :rows="8" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else>
      <div class="page-header">
        <div>
          <div class="page-title">{{ student.full_name }}</div>
          <div class="page-subtitle">
            {{ student.student_identifier }} &middot;
            <span style="text-transform: capitalize">{{ student.academic_level }}</span> &middot;
            <span style="text-transform: capitalize">{{ student.program_status.replace("_", " ") }}</span>
          </div>
        </div>
        <div class="flex gap-8 items-center">
          <RiskBadge :level="latestAssessment?.risk_level" />
          <button v-if="canManage" class="btn btn-secondary btn-sm" @click="assessNow" :disabled="assessing">
            {{ assessing ? "Assessing..." : "Assess Risk Now" }}
          </button>
          <button v-if="canManage" class="btn btn-primary btn-sm" @click="showInterventionForm = true">
            Log Intervention
          </button>
        </div>
      </div>

      <div class="tabs">
        <button v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
          {{ t.label }}
        </button>
      </div>

      <!-- Overview -->
      <div v-if="activeTab === 'overview'" class="grid grid-3">
        <MetricCard label="Current CGPA" :value="history.cgpa ?? '—'" />
        <MetricCard label="Completed Credits" :value="history.completed_credits ?? 0" />
        <MetricCard label="Assigned Staff" :value="student.assigned_staff_name || 'Unassigned'" />

        <div class="card card-pad" style="grid-column: 1 / -1">
          <h3 style="margin-bottom: 10px">Why is this student at this risk level?</h3>
          <p v-if="!latestAssessment" class="text-muted">No risk assessment has been run for this student yet.</p>
          <template v-else>
            <p class="text-muted" style="margin-bottom: 10px">{{ latestAssessment.summary }}</p>
            <p v-if="latestAssessment.data_completeness_note" class="field-error" style="margin-bottom: 14px">
              {{ latestAssessment.data_completeness_note }}
            </p>
            <div v-if="latestAssessment.factors.length" class="factor-list">
              <div v-for="f in latestAssessment.factors" :key="f.id" class="factor-row">
                <SeverityBadge :severity="f.severity" />
                <div>
                  <div style="font-weight: 600; font-size: 13px">{{ f.factor_name }}</div>
                  <div class="text-muted text-sm">{{ f.explanation }}</div>
                  <div v-if="f.recommended_action" class="text-sm" style="color: var(--color-primary); margin-top: 2px">
                    Suggested: {{ f.recommended_action }}
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-muted">No risk indicators are currently triggered.</p>
          </template>
        </div>
      </div>

      <!-- Academic History -->
      <div v-else-if="activeTab === 'academic'">
        <div class="card card-pad" style="margin-bottom: 16px">
          <h3 style="margin-bottom: 10px">Course Results</h3>
          <div v-if="history.course_results?.length" class="table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>Course</th><th>Term</th><th>Grade</th><th>Grade Points</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="r in history.course_results" :key="r.id">
                  <td>{{ r.course_code }} &mdash; {{ r.course_name }}</td>
                  <td>{{ r.academic_term_name }}</td>
                  <td>{{ r.grade || "—" }}</td>
                  <td>{{ r.grade_points ?? "—" }}</td>
                  <td style="text-transform: capitalize">{{ r.result_status.replace("_", " ") }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState v-else title="No course results" message="No results have been recorded yet." />
        </div>

        <div class="card card-pad">
          <h3 style="margin-bottom: 10px">Registrations</h3>
          <div v-if="history.registrations?.length" class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Course</th><th>Status</th><th>Validation</th><th>Errors</th></tr></thead>
              <tbody>
                <tr v-for="r in history.registrations" :key="r.id">
                  <td>{{ r.course_code }} &mdash; {{ r.course_name }}</td>
                  <td style="text-transform: capitalize">{{ r.status }}</td>
                  <td style="text-transform: capitalize">{{ r.validation_status.replace("_", " ") }}</td>
                  <td class="text-sm text-muted">{{ (r.validation_errors || []).join("; ") || "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState v-else title="No registrations" message="No registrations found for this student." />
        </div>
      </div>

      <!-- Projects -->
      <div v-else-if="activeTab === 'projects'" class="card card-pad">
        <h3 style="margin-bottom: 10px">Projects</h3>
        <div v-if="projects.length" class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Title</th><th>Status</th><th>Due</th><th>Completed</th><th>Grade</th><th>Supervisor</th></tr></thead>
            <tbody>
              <tr v-for="p in projects" :key="p.id">
                <td>{{ p.title }}</td>
                <td style="text-transform: capitalize">{{ p.status.replace("_", " ") }}</td>
                <td>{{ p.due_date || "—" }}</td>
                <td>{{ p.completion_date || "—" }}</td>
                <td>{{ p.grade || "—" }}</td>
                <td>{{ p.supervisor_name || "—" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No projects" message="No projects have been assigned yet." />
      </div>

      <!-- Risk Analysis -->
      <div v-else-if="activeTab === 'risk'" class="card card-pad">
        <h3 style="margin-bottom: 14px">Risk Assessment History</h3>
        <div v-if="riskHistory.length" class="risk-history">
          <div v-for="a in riskHistory" :key="a.id" class="risk-history-item">
            <div class="flex items-center justify-between" style="margin-bottom: 6px">
              <RiskBadge :level="a.risk_level" />
              <span class="text-muted text-sm">{{ new Date(a.assessment_date).toLocaleString() }}</span>
            </div>
            <div class="text-sm" style="margin-bottom: 6px">Score: {{ a.risk_score }}/100 &mdash; {{ a.summary }}</div>
            <ul class="text-sm text-muted" style="margin: 0; padding-left: 18px">
              <li v-for="f in a.factors" :key="f.id">{{ f.factor_name }}: {{ f.explanation }}</li>
            </ul>
          </div>
        </div>
        <EmptyState v-else title="No assessments" message="No risk assessments have been run yet." />
      </div>

      <!-- Interventions -->
      <div v-else-if="activeTab === 'interventions'" class="card card-pad">
        <h3 style="margin-bottom: 14px">Interventions</h3>
        <div v-if="interventions.length" class="flex-col gap-16">
          <div v-for="iv in interventions" :key="iv.id" class="intervention-card">
            <div class="flex items-center justify-between">
              <div style="font-weight: 600; text-transform: capitalize">{{ iv.intervention_type.replace("_", " ") }}</div>
              <span class="badge" :style="statusStyle(iv.status)">{{ iv.status.replace("_", " ") }}</span>
            </div>
            <p class="text-sm" style="margin: 6px 0">{{ iv.description }}</p>
            <div class="text-muted text-sm">
              By {{ iv.staff_user_name || "—" }} &middot; {{ new Date(iv.created_at).toLocaleDateString() }}
              <template v-if="iv.follow_up_date"> &middot; Follow-up: {{ iv.follow_up_date }}</template>
              <template v-if="iv.outcome"> &middot; Outcome: {{ iv.outcome.replace("_", " ") }}</template>
            </div>
            <div v-if="canManage && iv.status !== 'completed' && iv.status !== 'cancelled'" class="flex gap-8" style="margin-top: 8px">
              <select class="input" style="width: auto" @change="updateOutcome(iv, $event.target.value)">
                <option value="">Mark outcome...</option>
                <option value="improved">Improved</option>
                <option value="no_change">No Change</option>
                <option value="further_support_required">Further Support Required</option>
                <option value="unable_to_contact">Unable to Contact</option>
              </select>
            </div>
          </div>
        </div>
        <EmptyState v-else title="No interventions" message="No interventions have been logged." />
      </div>

      <!-- Activity History -->
      <div v-else-if="activeTab === 'activity'" class="card card-pad">
        <h3 style="margin-bottom: 14px">Activity Timeline</h3>
        <div v-if="timeline.length" class="timeline">
          <div v-for="(ev, idx) in timeline" :key="idx" class="timeline-item">
            <div class="timeline-dot"></div>
            <div>
              <div style="font-weight: 600; font-size: 13px">{{ ev.title }}</div>
              <div class="text-muted text-sm">{{ ev.date }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="No activity" message="No activity recorded yet." />
      </div>
    </template>

    <div v-if="showInterventionForm" class="modal-overlay" @click.self="showInterventionForm = false">
      <div class="modal-box">
        <h3 style="margin-bottom: 14px">Log Intervention</h3>
        <InterventionForm :student-id="studentId" @created="onInterventionCreated" @cancel="showInterventionForm = false" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import * as studentsApi from "@/api/students";
import * as interventionsApi from "@/api/interventions";
import { apiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import MetricCard from "@/components/MetricCard.vue";
import RiskBadge from "@/components/RiskBadge.vue";
import SeverityBadge from "@/components/SeverityBadge.vue";
import LoadingState from "@/components/LoadingState.vue";
import ErrorState from "@/components/ErrorState.vue";
import EmptyState from "@/components/EmptyState.vue";
import InterventionForm from "@/components/InterventionForm.vue";

const props = defineProps({ id: { type: String, required: true } });
const studentId = computed(() => props.id);

const auth = useAuthStore();
const canManage = computed(() => auth.role === "admin" || auth.role === "faculty" || auth.role === "ta");

const loading = ref(true);
const error = ref("");
const student = ref({});
const history = ref({});
const riskHistory = ref([]);
const projects = ref([]);
const interventions = ref([]);
const assessing = ref(false);
const showInterventionForm = ref(false);
const activeTab = ref("overview");

const tabs = [
  { key: "overview", label: "Overview" },
  { key: "academic", label: "Academic History" },
  { key: "projects", label: "Projects" },
  { key: "risk", label: "Risk Analysis" },
  { key: "interventions", label: "Interventions" },
  { key: "activity", label: "Activity History" },
];

const latestAssessment = computed(() => riskHistory.value[0] || null);

const timeline = computed(() => {
  const events = [];
  (history.value.course_results || []).forEach((r) =>
    events.push({ date: r.recorded_at, title: `Result recorded: ${r.course_code} (${r.result_status})` }),
  );
  riskHistory.value.forEach((a) =>
    events.push({ date: a.assessment_date, title: `Risk assessed as ${a.risk_level.toUpperCase()} (${a.risk_score}/100)` }),
  );
  interventions.value.forEach((iv) =>
    events.push({ date: iv.created_at, title: `Intervention logged: ${iv.intervention_type.replace("_", " ")}` }),
  );
  return events
    .map((e) => ({ ...e, _t: new Date(e.date).getTime() }))
    .sort((a, b) => b._t - a._t)
    .map((e) => ({ title: e.title, date: new Date(e.date).toLocaleString() }));
});

function statusStyle(status) {
  const colors = { open: "#1c7ed6", in_progress: "#e8a400", completed: "#2f9e44", cancelled: "#9499ab" };
  const c = colors[status] || "#9499ab";
  return { color: c, background: `${c}18` };
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [studentRes, historyRes, riskRes, projectsRes, interventionsRes] = await Promise.all([
      studentsApi.getStudent(studentId.value),
      studentsApi.getAcademicHistory(studentId.value),
      studentsApi.getRiskAssessments(studentId.value),
      studentsApi.getStudentProjects(studentId.value),
      studentsApi.getStudentInterventions(studentId.value),
    ]);
    student.value = studentRes.data;
    history.value = historyRes.data;
    riskHistory.value = riskRes.data;
    projects.value = projectsRes.data;
    interventions.value = interventionsRes.data;
  } catch (e) {
    error.value = apiErrorMessage(e, "Could not load this student's profile.");
  } finally {
    loading.value = false;
  }
}

async function assessNow() {
  assessing.value = true;
  try {
    await studentsApi.triggerRiskAssessment(studentId.value);
    const { data } = await studentsApi.getRiskAssessments(studentId.value);
    riskHistory.value = data;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    assessing.value = false;
  }
}

async function onInterventionCreated() {
  showInterventionForm.value = false;
  const { data } = await studentsApi.getStudentInterventions(studentId.value);
  interventions.value = data;
}

async function updateOutcome(intervention, outcome) {
  if (!outcome) return;
  await interventionsApi.updateIntervention(intervention.id, { outcome, status: "completed" });
  const { data } = await studentsApi.getStudentInterventions(studentId.value);
  interventions.value = data;
}

onMounted(load);
watch(studentId, load);
</script>

<style scoped>
.factor-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.factor-row {
  display: flex;
  gap: 10px;
}
.risk-history-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);
}
.risk-history-item:last-child {
  border-bottom: none;
}
.intervention-card {
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.timeline-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  margin-top: 6px;
  flex-shrink: 0;
}
</style>
