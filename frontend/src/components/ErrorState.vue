<template>
  <div class="state-box">
    <h3>Something went wrong</h3>
    <p>{{ message }}</p>
    <button v-if="retry" class="btn btn-secondary" @click="$emit('retry')">Try again</button>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: "We could not load this data. Please try again." },
  retry: { type: Boolean, default: true },
});
defineEmits(["retry"]);
</script>
