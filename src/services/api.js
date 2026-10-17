const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const ETUDIANTS_URL = `${BASE_URL}/api/etudiants`
const STATS_URL = `${BASE_URL}/api/statistiques`
const TOKEN_KEY = 'gestion-etudiants-token'

// Si un token JWT est présent (scaffold auth, cf. composables/useAuth.js),
// il est automatiquement ajouté à chaque requête. Tant que le backend n'expose
// pas de routes /api/auth/*, aucun token n'est stocké et ce header reste vide.
function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function parseOrThrow(response) {
  if (!response.ok) {
    let detail = 'Une erreur est survenue.'
    try {
      const err = await response.json()
      detail = err.detail || detail
    } catch (_) { /* pas de corps JSON */ }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }
  return response.status === 204 ? null : response.json()
}

export const api = {
  // Liste paginée + filtres
  async getEtudiants(params = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== '' && v !== null && v !== undefined) query.append(k, v)
    })
    const res = await fetch(`${ETUDIANTS_URL}?${query.toString()}`, {
      headers: { ...authHeaders() }
    })
    return parseOrThrow(res)
  },

  // Fiche d'un étudiant : la route de liste filtre par "contient", on garde donc la correspondance exacte.
  // On cherche d'abord parmi les étudiants actifs, puis dans les archives.
  async getEtudiant(numero) {
    for (const uniquement_archives of [false, true]) {
      const result = await this.getEtudiants({ numero, size: 50, uniquement_archives })
      const found = (result.data || []).find(s => s.numero === numero)
      if (found) return found
    }
    return null
  },

  // Tous les étudiants d'une classe (sert au calcul du rang et de la moyenne de classe)
  async getEtudiantsParClasse(classe) {
    const result = await this.getEtudiants({ classe, size: 1000 })
    return result.data || []
  },

  async getStatistiques() {
    const res = await fetch(STATS_URL, { headers: { ...authHeaders() } })
    return parseOrThrow(res)
  },

  async ajouterEtudiant(payload) {
    const res = await fetch(`${ETUDIANTS_URL}/ajouter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload)
    })
    return parseOrThrow(res)
  },

  async modifierEtudiant(numero, payload) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload)
    })
    return parseOrThrow(res)
  },

  async supprimerEtudiant(numero) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}`, {
      method: 'DELETE',
      headers: { ...authHeaders() }
    })
    return parseOrThrow(res)
  },

  async archiverEtudiant(numero) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}/archiver`, {
      method: 'POST',
      headers: { ...authHeaders() }
    })
    return parseOrThrow(res)
  },

  async restaurerEtudiant(numero) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}/restaurer`, {
      method: 'POST',
      headers: { ...authHeaders() }
    })
    return parseOrThrow(res)
  },

  async importerSelection(numeros) {
    const res = await fetch(`${ETUDIANTS_URL}/importer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ numeros })
    })
    return parseOrThrow(res)
  },

  async getNotes(numero) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}/notes`, {
      headers: { ...authHeaders() }
    })
    return parseOrThrow(res)
  },

  async modifierNotes(numero, payload) {
    const res = await fetch(`${ETUDIANTS_URL}/${numero}/notes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload)
    })
    return parseOrThrow(res)
  }
}
