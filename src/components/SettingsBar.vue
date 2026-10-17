<script setup>
import { useI18n } from 'vue-i18n'
import { useTheme } from '../composables/useTheme'
import { setLocale } from '../i18n'

const { theme, toggleTheme } = useTheme()
const { locale, t } = useI18n()

function switchLocale() {
  setLocale(locale.value === 'fr' ? 'en' : 'fr')
}
</script>

<template>
  <div class="settings-bar">
    <button class="settings-btn" :aria-label="t('theme.toggle')" :title="t('theme.toggle')" @click="toggleTheme">
      <i class="fa-solid" :class="theme === 'light' ? 'fa-moon' : 'fa-sun'"></i>
    </button>
    <button class="settings-btn lang" aria-label="Français / English" title="Français / English" @click="switchLocale">
      {{ locale.toUpperCase() }}
    </button>
  </div>
</template>

<style scoped>
.settings-bar { display: flex; gap: 6px; }
.settings-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  width: 40px;
  height: 40px;
  border-radius: 10px;
  justify-content: center;
  padding: 0;
  font-size: 14px;
}
.settings-btn:hover { background: var(--hover); color: var(--ink); }
.lang { font-size: 12.5px; letter-spacing: 0.03em; }
</style>
