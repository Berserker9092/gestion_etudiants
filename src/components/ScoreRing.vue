<script setup>
import { computed, ref, onMounted } from 'vue'
import { toNumber, mentionFor, toneVar } from '../utils/students'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  max: { type: Number, default: 20 },
  size: { type: Number, default: 120 },
  stroke: { type: Number, default: 10 },
  showMax: { type: Boolean, default: true }
})

const num = computed(() => toNumber(props.value) ?? 0)
const radius = computed(() => (props.size - props.stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const color = computed(() => toneVar(mentionFor(num.value).tone))

// L'anneau se remplit au montage : un seul mouvement, lié à l'apparition de la donnée
const ready = ref(false)
onMounted(() => requestAnimationFrame(() => { ready.value = true }))

const offset = computed(() => {
  const ratio = Math.min(1, Math.max(0, num.value / props.max))
  return circumference.value * (1 - (ready.value ? ratio : 0))
})
</script>

<template>
  <div class="ring" :style="{ width: `${size}px`, height: `${size}px` }" role="img" :aria-label="`${num.toFixed(2)} / ${max}`">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <circle class="track" :cx="size / 2" :cy="size / 2" :r="radius" :stroke-width="stroke" fill="none" />
      <circle
        class="value"
        :cx="size / 2" :cy="size / 2" :r="radius"
        :stroke-width="stroke" fill="none" stroke-linecap="round"
        :stroke="color"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
      />
    </svg>
    <div class="label">
      <strong :style="{ fontSize: `${size * 0.26}px` }">{{ num.toFixed(2) }}</strong>
      <small v-if="showMax" :style="{ fontSize: `${Math.max(11, size * 0.1)}px` }">/ {{ max }}</small>
    </div>
  </div>
</template>

<style scoped>
.ring { position: relative; flex: none; }
.track { stroke: var(--border); }
.value { transition: stroke-dashoffset 1s cubic-bezier(0.22, 1, 0.36, 1); }
.label {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  line-height: 1.05;
}
.label strong { font-family: var(--font-display); color: var(--ink); font-variant-numeric: tabular-nums; }
.label small { color: var(--muted); font-weight: 600; margin-top: 2px; }
</style>
