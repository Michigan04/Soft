<template>
  <form @submit.prevent="submit">
    <div class="field">
      <label>Type</label>
      <select v-model="form.intervention_type" class="input" required>
        <option value="call">Call</option>
        <option value="email">Email</option>
        <option value="meeting">Meeting</option>
        <option value="academic_counselling">Academic Counselling</option>
        <option value="remedial_recommendation">Remedial Recommendation</option>
        <option value="other">Other</option>
      </select>
    </div>
    <div class="field">
      <label>Description</label>
      <textarea v-model="form.description" class="input" rows="3" required></textarea>
    </div>
    <div class="field">
      <label>Follow-up date (optional)</label>
      <input v-model="form.follow_up_date" type="date" class="input" />
    </div>
    <p v-if="error" class="field-error" style="margin-bottom: 10px">{{ error }}</p>
    <div class="flex gap-8" style="justify-content: flex-end">
      <button type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? "Saving..." : "Log Intervention" }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref } from "vue";
import * as interventionsApi from "@/api/interventions";
import { apiErrorMessage } from "@/api/client";

const props = defineProps({ studentId: { type: String, required: true } });
const emit = defineEmits(["created", "cancel"]);

const form = reactive({
  intervention_type: "call",
  description: "",
  follow_up_date: "",
});
const submitting = ref(false);
const error = ref("");

async function submit() {
  submitting.value = true;
  error.value = "";
  try {
    const { data } = await interventionsApi.createIntervention({
      student_id: props.studentId,
      intervention_type: form.intervention_type,
      description: form.description,
      follow_up_date: form.follow_up_date || null,
    });
    emit("created", data);
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    submitting.value = false;
  }
}
</script>
