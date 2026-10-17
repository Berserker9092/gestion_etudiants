<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  decimals: { type: Number, default: 0 },
  duration: { type: Number, default: 900 }
})

const display = ref(0)
let frame = null

function animate(from, to) {
  cancelAnimationFrame(frame)
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    display.value = to
    return
  }
  const start = performance.now()
  const step = now => {
    const t = Math.min(1, (now - start) / props.duration)
    const eased = 1 - Math.pow(1 - t, 3)
    display.value = from + (to - from) * eased
    if (t < 1) frame = requestAnimationFrame(step)
  }
  frame = requestAnimationFrame(step)
}

onMounted(() => animate(0, props.value))
watch(() => props.value, (to, from) => animate(from || 0, to))
</script>

<template>
  <span class="num">{{ display.toFixed(decimals) }}</span>
</template>
