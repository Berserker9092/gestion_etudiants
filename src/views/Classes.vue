<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { toNumber, mentionFor, toneVar } from '../utils/students'
import ScoreRing from '../components/ScoreRing.vue'
import StudentAvatar from '../components/StudentAvatar.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const loading = ref(true)
const students = ref([])
const sortBy = ref('name')

async function charger() {
  loading.value = true
  try {
    const res = await api.getEtudiants({ size: 1000 })
    students.value = res.data || []
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    loading.value = false
  }
}

const classes = computed(() => {
  const map = {}
  students.value.forEach(s => {
    const key = s.classe || '—'
    if (!map[key]) map[key] = { name: key, students: [] }
    map[key].students.push(s)
  })
  const list = Object.values(map).map(c => {
    const noted = c.students.filter(s => (toNumber(s.moyenne_generale) || 0) > 0)
    const avg = noted.length ? noted.reduce((sum, s) => sum + Number(s.moyenne_generale), 0) / noted.length : 0
    const passed = noted.filter(s => s.moyenne_generale >= 10).length
    const best = [...noted].sort((a, b) => b.moyenne_generale - a.moyenne_generale)[0] || null
    return {
      name: c.name,
      count: c.students.length,
      avg,
      rate: noted.length ? (passed / noted.length) * 100 : 0,
      best
    }
  })
  const sorters = {
    name: (a, b) => a.name.localeCompare(b.name),
    avg: (a, b) => b.avg - a.avg,
    count: (a, b) => b.count - a.count
  }
  return list.sort(sorters[sortBy.value])
})

function ouvrirClasse(name) { router.push({ name: 'liste', query: { classe: name } }) }
function ouvrirFiche(s) { router.push({ name: 'fiche', params: { numero: s.numero } }) }

onMounted(charger)
</script>

<template>
  <div class="container">
    <header class="page-head">
      <div>
        <h1>{{ t('classes.title') }}</h1>
        <p>{{ t('classes.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <div class="seg" role="group" :aria-label="t('classes.sort')">
          <button :class="{ on: sortBy === 'name' }" @click="sortBy = 'name'">{{ t('classes.sortName') }}</button>
          <button :class="{ on: sortBy === 'avg' }" @click="sortBy = 'avg'">{{ t('classes.sortAverage') }}</button>
          <button :class="{ on: sortBy === 'count' }" @click="sortBy = 'count'">{{ t('classes.sortSize') }}</button>
        </div>
      </div>
    </header>

    <div v-if="loading" class="grid">
      <div v-for="n in 6" :key="n" class="skeleton" style="height: 230px; border-radius: 14px;"></div>
    </div>

    <div v-else-if="!classes.length" class="card">
      <EmptyState icon="fa-school" :title="t('classes.emptyTitle')" :text="t('classes.emptyText')" />
    </div>

    <div v-else class="grid">
      <article v-for="c in classes" :key="c.name" class="card class-card">
        <header class="cc-head">
          <div>
            <h2>{{ c.name }}</h2>
            <span class="muted num">{{ t('classes.students', c.count) }}</span>
          </div>
          <ScoreRing :value="c.avg" :size="76" :stroke="8" :show-max="false" />
        </header>

        <div class="rate">
          <div class="rate-top">
            <span>{{ t('classes.successRate') }}</span>
            <strong class="num">{{ c.rate.toFixed(0) }} %</strong>
          </div>
          <span class="bar"><span :style="{ width: `${c.rate}%`, background: toneVar(c.rate >= 50 ? 'success' : 'danger') }"></span></span>
        </div>

        <button v-if="c.best" class="best" @click="ouvrirFiche(c.best)">
          <StudentAvatar :nom="c.best.nom" :prenom="c.best.prenom" :size="32" />
          <span>
            <small>{{ t('classes.best') }}</small>
            <strong>{{ c.best.prenom }} {{ c.best.nom }}</strong>
          </span>
          <b class="num" :style="{ color: toneVar(mentionFor(c.best.moyenne_generale).tone) }">{{ Number(c.best.moyenne_generale).toFixed(2) }}</b>
        </button>

        <button class="btn-muted open" @click="ouvrirClasse(c.name)">
          {{ t('classes.open') }} <i class="fa-solid fa-arrow-right"></i>
        </button>
      </article>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 18px; }
.class-card { padding: 22px; display: flex; flex-direction: column; gap: 18px; }
.cc-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.cc-head h2 { margin: 0; font-size: 26px; }
.muted { color: var(--muted); font-size: 13px; }

.rate-top { display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); margin-bottom: 8px; }
.rate-top strong { color: var(--ink); }
.rate .bar { height: 8px; }

.best {
  width: 100%; background: var(--surface-2); border: 1px solid var(--border); color: var(--text);
  padding: 10px 12px; border-radius: 12px; gap: 12px; text-align: left;
}
.best:hover { border-color: var(--primary); }
.best span { display: flex; flex-direction: column; line-height: 1.25; flex: 1; min-width: 0; }
.best small { color: var(--muted); font-size: 12px; font-weight: 500; }
.best strong { color: var(--ink); font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.open { justify-content: center; margin-top: auto; }

.seg { display: inline-flex; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: var(--card-bg); }
.seg button { background: transparent; color: var(--muted); border-radius: 0; padding: 8px 14px; font-size: 13px; }
.seg button.on { background: var(--primary-soft); color: var(--primary); }
</style>
