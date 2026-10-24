<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Students</div>
        <div class="page-subtitle">Search, filter, and review student risk status across the program.</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px">
      <div class="filters-row">
        <input v-model="search" class="input" placeholder="Search name or ID..." style="max-width: 220px" @input="debouncedReload" />
        <select v-model="academicLevel" class="input" style="max-width: 160px" @change="reload">
          <option :value="null">All levels</option>
          <option value="foundation">Foundation</option>
          <option value="diploma">Diploma</option>
          <option value="degree">Degree</option>
        </select>
        <select v-model="riskLevel" class="input" style="max-width: 160px" @change="reload">
          <option :value="null">All risk levels</option>
          <option value="low">Low</option>
          <option value="moderate">Moderate</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select v-model="programStatus" class="input" style="max-width: 160px" @change="reload">
          <option :value="null">All statuses</option>
          <option value="active">Active</option>
          <option value="on_hold">On hold</option>
          <option value="completed">Completed</option>
          <option value="discontinued">Discontinued</option>
        </select>
        <select v-model="sortBy" class="input" style="max-width: 180px" @change="reload">
          <option value="risk_score">Sort: Risk score</option>
          <option value="latest_assessment">Sort: Latest assessment</option>
          <option value="pending_followups">Sort: Pending follow-ups</option>
          <option value="full_name">Sort: Name</option>
        </select>
        <label class="flex items-center gap-8 text-sm">
          <input type="checkbox" v-model="riskIncreasedOnly" @change="reload" />
          Risk increased only
        </label>
      </div>
    </div>

    <div class="card">
      <LoadingState v-if="loading" :rows="6" />
      <ErrorState v-else-if="error" :message="error" @retry="reload" />
      <EmptyState v-else-if="items.length === 0" title="No students found" message="Try adjusting your filters." />
      <template v-else>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Level</th>
                <th>CGPA</th>
                <th>Risk</th>
                <th>Primary Reason</th>
                <th>Assigned Staff</th>
                <th>Overdue Follow-ups</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in items" :key="s.id" class="clickable" @click="goToProfile(s.id)">
                <td>
                  <div style="font-weight: 600">{{ s.full_name }}</div>
                  <div class="text-muted text-sm">{{ s.student_identifier }}</div>
                </td>
                <td style="text-transform: capitalize">{{ s.academic_level }}</td>
                <td>{{ s.cgpa ?? "—" }}</td>
                <td><RiskBadge :level="s.latest_risk_level" /></td>
                <td class="text-sm">{{ s.primary_risk_reason || "—" }}</td>
                <td class="text-sm">{{ s.assigned_staff_name || "Unassigned" }}</td>
                <td class="text-sm">{{ s.pending_followups }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card-pad">
          <Pagination :page="page" :pages="pages" :total="total" @update:page="(p) => { page = p; reload(); }" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import * as studentsApi from "@/api/students";
import { apiErrorMessage } from "@/api/client";
import RiskBadge from "@/components/RiskBadge.vue";
import LoadingState from "@/components/LoadingState.vue";
import ErrorState from "@/components/ErrorState.vue";
import EmptyState from "@/components/EmptyState.vue";
import Pagination from "@/components/Pagination.vue";

const router = useRouter();

const search = ref("");
const academicLevel = ref(null);
const riskLevel = ref(null);
const programStatus = ref(null);
const sortBy = ref("risk_score");
const riskIncreasedOnly = ref(false);
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const items = ref([]);
const loading = ref(true);
const error = ref("");

let debounceTimer = null;
function debouncedReload() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    page.value = 1;
    reload();
  }, 350);
}

async function reload() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await studentsApi.listStudents({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      academic_level: academicLevel.value || undefined,
      risk_level: riskLevel.value || undefined,
      program_status: programStatus.value || undefined,
      sort_by: sortBy.value,
      sort_dir: "desc",
      risk_increased_only: riskIncreasedOnly.value || undefined,
    });
    items.value = data.items;
    pages.value = data.pages;
    total.value = data.total;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

function goToProfile(id) {
  router.push({ name: "student-profile", params: { id } });
}

onMounted(reload);
</script>

<style scoped>
.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.clickable {
  cursor: pointer;
}
</style>
