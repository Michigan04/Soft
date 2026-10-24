<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Interventions &amp; Follow-ups</div>
        <div class="page-subtitle">Track support activities and upcoming or overdue follow-ups.</div>
      </div>
      <button class="btn btn-primary" @click="showForm = true">Log Intervention</button>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px">
      <div class="filters-row">
        <select v-model="statusFilter" class="input" style="max-width: 180px" @change="load">
          <option :value="null">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <label class="flex items-center gap-8 text-sm">
          <input type="checkbox" v-model="overdueOnly" @change="load" />
          Overdue follow-ups only
        </label>
      </div>
    </div>

    <LoadingState v-if="loading" :rows="6" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="items.length === 0" title="No interventions" message="No interventions match these filters." />
    <div v-else class="flex-col gap-16">
      <div v-for="iv in items" :key="iv.id" class="card card-pad">
        <div class="flex items-center justify-between">
          <div style="font-weight: 600; text-transform: capitalize">{{ iv.intervention_type.replace("_", " ") }}</div>
          <span class="badge" :style="statusStyle(iv.status)">{{ iv.status.replace("_", " ") }}</span>
        </div>
        <p class="text-sm" style="margin: 6px 0">{{ iv.description }}</p>
        <div class="text-muted text-sm">
          Student:
          <router-link :to="{ name: 'student-profile', params: { id: iv.student_id } }">View profile</router-link>
          &middot; By {{ iv.staff_user_name || "—" }} &middot; {{ new Date(iv.created_at).toLocaleDateString() }}
          <template v-if="iv.follow_up_date"> &middot; Follow-up: {{ iv.follow_up_date }}</template>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-box">
        <h3 style="margin-bottom: 14px">Log Intervention</h3>
        <div class="field">
          <label>Student</label>
          <input v-model="studentSearch" class="input" placeholder="Search by name or ID..." @input="searchStudents" />
          <div v-if="studentOptions.length" class="dropdown-list">
            <div v-for="s in studentOptions" :key="s.id" class="dropdown-item" @click="selectStudent(s)">
              {{ s.full_name }} ({{ s.student_identifier }})
            </div>
          </div>
        </div>
        <InterventionForm v-if="selectedStudentId" :student-id="selectedStudentId" @created="onCreated" @cancel="showForm = false" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import * as interventionsApi from "@/api/interventions";
import * as studentsApi from "@/api/students";
import { apiErrorMessage } from "@/api/client";
import LoadingState from "@/components/LoadingState.vue";
import ErrorState from "@/components/ErrorState.vue";
import EmptyState from "@/components/EmptyState.vue";
import InterventionForm from "@/components/InterventionForm.vue";

const items = ref([]);
const loading = ref(true);
const error = ref("");
const statusFilter = ref(null);
const overdueOnly = ref(false);
const showForm = ref(false);
const studentSearch = ref("");
const studentOptions = ref([]);
const selectedStudentId = ref(null);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await interventionsApi.listInterventions({
      status: statusFilter.value || undefined,
      overdue_only: overdueOnly.value || undefined,
    });
    items.value = data;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

let searchTimer = null;
function searchStudents() {
  clearTimeout(searchTimer);
  if (!studentSearch.value) {
    studentOptions.value = [];
    return;
  }
  searchTimer = setTimeout(async () => {
    const { data } = await studentsApi.listStudents({ search: studentSearch.value, page_size: 8 });
    studentOptions.value = data.items;
  }, 300);
}

function selectStudent(s) {
  selectedStudentId.value = s.id;
  studentOptions.value = [];
  studentSearch.value = `${s.full_name} (${s.student_identifier})`;
}

function onCreated() {
  showForm.value = false;
  selectedStudentId.value = null;
  studentSearch.value = "";
  load();
}

function statusStyle(status) {
  const colors = { open: "#1c7ed6", in_progress: "#e8a400", completed: "#2f9e44", cancelled: "#9499ab" };
  const c = colors[status] || "#9499ab";
  return { color: c, background: `${c}18` };
}

onMounted(load);
</script>

<style scoped>
.filters-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}
.dropdown-list {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  margin-top: 4px;
  max-height: 160px;
  overflow-y: auto;
}
.dropdown-item {
  padding: 8px 10px;
  cursor: pointer;
  font-size: 13px;
}
.dropdown-item:hover {
  background: #faf5f6;
}
</style>
