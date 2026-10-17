import { reactive, ref } from 'vue'
import { api } from '../services/api'

// Cache partagé des indicateurs (sidebar, accueil...) pour éviter de multiplier les appels
const stats = ref(null)
const loading = ref(false)
const lastFetch = ref(0)

const indicateurs = reactive({ total: 0, db: 0, json: 0, archives: 0 })

export function useStats() {
  async function loadStats(force = false) {
    if (loading.value) return stats.value
    if (!force && Date.now() - lastFetch.value < 4000) return stats.value
    loading.value = true
    try {
      const data = await api.getStatistiques()
      stats.value = data
      const ind = data.indicateurs || {}
      indicateurs.total = ind.total_global ?? 0
      indicateurs.db = ind.total_db ?? 0
      indicateurs.json = ind.total_json ?? 0
      indicateurs.archives = ind.total_archives ?? 0
      lastFetch.value = Date.now()
    } catch (e) {
      /* l'interface reste utilisable sans les indicateurs */
    } finally {
      loading.value = false
    }
    return stats.value
  }

  return { stats, indicateurs, loading, loadStats }
}
