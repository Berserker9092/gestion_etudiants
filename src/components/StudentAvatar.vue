<script setup>
import { computed } from 'vue'
import { initials, hueFromString } from '../utils/students'

const props = defineProps({
  nom: { type: String, default: '' },
  prenom: { type: String, default: '' },
  size: { type: Number, default: 36 }
})

const label = computed(() => initials(props.nom, props.prenom))
const hue = computed(() => hueFromString(`${props.prenom} ${props.nom}`))
</script>

<template>
  <span
    class="avatar"
    :style="{ '--h': hue, width: `${size}px`, height: `${size}px`, fontSize: `${Math.round(size * 0.38)}px` }"
    aria-hidden="true"
  >{{ label }}</span>
</template>

<style scoped>
.avatar {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.02em;
  background: hsl(var(--h) 55% 90%);
  color: hsl(var(--h) 55% 26%);
}
[data-theme="dark"] .avatar {
  background: hsl(var(--h) 35% 24%);
  color: hsl(var(--h) 70% 85%);
}
</style>
