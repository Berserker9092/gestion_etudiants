<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useShell } from '../composables/useShell'
import SettingsBar from './SettingsBar.vue'

const route = useRoute()
const { t } = useI18n()
const { openMobile, openPalette } = useShell()

const section = computed(() => (route.meta.sectionKey ? t(route.meta.sectionKey) : ''))
const title = computed(() => (route.meta.titleKey ? t(route.meta.titleKey) : ''))
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
</script>

<template>
  <header class="topbar">
    <button class="menu-btn" :aria-label="t('nav.openMenu')" @click="openMobile">
      <i class="fa-solid fa-bars"></i>
    </button>

    <nav class="crumbs" :aria-label="t('nav.breadcrumb')">
      <template v-if="section">
        <span class="crumb-section">{{ section }}</span>
        <i class="fa-solid fa-chevron-right sep"></i>
      </template>
      <strong>{{ title }}</strong>
    </nav>

    <button class="search-trigger" @click="openPalette">
      <i class="fa-solid fa-magnifying-glass"></i>
      <span class="search-text">{{ t('palette.trigger') }}</span>
      <kbd>{{ isMac ? '⌘' : 'Ctrl' }} K</kbd>
    </button>

    <router-link to="/ajouter" class="btn btn-primary new-btn">
      <i class="fa-solid fa-plus"></i> <span>{{ t('nav.newStudent') }}</span>
    </router-link>

    <SettingsBar />
  </header>
</template>

<style scoped>
.topbar {
  position: sticky; top: 0; z-index: 40;
  height: var(--topbar-h);
  display: flex; align-items: center; gap: 14px;
  padding: 0 32px;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}
.menu-btn { display: none; background: transparent; border: 1px solid var(--border); color: var(--text); width: 40px; height: 40px; padding: 0; justify-content: center; }
.crumbs { display: flex; align-items: center; gap: 10px; min-width: 0; margin-right: auto; font-size: 14px; }
.crumbs strong { color: var(--ink); font-family: var(--font-display); font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crumb-section { color: var(--muted); font-weight: 500; white-space: nowrap; }
.sep { font-size: 10px; color: var(--muted); }

.search-trigger {
  background: var(--card-bg); border: 1px solid var(--border); color: var(--muted);
  min-width: 280px; padding: 9px 12px; font-weight: 500;
}
.search-trigger:hover { border-color: var(--primary); color: var(--text); }
.search-text { flex: 1; text-align: left; }
kbd {
  font-family: inherit; font-size: 11.5px; font-weight: 700; color: var(--muted);
  background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 2px 6px;
}

@media (max-width: 1100px) { .search-trigger { min-width: 0; } .search-text, kbd { display: none; } .search-trigger { width: 40px; height: 40px; padding: 0; justify-content: center; } }
@media (max-width: 960px) {
  .topbar { padding: 0 16px; }
  .menu-btn { display: inline-flex; }
  .new-btn span { display: none; }
  .new-btn { width: 40px; height: 40px; padding: 0; justify-content: center; }
}
</style>
