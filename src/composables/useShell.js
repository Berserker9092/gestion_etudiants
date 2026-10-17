import { ref } from 'vue'

// État partagé de la coque d'application : menu latéral et palette de recherche
const sidebarCollapsed = ref(localStorage.getItem('gestion-etudiants-sidebar') === '1')
const mobileOpen = ref(false)
const paletteOpen = ref(false)

export function useShell() {
  function toggleCollapse() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('gestion-etudiants-sidebar', sidebarCollapsed.value ? '1' : '0')
  }
  return {
    sidebarCollapsed,
    mobileOpen,
    paletteOpen,
    toggleCollapse,
    openMobile: () => { mobileOpen.value = true },
    closeMobile: () => { mobileOpen.value = false },
    openPalette: () => { paletteOpen.value = true },
    closePalette: () => { paletteOpen.value = false }
  }
}
