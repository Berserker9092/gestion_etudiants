<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { mentionFor } from '../utils/students'

const props = defineProps({ moyenne: { type: [Number, String], default: 0 } })
const { t } = useI18n()
const mention = computed(() => mentionFor(props.moyenne))
</script>

<template>
  <span :class="['pill', mention.tone]">{{ t(`mention.${mention.key}`) }}</span>
</template>
