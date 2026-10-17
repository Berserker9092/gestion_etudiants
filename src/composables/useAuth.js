import { ref } from 'vue'

// -----------------------------------------------------------------------------
// SCAFFOLD D'AUTHENTIFICATION JWT
// -----------------------------------------------------------------------------
// Ce composable est prêt à être branché sur un backend FastAPI qui exposerait :
//   POST /api/auth/login   { username, password } -> { access_token }
//   GET  /api/auth/me       (header Authorization: Bearer <token>) -> { username, role }
//
// Tant que ces routes n'existent pas côté backend, l'authentification reste
// désactivée via VITE_AUTH_ENABLED=false dans le .env (voir router/index.js
// et services/api.js qui ajoutent déjà le header Authorization automatiquement
// dès qu'un token est présent).
// -----------------------------------------------------------------------------

const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED === 'true'
const TOKEN_KEY = 'gestion-etudiants-token'

const token = ref(localStorage.getItem(TOKEN_KEY) || null)
const user = ref(null)

export function useAuth() {
  const isAuthEnabled = AUTH_ENABLED
  const isAuthenticated = () => !AUTH_ENABLED || !!token.value

  function setToken(newToken) {
    token.value = newToken
    if (newToken) localStorage.setItem(TOKEN_KEY, newToken)
    else localStorage.removeItem(TOKEN_KEY)
  }

  async function login(username, password) {
    const base = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
    const res = await fetch(`${base}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Identifiants invalides.')
    }
    const data = await res.json()
    setToken(data.access_token)
    user.value = { username }
    return data
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return { token, user, isAuthEnabled, isAuthenticated, login, logout }
}
