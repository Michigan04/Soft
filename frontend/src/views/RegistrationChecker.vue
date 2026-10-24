<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Registration Checker</div>
        <div class="page-subtitle">
          Validate course selections against prerequisites and academic rules before registering.
        </div>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px">
      <div v-if="!auth.isStudent" class="field">
        <label>Student</label>
        <input
          v-model="studentSearch"
          class="input"
          placeholder="Search by name or ID..."
          @input="searchStudents"
        />
        <div v-if="studentOptions.length" class="dropdown-list">
          <div
            v-for="s in studentOptions"
            :key="s.id"
            class="dropdown-item"
            @click="selectStudent(s)"
          >
            {{ s.full_name }} ({{ s.student_identifier }})
          </div>
        </div>
      </div>
      <p v-if="selectedStudent" class="text-sm" style="margin-bottom: 10px">
        Registering for: <strong>{{ selectedStudent.full_name }}</strong>
        ({{ selectedStudent.student_identifier }}, {{ selectedStudent.academic_level }})
      </p>

      <div class="field">
        <label>Academic Term</label>
        <select v-model="termId" class="input">
          <option v-for="t in terms" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </div>

      <div v-if="courses.length" class="field">
        <label>Courses</label>
        <div class="course-grid">
          <label v-for="c in courses" :key="c.id" class="course-chip">
            <input type="checkbox" :value="c.id" v-model="selectedCourseIds" />
            {{ c.course_code }} &mdash; {{ c.course_name }}
          </label>
        </div>
      </div>

      <div class="flex gap-8">
        <button class="btn btn-secondary" :disabled="!canCheck" @click="validate">
          {{ validating ? "Validating..." : "Validate Selection" }}
        </button>
        <button class="btn btn-primary" :disabled="!canSubmit" @click="submit">
          {{ submitting ? "Submitting..." : "Submit Registration" }}
        </button>
      </div>
      <p v-if="error" class="field-error" style="margin-top: 10px">{{ error }}</p>
    </div>

    <div v-if="validationResult" class="card card-pad">
      <h3 style="margin-bottom: 12px">
        Validation Result:
        <span :style="{ color: validationResult.overall_valid ? 'var(--risk-low)' : 'var(--risk-critical)' }">
          {{ validationResult.overall_valid ? "All selections valid" : "Some selections are invalid" }}
        </span>
      </h3>
      <div class="result-list">
        <div v-for="r in validationResult.results" :key="r.course_id" class="result-row">
          <span class="badge" :style="r.is_valid ? validStyle : invalidStyle">
            {{ r.is_valid ? "Valid" : "Invalid" }}
          </span>
          <div>
            <div style="font-weight: 600; font-size: 13px">{{ r.course_code }} &mdash; {{ r.course_name }}</div>
            <ul v-if="r.errors.length" class="text-sm field-error" style="margin: 4px 0 0; padding-left: 18px">
              <li v-for="(e, idx) in r.errors" :key="idx">{{ e }}</li>
            </ul>
          </div>
        </div>
      </div>
      <p class="text-muted text-sm" style="margin-top: 12px">
        Invalid selections will be recorded as rejected and cannot be submitted as approved registrations.
      </p>
    </div>

    <div v-if="submittedRegistrations.length" class="card card-pad" style="margin-top: 16px">
      <h3 style="margin-bottom: 12px">Submitted Registrations</h3>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Course</th><th>Status</th><th>Validation</th></tr></thead>
          <tbody>
            <tr v-for="r in submittedRegistrations" :key="r.id">
              <td>{{ r.course_code }} &mdash; {{ r.course_name }}</td>
              <td style="text-transform: capitalize">{{ r.status }}</td>
              <td style="text-transform: capitalize">{{ r.validation_status.replace("_", " ") }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import * as academicApi from "@/api/academic";
import * as studentsApi from "@/api/students";
import * as registrationsApi from "@/api/registrations";
import { apiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const terms = ref([]);
const termId = ref(null);
const courses = ref([]);
const selectedCourseIds = ref([]);
const studentSearch = ref("");
const studentOptions = ref([]);
const selectedStudent = ref(null);
const validationResult = ref(null);
const submittedRegistrations = ref([]);
const validating = ref(false);
const submitting = ref(false);
const error = ref("");

const effectiveStudentId = computed(() => (auth.isStudent ? auth.user?.student_id : selectedStudent.value?.id));

const canCheck = computed(() => effectiveStudentId.value && termId.value && selectedCourseIds.value.length > 0);
const canSubmit = computed(() => canCheck.value && validationResult.value);

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
  selectedStudent.value = s;
  studentOptions.value = [];
  studentSearch.value = `${s.full_name} (${s.student_identifier})`;
  loadCoursesForLevel(s.academic_level);
}

async function loadCoursesForLevel(level) {
  const { data } = await academicApi.listCourses({ academic_level: level });
  courses.value = data;
  selectedCourseIds.value = [];
  validationResult.value = null;
}

async function validate() {
  validating.value = true;
  error.value = "";
  validationResult.value = null;
  try {
    const { data } = await registrationsApi.validateRegistration({
      student_id: effectiveStudentId.value,
      academic_term_id: termId.value,
      course_ids: selectedCourseIds.value,
    });
    validationResult.value = data;
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    validating.value = false;
  }
}

async function submit() {
  submitting.value = true;
  error.value = "";
  try {
    const { data } = await registrationsApi.submitRegistration({
      student_id: effectiveStudentId.value,
      academic_term_id: termId.value,
      course_ids: selectedCourseIds.value,
    });
    submittedRegistrations.value = data;
    validationResult.value = null;
    selectedCourseIds.value = [];
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    submitting.value = false;
  }
}

const validStyle = { color: "#2f9e44", background: "#2f9e4418" };
const invalidStyle = { color: "#c92a2a", background: "#c92a2a18" };

onMounted(async () => {
  const { data } = await academicApi.listTerms();
  terms.value = data;
  termId.value = data.find((t) => t.is_active)?.id || data[0]?.id || null;

  if (auth.isStudent) {
    const { data: me } = await studentsApi.getStudent(auth.user.student_id);
    selectedStudent.value = me;
    loadCoursesForLevel(me.academic_level);
  }
});
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
.course-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.course-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
</style>
