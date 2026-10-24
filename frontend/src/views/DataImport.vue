<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Academic Data Import</div>
        <div class="page-subtitle">Validate and commit CSV uploads for students, results, registrations, and projects.</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 20px">
      <div class="field">
        <label>Import type</label>
        <select v-model="importType" class="input" style="max-width: 260px" @change="reset">
          <option value="students">Students</option>
          <option value="course_results">Course Results</option>
          <option value="registrations">Registrations</option>
          <option value="projects">Projects</option>
        </select>
      </div>
      <button class="btn btn-secondary btn-sm" style="margin-bottom: 16px" @click="downloadTemplate">
        Download CSV Template
      </button>

      <div class="field">
        <label>CSV file</label>
        <input ref="fileInput" type="file" accept=".csv" class="input" @change="onFileChange" />
      </div>
      <button class="btn btn-primary" :disabled="!file || validating" @click="runValidate">
        {{ validating ? "Validating..." : "Validate File" }}
      </button>
      <p v-if="error" class="field-error" style="margin-top: 10px">{{ error }}</p>
    </div>

    <div v-if="validation" class="card card-pad" style="margin-bottom: 20px">
      <h3 style="margin-bottom: 10px">Validation Report</h3>
      <div class="grid grid-3" style="margin-bottom: 16px">
        <MetricCard label="Total Rows" :value="validation.total_rows" />
        <MetricCard label="Valid Rows" :value="validation.valid_rows" accent="var(--risk-low)" />
        <MetricCard label="Invalid Rows" :value="validation.invalid_rows" accent="var(--risk-critical)" />
      </div>

      <div v-if="validation.row_errors.length" style="margin-bottom: 16px">
        <h4 style="margin-bottom: 8px">Row Errors</h4>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Row</th><th>Errors</th></tr></thead>
            <tbody>
              <tr v-for="re in validation.row_errors" :key="re.row_number">
                <td>{{ re.row_number }}</td>
                <td class="text-sm field-error">{{ re.errors.join("; ") }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <button class="btn btn-primary" :disabled="validation.valid_rows === 0 || committing" @click="confirmCommit = true">
        {{ committing ? "Committing..." : `Commit ${validation.valid_rows} Valid Row(s)` }}
      </button>
    </div>

    <div v-if="importResult" class="card card-pad" style="margin-bottom: 20px">
      <h3 style="margin-bottom: 10px">Import Summary</h3>
      <p class="text-sm">
        Status: <strong>{{ importResult.status }}</strong> &middot;
        Successful: {{ importResult.successful_rows }} &middot; Failed: {{ importResult.failed_rows }}
      </p>
    </div>

    <div class="card">
      <div class="card-pad" style="padding-bottom: 0"><h3>Import History</h3></div>
      <LoadingState v-if="loadingHistory" :rows="4" />
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead><tr><th>File</th><th>Type</th><th>Status</th><th>Total</th><th>Success</th><th>Failed</th><th>Date</th></tr></thead>
          <tbody>
            <tr v-for="imp in history" :key="imp.id">
              <td>{{ imp.filename }}</td>
              <td style="text-transform: capitalize">{{ imp.import_type.replace("_", " ") }}</td>
              <td style="text-transform: capitalize">{{ imp.status }}</td>
              <td>{{ imp.total_rows }}</td>
              <td>{{ imp.successful_rows }}</td>
              <td>{{ imp.failed_rows }}</td>
              <td>{{ new Date(imp.created_at).toLocaleDateString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmDialog
      v-model="confirmCommit"
      title="Commit this import?"
      message="This will permanently write the validated rows to the database."
      confirm-label="Commit"
      @confirm="runCommit"
      @cancel="confirmCommit = false"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import * as importsApi from "@/api/imports";
import { apiErrorMessage } from "@/api/client";
import MetricCard from "@/components/MetricCard.vue";
import LoadingState from "@/components/LoadingState.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

const importType = ref("students");
const file = ref(null);
const fileInput = ref(null);
const validating = ref(false);
const committing = ref(false);
const error = ref("");
const validation = ref(null);
const importResult = ref(null);
const confirmCommit = ref(false);
const history = ref([]);
const loadingHistory = ref(true);

const templates = {
  students: "student_identifier,email,full_name,academic_level,admission_date,current_term\nEX25F000001,example@demo.iitm.ac.in,Example Student,foundation,2026-01-10,Sep 2026 Term\n",
  course_results: "student_identifier,course_code,academic_term_name,result_status,credits,grade,grade_points\nEX25F000001,MATH1001,Sep 2026 Term,pass,4,A,8\n",
  registrations: "student_identifier,course_code,academic_term_name,status\nEX25F000001,MATH1001,Sep 2026 Term,approved\n",
  projects: "student_identifier,title,status,description,start_date,due_date,completion_date,grade\nEX25F000001,Capstone Project,in_progress,,2026-09-01,2027-01-10,,\n",
};

function downloadTemplate() {
  const blob = new Blob([templates[importType.value]], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${importType.value}_template.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function onFileChange(e) {
  file.value = e.target.files[0] || null;
}

function reset() {
  file.value = null;
  validation.value = null;
  importResult.value = null;
  error.value = "";
  if (fileInput.value) fileInput.value.value = "";
}

async function runValidate() {
  validating.value = true;
  error.value = "";
  validation.value = null;
  importResult.value = null;
  try {
    const { data } = await importsApi.validateImport(importType.value, file.value);
    validation.value = data;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    validating.value = false;
  }
}

async function runCommit() {
  confirmCommit.value = false;
  committing.value = true;
  try {
    const { data } = await importsApi.commitImport(validation.value.validation_token);
    importResult.value = data;
    validation.value = null;
    await loadHistory();
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    committing.value = false;
  }
}

async function loadHistory() {
  loadingHistory.value = true;
  const { data } = await importsApi.listImports();
  history.value = data;
  loadingHistory.value = false;
}

onMounted(loadHistory);
</script>
