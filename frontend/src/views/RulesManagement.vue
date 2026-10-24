<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Rules &amp; Academic Policies</div>
        <div class="page-subtitle">Configure risk indicator thresholds, severities, and policy assumptions.</div>
      </div>
      <button class="btn btn-primary" @click="openCreate">New Risk Rule</button>
    </div>

    <p v-if="feedback" class="text-sm" :style="{ color: feedbackIsError ? 'var(--risk-critical)' : 'var(--risk-low)', marginBottom: '14px' }">
      {{ feedback }}
    </p>

    <div class="card" style="margin-bottom: 20px">
      <LoadingState v-if="loading" :rows="6" />
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>Name</th><th>Indicator</th><th>Level</th><th>Threshold</th><th>Severity</th><th>Weight</th><th>Active</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="r in rules" :key="r.id">
              <td>{{ r.name }}</td>
              <td style="text-transform: capitalize">{{ r.indicator_type.replace("_", " ") }}</td>
              <td style="text-transform: capitalize">{{ r.academic_level || "All" }}</td>
              <td>{{ r.threshold_value }}</td>
              <td><SeverityBadge :severity="r.severity" /></td>
              <td>{{ r.weight }}</td>
              <td>{{ r.is_active ? "Yes" : "No" }}</td>
              <td><button class="btn btn-secondary btn-sm" @click="openEdit(r)">Edit</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 20px">
      <h3 style="margin-bottom: 14px">Risk Level Thresholds</h3>
      <p class="text-muted text-sm" style="margin-bottom: 14px">
        A risk score (0-100) at or above each threshold places a student at that level.
      </p>
      <div class="grid grid-3">
        <div class="field">
          <label>Moderate</label>
          <input v-model.number="riskThresholds.moderate" type="number" class="input" />
        </div>
        <div class="field">
          <label>High</label>
          <input v-model.number="riskThresholds.high" type="number" class="input" />
        </div>
        <div class="field">
          <label>Critical</label>
          <input v-model.number="riskThresholds.critical" type="number" class="input" />
        </div>
      </div>
      <button class="btn btn-secondary" @click="confirmSavePolicy('risk_level_thresholds', riskThresholds)">Save Thresholds</button>
    </div>

    <div class="card card-pad">
      <h3 style="margin-bottom: 14px">CGPA Projection Assumptions</h3>
      <p class="text-muted text-sm" style="margin-bottom: 14px">
        These are development assumptions used for target-CGPA projections, not official IITM policy.
      </p>
      <div class="grid grid-2">
        <div class="field">
          <label>Max grade points</label>
          <input v-model.number="cgpaAssumptions.max_grade_points" type="number" class="input" />
        </div>
        <div class="field">
          <label>Default course credits</label>
          <input v-model.number="cgpaAssumptions.default_course_credits" type="number" class="input" />
        </div>
      </div>
      <button class="btn btn-secondary" @click="confirmSavePolicy('cgpa_assumptions', cgpaAssumptions)">Save Assumptions</button>
    </div>

    <div v-if="editing" class="modal-overlay" @click.self="editing = null">
      <div class="modal-box">
        <h3 style="margin-bottom: 14px">{{ editing.id ? "Edit Risk Rule" : "New Risk Rule" }}</h3>
        <form @submit.prevent="confirmSaveRule">
          <div class="field">
            <label>Name</label>
            <input v-model="editing.name" class="input" required />
          </div>
          <div class="field" v-if="!editing.id">
            <label>Indicator type</label>
            <select v-model="editing.indicator_type" class="input" required>
              <option v-for="i in indicatorTypes" :key="i" :value="i">{{ i.replace("_", " ") }}</option>
            </select>
          </div>
          <div class="field">
            <label>Academic level (optional)</label>
            <select v-model="editing.academic_level" class="input">
              <option :value="null">All levels</option>
              <option value="foundation">Foundation</option>
              <option value="diploma">Diploma</option>
              <option value="degree">Degree</option>
            </select>
          </div>
          <div class="grid grid-2">
            <div class="field">
              <label>Threshold value</label>
              <input v-model.number="editing.threshold_value" type="number" step="0.1" min="0" class="input" required />
            </div>
            <div class="field">
              <label>Weight</label>
              <input v-model.number="editing.weight" type="number" step="0.1" min="0" class="input" required />
            </div>
          </div>
          <div class="field">
            <label>Severity</label>
            <select v-model="editing.severity" class="input" required>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <label class="flex items-center gap-8 text-sm" style="margin-bottom: 16px">
            <input type="checkbox" v-model="editing.is_active" />
            Active
          </label>
          <p v-if="formError" class="field-error" style="margin-bottom: 10px">{{ formError }}</p>
          <div class="flex gap-8" style="justify-content: flex-end">
            <button type="button" class="btn btn-secondary" @click="editing = null">Cancel</button>
            <button type="submit" class="btn btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmDialog
      v-model="confirmOpen"
      title="Apply this change?"
      message="This will immediately affect how risk is calculated program-wide."
      confirm-label="Apply"
      @confirm="runPendingAction"
      @cancel="confirmOpen = false"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import * as rulesApi from "@/api/rules";
import { apiErrorMessage } from "@/api/client";
import SeverityBadge from "@/components/SeverityBadge.vue";
import LoadingState from "@/components/LoadingState.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

const rules = ref([]);
const loading = ref(true);
const editing = ref(null);
const formError = ref("");
const feedback = ref("");
const feedbackIsError = ref(false);
const confirmOpen = ref(false);
const pendingAction = ref(null);

const riskThresholds = reactive({ moderate: 25, high: 50, critical: 75 });
const cgpaAssumptions = reactive({ max_grade_points: 10, default_course_credits: 4 });

const indicatorTypes = [
  "low_cgpa", "failed_courses", "insufficient_credits", "missed_milestone", "pending_courses",
  "incomplete_project", "registration_failures", "inactivity", "overdue_followup",
];

async function load() {
  loading.value = true;
  const [rulesRes, policiesRes] = await Promise.all([rulesApi.listRules(), rulesApi.listPolicies()]);
  rules.value = rulesRes.data;
  if (policiesRes.data.risk_level_thresholds) Object.assign(riskThresholds, policiesRes.data.risk_level_thresholds);
  if (policiesRes.data.cgpa_assumptions) Object.assign(cgpaAssumptions, policiesRes.data.cgpa_assumptions);
  loading.value = false;
}

function openCreate() {
  editing.value = { name: "", indicator_type: indicatorTypes[0], academic_level: null, threshold_value: 1, severity: "warning", weight: 1, is_active: true };
}

function openEdit(rule) {
  editing.value = { ...rule };
}

function confirmSaveRule() {
  formError.value = "";
  if (editing.value.threshold_value < 0 || editing.value.weight < 0) {
    formError.value = "Threshold and weight must be zero or greater.";
    return;
  }
  pendingAction.value = saveRule;
  confirmOpen.value = true;
}

async function saveRule() {
  try {
    if (editing.value.id) {
      await rulesApi.updateRule(editing.value.id, {
        name: editing.value.name, academic_level: editing.value.academic_level,
        threshold_value: editing.value.threshold_value, severity: editing.value.severity,
        weight: editing.value.weight, is_active: editing.value.is_active,
      });
    } else {
      await rulesApi.createRule(editing.value);
    }
    feedback.value = "Risk rule saved successfully.";
    feedbackIsError.value = false;
    editing.value = null;
    await load();
  } catch (e) {
    feedback.value = apiErrorMessage(e);
    feedbackIsError.value = true;
  }
}

function confirmSavePolicy(key, value) {
  pendingAction.value = () => savePolicy(key, value);
  confirmOpen.value = true;
}

async function savePolicy(key, value) {
  try {
    await rulesApi.updatePolicy(key, { ...value });
    feedback.value = "Policy updated successfully.";
    feedbackIsError.value = false;
  } catch (e) {
    feedback.value = apiErrorMessage(e);
    feedbackIsError.value = true;
  }
}

async function runPendingAction() {
  confirmOpen.value = false;
  if (pendingAction.value) await pendingAction.value();
  pendingAction.value = null;
}

onMounted(load);
</script>
