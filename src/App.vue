<script setup>
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import ToastContainer from './components/ToastContainer.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'
import CommandPalette from './components/CommandPalette.vue'
import { useShell } from './composables/useShell'

const route = useRoute()
const { sidebarCollapsed, paletteOpen, openPalette, closePalette } = useShell()

// Les pages publiques (connexion) s'affichent sans la coque de navigation
const withShell = computed(() => route.meta.layout !== 'blank')

function onGlobalKey(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (withShell.value) paletteOpen.value ? closePalette() : openPalette()
  }
}
onMounted(() => window.addEventListener('keydown', onGlobalKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKey))
</script>

<template>
  <div v-if="withShell" class="shell" :class="{ collapsed: sidebarCollapsed }">
    <AppSidebar />
    <div class="content">
      <AppTopbar />
      <main class="main">
        <router-view v-slot="{ Component, route: r }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="r.path" />
          </transition>
        </router-view>
      </main>
    </div>
    <CommandPalette />
  </div>

  <router-view v-else v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <ToastContainer />
  <ConfirmDialog />
</template>

<style scoped>
.content {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.22s ease;
}
.shell.collapsed .content { margin-left: var(--sidebar-w-collapsed); }
.main { flex: 1; padding: 28px 32px 56px; }

@media (max-width: 960px) {
  .content, .shell.collapsed .content { margin-left: 0; }
  .main { padding: 20px 16px 48px; }
}
</style>
