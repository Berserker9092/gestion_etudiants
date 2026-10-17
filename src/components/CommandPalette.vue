<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useShell } from '../composables/useShell'
import { debounce } from '../composables/useDebounce'
import StudentAvatar from './StudentAvatar.vue'

const router = useRouter()
const { t } = useI18n()
const { paletteOpen, closePalette } = useShell()

const query = ref('')
const results = ref([])
const loading = ref(false)
const active = ref(0)
const inputRef = ref(null)

const pages = computed(() => [
  { icon: 'fa-house', label: t('nav.home'), go: () => router.push('/') },
  { icon: 'fa-users', label: t('nav.registry'), go: () => router.push('/etudiants') },
  { icon: 'fa-school', label: t('nav.classes'), go: () => router.push('/classes') },
  { icon: 'fa-chart-pie', label: t('nav.analytics'), go: () => router.push('/dashboard') },
  { icon: 'fa-user-plus', label: t('nav.newStudent'), go: () => router.push('/ajouter') },
  { icon: 'fa-box-archive', label: t('nav.archives'), go: () => router.push('/archive') }
])

const q = computed(() => query.value.trim())
const matchingPages = computed(() =>
  q.value ? pages.value.filter(p => p.label.toLowerCase().includes(q.value.toLowerCase())) : pages.value
)

// Liste à plat pour la navigation clavier : étudiants d'abord, puis pages
const items = computed(() => [
  ...results.value.map(s => ({ type: 'student', student: s, go: () => router.push({ name: 'fiche', params: { numero: s.numero } }) })),
  ...matchingPages.value.map(p => ({ type: 'page', ...p }))
])

async function search() {
  if (q.value.length < 2) { results.value = []; loading.value = false; return }
  loading.value = true
  try {
    // Un texte contenant des chiffres ressemble à un matricule ou à un code
    const queries = /\d/.test(q.value)
      ? [{ numero: q.value }, { code: q.value }]
      : [{ nom_prenom: q.value }]
    const responses = await Promise.all(queries.map(p => api.getEtudiants({ ...p, size: 6 })))
    const merged = new Map()
    responses.forEach(r => (r.data || []).forEach(s => merged.set(s.numero, s)))
    results.value = [...merged.values()].slice(0, 6)
  } catch (e) {
    results.value = []
  } finally {
    loading.value = false
  }
}
const searchDebounced = debounce(search, 250)

watch(query, () => { active.value = 0; searchDebounced() })
watch(paletteOpen, async open => {
  if (open) {
    query.value = ''
    results.value = []
    active.value = 0
    await nextTick()
    inputRef.value?.focus()
  }
})

function choose(item) {
  if (!item) return
  closePalette()
  item.go()
}

function onKey(e) {
  if (e.key === 'ArrowDown') { e.preventDefault(); active.value = (active.value + 1) % Math.max(1, items.value.length) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); active.value = (active.value - 1 + items.value.length) % Math.max(1, items.value.length) }
  else if (e.key === 'Enter') { e.preventDefault(); choose(items.value[active.value]) }
  else if (e.key === 'Escape') { closePalette() }
}
</script>

<template>
  <Teleport to="body">
    <transition name="palette">
      <div v-if="paletteOpen" class="backdrop" @click.self="closePalette">
        <div class="panel" role="dialog" aria-modal="true" :aria-label="t('palette.trigger')" @keydown="onKey">
          <div class="input-row">
            <i class="fa-solid fa-magnifying-glass"></i>
            <input
              ref="inputRef" v-model="query" type="text" autocomplete="off" spellcheck="false"
              :placeholder="t('palette.placeholder')" :aria-label="t('palette.placeholder')"
            >
            <i v-if="loading" class="fa-solid fa-circle-notch fa-spin spin"></i>
            <kbd>Esc</kbd>
          </div>

          <div class="list">
            <template v-if="results.length">
              <p class="group">{{ t('palette.students') }}</p>
              <button
                v-for="(it, i) in items.filter(x => x.type === 'student')" :key="it.student.numero"
                class="row" :class="{ active: active === i }" @mouseenter="active = i" @click="choose(it)"
              >
                <StudentAvatar :nom="it.student.nom" :prenom="it.student.prenom" :size="34" />
                <span class="main">
                  <strong>{{ it.student.prenom }} {{ it.student.nom }}</strong>
                  <small>{{ it.student.classe }} · {{ it.student.numero }}</small>
                </span>
                <span class="hint">{{ t('palette.openFile') }}</span>
              </button>
            </template>
            <p v-else-if="q.length >= 2 && !loading" class="none">{{ t('palette.noStudent') }}</p>

            <template v-if="matchingPages.length">
              <p class="group">{{ t('palette.pages') }}</p>
              <button
                v-for="(it, j) in items.filter(x => x.type === 'page')" :key="it.label"
                class="row" :class="{ active: active === results.length + j }"
                @mouseenter="active = results.length + j" @click="choose(it)"
              >
                <span class="page-icon"><i class="fa-solid" :class="it.icon"></i></span>
                <span class="main"><strong>{{ it.label }}</strong></span>
              </button>
            </template>
          </div>

          <div class="foot">
            <span><kbd>↑</kbd><kbd>↓</kbd> {{ t('palette.navigate') }}</span>
            <span><kbd>Enter</kbd> {{ t('palette.open') }}</span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed; inset: 0; z-index: 3000;
  background: rgba(6, 28, 32, 0.5); backdrop-filter: blur(3px);
  display: flex; justify-content: center; align-items: flex-start; padding: 12vh 16px 16px;
}
.panel {
  width: 100%; max-width: 580px; background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 16px; box-shadow: var(--shadow-lg); overflow: hidden;
}
.input-row { display: flex; align-items: center; gap: 12px; padding: 16px 18px; border-bottom: 1px solid var(--border); color: var(--muted); }
.input-row input { flex: 1; border: none; outline: none; background: transparent; font-family: inherit; font-size: 16px; color: var(--ink); }
.spin { color: var(--primary); }
kbd {
  font-family: inherit; font-size: 11px; font-weight: 700; color: var(--muted);
  background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 2px 6px; margin-right: 4px;
}
.list { max-height: 52vh; overflow-y: auto; padding: 8px; }
.group { margin: 8px 10px 4px; font-size: 12.5px; font-weight: 700; color: var(--muted); }
.none { margin: 14px 10px; color: var(--muted); }
.row {
  width: 100%; background: transparent; color: var(--text); text-align: left;
  padding: 9px 10px; border-radius: 10px; gap: 12px; font-weight: 500;
}
.row.active { background: var(--primary-soft); }
.main { display: flex; flex-direction: column; min-width: 0; line-height: 1.25; }
.main strong { color: var(--ink); font-size: 14px; }
.main small { color: var(--muted); font-size: 12.5px; font-weight: 500; }
.hint { margin-left: auto; font-size: 12px; color: var(--primary); opacity: 0; font-weight: 600; }
.row.active .hint { opacity: 1; }
.page-icon { width: 34px; height: 34px; border-radius: 10px; background: var(--surface-2); border: 1px solid var(--border); display: inline-flex; align-items: center; justify-content: center; color: var(--primary); font-size: 14px; }
.foot { display: flex; gap: 18px; padding: 10px 18px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); background: var(--surface-2); }

.palette-enter-active, .palette-leave-active { transition: opacity 0.15s ease; }
.palette-enter-active .panel, .palette-leave-active .panel { transition: transform 0.15s ease; }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-from .panel, .palette-leave-to .panel { transform: translateY(-8px) scale(0.98); }
</style>
