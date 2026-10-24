<template>
  <div class="state-box">
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: "Nothing here yet" },
  message: { type: String, default: "There is no data to show." },
});
</script>
