<template>
  <div class="flex items-center justify-between pagination">
    <span class="text-muted text-sm">Page {{ page }} of {{ pages || 1 }} ({{ total }} total)</span>
    <div class="flex gap-8">
      <button class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
        Previous
      </button>
      <button class="btn btn-secondary btn-sm" :disabled="page >= pages" @click="$emit('update:page', page + 1)">
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, required: true },
  pages: { type: Number, required: true },
  total: { type: Number, required: true },
});
defineEmits(["update:page"]);
</script>

<style scoped>
.pagination {
  padding: 14px 4px 4px;
}
</style>
