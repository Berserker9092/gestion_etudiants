<script setup>
defineProps({
  icon: { type: String, default: 'fa-user-graduate' },
  title: { type: String, required: true },
  text: { type: String, default: '' }
})
</script>

<template>
  <div class="empty">
    <i class="fa-solid" :class="icon"></i>
    <h3>{{ title }}</h3>
    <p v-if="text">{{ text }}</p>
    <slot />
  </div>
</template>
