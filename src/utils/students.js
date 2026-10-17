// Petites fonctions utilitaires autour des étudiants et de leurs notes (barème /20)

export function toNumber(value) {
  const n = parseFloat(value)
  return Number.isNaN(n) ? null : n
}

export function formatMoyenne(value, digits = 2) {
  const n = toNumber(value)
  return n === null ? '–' : n.toFixed(digits)
}

export function initials(nom = '', prenom = '') {
  const a = (prenom || '').trim().charAt(0)
  const b = (nom || '').trim().charAt(0)
  return `${a}${b}`.toUpperCase() || '?'
}

// Teinte stable (0-359) calculée à partir d'un texte : sert aux avatars
export function hueFromString(text = '') {
  let hash = 0
  for (let i = 0; i < text.length; i++) hash = (hash * 31 + text.charCodeAt(i)) % 360
  return hash
}

// Mentions du barème français : clé i18n + ton visuel
export function mentionFor(moyenne) {
  const n = toNumber(moyenne)
  if (n === null || n === 0) return { key: 'none', tone: 'muted' }
  if (n >= 16) return { key: 'excellent', tone: 'success' }
  if (n >= 14) return { key: 'good', tone: 'success' }
  if (n >= 12) return { key: 'fair', tone: 'info' }
  if (n >= 10) return { key: 'pass', tone: 'warning' }
  return { key: 'fail', tone: 'danger' }
}

export function toneVar(tone) {
  return `var(--${tone === 'muted' ? 'muted' : tone})`
}

// Les dates arrivent en "YYYY-MM-DD" (base) ou "DD/MM/YYYY" (JSON)
export function parseBirthDate(value) {
  if (!value || value === 'None') return null
  let y, m, d
  if (/^\d{4}-\d{2}-\d{2}/.test(value)) [y, m, d] = value.slice(0, 10).split('-').map(Number)
  else if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) [d, m, y] = value.split('/').map(Number)
  else return null
  const date = new Date(y, m - 1, d)
  return Number.isNaN(date.getTime()) ? null : date
}

export function ageFrom(date) {
  if (!date) return null
  const now = new Date()
  let age = now.getFullYear() - date.getFullYear()
  const birthdayPassed =
    now.getMonth() > date.getMonth() ||
    (now.getMonth() === date.getMonth() && now.getDate() >= date.getDate())
  if (!birthdayPassed) age--
  return age
}

// Même formule que le backend : (moyenne des devoirs + 2 × examen) / 3
export function moyenneMatiere(devoirs, examen) {
  const list = (devoirs || []).filter(v => typeof v === 'number' && !Number.isNaN(v))
  const moyDevoirs = list.length ? list.reduce((s, v) => s + v, 0) / list.length : 0
  return Math.round(((moyDevoirs + 2 * (toNumber(examen) || 0)) / 3) * 100) / 100
}

export function parseDevoirs(text) {
  return String(text || '')
    .split(',')
    .map(v => parseFloat(v.trim()))
    .filter(v => !Number.isNaN(v))
}
