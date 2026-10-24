<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Staff Assignments</div>
        <div class="page-subtitle">Assign students to faculty/TAs and monitor workload.</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px">
      <h3 style="margin-bottom: 10px">Staff Workload</h3>
      <LoadingState v-if="loadingWorkload" :rows="3" />
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Staff</th><th>Role</th><th>Assigned Students</th><th>Open Interventions</th><th>Overdue Follow-ups</th></tr></thead>
          <tbody>
            <tr v-for="w in workload" :key="w.staff_user_id">
              <td>{{ w.staff_name }}</td>
              <td style="text-transform: capitalize">{{ w.role }}</td>
              <td>{{ w.assigned_student_count }}</td>
              <td>{{ w.open_interventions }}</td>
              <td>{{ w.overdue_followups }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card card-pad">
      <div class="flex items-center justify-between" style="margin-bottom: 10px">
        <h3>Students</h3>
        <input v-model="search" class="input" placeholder="Search..." style="max-width: 220px" @input="debouncedReload" />
      </div>
      <LoadingState v-if="loadingStudents" :rows="6" />
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Student</th><th>Level</th><th>Currently Assigned</th><th>Reassign to</th></tr></thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td>{{ s.full_name }} <span class="text-muted text-sm">({{ s.student_identifier }})</span></td>
              <td style="text-transform: capitalize">{{ s.academic_level }}</td>
              <td>{{ s.assigned_staff_name || "Unassigned" }}</td>
              <td>
                <select class="input" style="width: auto" @change="assign(s, $event.target.value)">
                  <option value="">Select staff...</option>
                  <option v-for="w in workload" :key="w.staff_user_id" :value="w.staff_user_id">{{ w.staff_name }}</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination :page="page" :pages="pages" :total="total" @update:page="(p) => { page = p; loadStudents(); }" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import * as assignmentsApi from "@/api/assignments";
import * as studentsApi from "@/api/students";
import LoadingState from "@/components/LoadingState.vue";
import Pagination from "@/components/Pagination.vue";

const workload = ref([]);
const loadingWorkload = ref(true);
const students = ref([]);
const loadingStudents = ref(true);
const search = ref("");
const page = ref(1);
const pages = ref(1);
const total = ref(0);

async function loadWorkload() {
  loadingWorkload.value = true;
  const { data } = await assignmentsApi.getStaffWorkload();
  workload.value = data;
  loadingWorkload.value = false;
}

async function loadStudents() {
  loadingStudents.value = true;
  const { data } = await studentsApi.listStudents({ page: page.value, page_size: 15, search: search.value || undefined, sort_by: "full_name", sort_dir: "asc" });
  students.value = data.items;
  pages.value = data.pages;
  total.value = data.total;
  loadingStudents.value = false;
}

let debounceTimer = null;
function debouncedReload() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    page.value = 1;
    loadStudents();
  }, 350);
}

async function assign(student, staffId) {
  if (!staffId) return;
  await assignmentsApi.assignStudent(student.id, staffId);
  await Promise.all([loadStudents(), loadWorkload()]);
}

onMounted(() => {
  loadWorkload();
  loadStudents();
});
</script>
