<script setup>
defineProps({
  columns: { type: Number, default: 6 },
  rows: { type: Number, default: 5 }
})
</script>

<template>
  <tr v-for="r in rows" :key="r">
    <td v-for="c in columns" :key="c">
      <div class="skeleton skeleton-text" :style="{ width: `${50 + ((c * 13) % 40)}%` }"></div>
    </td>
  </tr>
</template>
