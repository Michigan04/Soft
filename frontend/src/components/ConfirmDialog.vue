<template>
  <div v-if="modelValue" class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <h3 style="margin-bottom: 10px">{{ title }}</h3>
      <p class="text-muted" style="margin-bottom: 20px">{{ message }}</p>
      <div class="flex gap-8" style="justify-content: flex-end">
        <button class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
        <button class="btn" :class="danger ? 'btn-danger' : 'btn-primary'" @click="$emit('confirm')">
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "Are you sure?" },
  message: { type: String, default: "This action cannot be undone." },
  confirmLabel: { type: String, default: "Confirm" },
  danger: { type: Boolean, default: false },
});
defineEmits(["confirm", "cancel", "update:modelValue"]);
</script>
