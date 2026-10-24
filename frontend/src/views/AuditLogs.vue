<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Audit Logs</div>
        <div class="page-subtitle">Immutable record of significant changes across the platform.</div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px">
      <div class="filters-row">
        <select v-model="entityType" class="input" style="max-width: 200px" @change="reload">
          <option :value="null">All entity types</option>
          <option value="student">Student</option>
          <option value="risk_rule">Risk Rule</option>
          <option value="policy_setting">Policy Setting</option>
          <option value="intervention">Intervention</option>
          <option value="student_assignment">Student Assignment</option>
          <option value="data_import">Data Import</option>
          <option value="project">Project</option>
        </select>
        <select v-model="action" class="input" style="max-width: 180px" @change="reload">
          <option :value="null">All actions</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="assign">Assign</option>
          <option value="validate">Validate</option>
          <option value="commit">Commit</option>
          <option value="assess_risk">Assess Risk</option>
        </select>
        <input v-model="startDate" type="date" class="input" style="max-width: 160px" @change="reload" />
        <input v-model="endDate" type="date" class="input" style="max-width: 160px" @change="reload" />
      </div>
    </div>

    <div class="card">
      <LoadingState v-if="loading" :rows="6" />
      <EmptyState v-else-if="items.length === 0" title="No audit events" message="No events match these filters." />
      <template v-else>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Date</th><th>Actor</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
            <tbody>
              <tr v-for="log in items" :key="log.id">
                <td class="text-sm">{{ new Date(log.created_at).toLocaleString() }}</td>
                <td class="text-sm">{{ log.actor_name || "System" }}</td>
                <td style="text-transform: capitalize">{{ log.action }}</td>
                <td style="text-transform: capitalize">{{ log.entity_type.replace("_", " ") }}</td>
                <td class="text-sm text-muted">
                  <span v-if="log.after_data">{{ JSON.stringify(log.after_data) }}</span>
                </td>
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
import * as auditApi from "@/api/audit";
import LoadingState from "@/components/LoadingState.vue";
import EmptyState from "@/components/EmptyState.vue";
import Pagination from "@/components/Pagination.vue";

const items = ref([]);
const loading = ref(true);
const entityType = ref(null);
const action = ref(null);
const startDate = ref("");
const endDate = ref("");
const page = ref(1);
const pages = ref(1);
const total = ref(0);

async function reload() {
  loading.value = true;
  const { data } = await auditApi.listAuditLogs({
    page: page.value, page_size: 25,
    entity_type: entityType.value || undefined,
    action: action.value || undefined,
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
  });
  items.value = data.items;
  pages.value = data.pages;
  total.value = data.total;
  loading.value = false;
}

onMounted(reload);
</script>

<style scoped>
.filters-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
