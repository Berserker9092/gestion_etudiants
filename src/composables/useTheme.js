import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'gestion-etudiants-theme'
const theme = ref(localStorage.getItem(STORAGE_KEY) || 'light')

watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem(STORAGE_KEY, theme.value)
})

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }
  return { theme, toggleTheme }
}
