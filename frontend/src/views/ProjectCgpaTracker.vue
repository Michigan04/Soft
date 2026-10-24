<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Project &amp; CGPA Tracker</div>
        <div class="page-subtitle">Track project milestones, current CGPA, and target-CGPA projections.</div>
      </div>
    </div>

    <div v-if="!auth.isStudent" class="card card-pad" style="margin-bottom: 16px">
      <div class="field" style="margin-bottom: 0">
        <label>Student</label>
        <input v-model="studentSearch" class="input" placeholder="Search by name or ID..." @input="searchStudents" />
        <div v-if="studentOptions.length" class="dropdown-list">
          <div v-for="s in studentOptions" :key="s.id" class="dropdown-item" @click="selectStudent(s)">
            {{ s.full_name }} ({{ s.student_identifier }})
          </div>
        </div>
      </div>
    </div>

    <LoadingState v-if="loading" :rows="5" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="!studentId" title="Select a student" message="Search for a student above to view their CGPA and projects." />

    <template v-else>
      <div class="grid grid-3" style="margin-bottom: 16px">
        <MetricCard label="Current CGPA" :value="cgpaSummary.current_cgpa ?? '—'" />
        <MetricCard label="Completed Credits" :value="cgpaSummary.completed_credits ?? 0" />
        <MetricCard label="Attempted Credits" :value="cgpaSummary.total_attempted_credits ?? 0" />
      </div>

      <div class="grid grid-2" style="align-items: start; margin-bottom: 16px">
        <div class="card card-pad">
          <h3 style="margin-bottom: 10px">Target CGPA Scenarios</h3>
          <div v-if="cgpaSummary.target_scenarios?.length" class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Target</th><th>Remaining Credits</th><th>Required Avg GP</th><th>Feasible</th></tr></thead>
              <tbody>
                <tr v-for="(s, idx) in cgpaSummary.target_scenarios" :key="idx">
                  <td>{{ s.target_cgpa }}</td>
                  <td>{{ s.remaining_credits }}</td>
                  <td>{{ s.required_avg_grade_points ?? "—" }}</td>
                  <td :style="{ color: s.feasible ? 'var(--risk-low)' : 'var(--risk-critical)' }">
                    {{ s.feasible ? "Yes" : "No" }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState v-else title="No scenarios" message="No remaining credits to project." />
          <div style="margin-top: 14px">
            <p class="text-muted text-sm" style="font-weight: 600; margin-bottom: 4px">Assumptions used:</p>
            <ul class="text-muted text-sm" style="margin: 0; padding-left: 18px">
              <li v-for="(a, idx) in cgpaSummary.assumptions" :key="idx">{{ a }}</li>
            </ul>
          </div>
        </div>

        <div class="card card-pad">
          <h3 style="margin-bottom: 10px">Pending Requirements</h3>
          <ul v-if="cgpaSummary.pending_requirements?.length" class="text-sm" style="margin: 0; padding-left: 18px">
            <li v-for="(r, idx) in cgpaSummary.pending_requirements" :key="idx">{{ r }}</li>
          </ul>
          <EmptyState v-else title="All milestones complete" message="No pending requirements for this level." />
        </div>
      </div>

      <div class="card card-pad">
        <div class="flex items-center justify-between" style="margin-bottom: 10px">
          <h3>Projects</h3>
          <button v-if="canManage" class="btn btn-secondary btn-sm" @click="showProjectForm = true">New Project</button>
        </div>
        <div v-if="projects.length" class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Title</th><th>Status</th><th>Due</th><th>Grade</th></tr></thead>
            <tbody>
              <tr v-for="p in projects" :key="p.id">
                <td>{{ p.title }}</td>
                <td style="text-transform: capitalize">{{ p.status.replace("_", " ") }}</td>
                <td>{{ p.due_date || "—" }}</td>
                <td>{{ p.grade || "—" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="No projects" message="No projects recorded for this student." />
      </div>
    </template>

    <div v-if="showProjectForm" class="modal-overlay" @click.self="showProjectForm = false">
      <div class="modal-box">
        <h3 style="margin-bottom: 14px">New Project</h3>
        <form @submit.prevent="createNewProject">
          <div class="field">
            <label>Title</label>
            <input v-model="newProject.title" class="input" required />
          </div>
          <div class="field">
            <label>Due date</label>
            <input v-model="newProject.due_date" type="date" class="input" />
          </div>
          <div class="flex gap-8" style="justify-content: flex-end">
            <button type="button" class="btn btn-secondary" @click="showProjectForm = false">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import * as studentsApi from "@/api/students";
import * as projectsApi from "@/api/projects";
import { apiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import MetricCard from "@/components/MetricCard.vue";
import LoadingState from "@/components/LoadingState.vue";
import ErrorState from "@/components/ErrorState.vue";
import EmptyState from "@/components/EmptyState.vue";

const auth = useAuthStore();
const canManage = auth.isAdmin || auth.isStaff;

const studentId = ref(auth.isStudent ? auth.user?.student_id : null);
const studentSearch = ref("");
const studentOptions = ref([]);
const loading = ref(false);
const error = ref("");
const cgpaSummary = ref({});
const projects = ref([]);
const showProjectForm = ref(false);
const newProject = reactive({ title: "", due_date: "" });

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
  studentId.value = s.id;
  studentOptions.value = [];
  studentSearch.value = `${s.full_name} (${s.student_identifier})`;
  load();
}

async function load() {
  if (!studentId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [cgpaRes, projectsRes] = await Promise.all([
      studentsApi.getCgpaSummary(studentId.value),
      studentsApi.getStudentProjects(studentId.value),
    ]);
    cgpaSummary.value = cgpaRes.data;
    projects.value = projectsRes.data;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function createNewProject() {
  await projectsApi.createProject({
    student_id: studentId.value,
    title: newProject.title,
    due_date: newProject.due_date || null,
  });
  showProjectForm.value = false;
  newProject.title = "";
  newProject.due_date = "";
  load();
}

onMounted(load);
</script>

<style scoped>
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
