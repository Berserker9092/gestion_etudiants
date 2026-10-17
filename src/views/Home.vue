<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useStats } from '../composables/useStats'
import { STACK, GITHUB_URL, APP_NAME } from '../config'
import { toNumber, mentionFor, toneVar } from '../utils/students'
import StudentAvatar from '../components/StudentAvatar.vue'
import ScoreRing from '../components/ScoreRing.vue'
import AnimatedNumber from '../components/AnimatedNumber.vue'
import MentionPill from '../components/MentionPill.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const { indicateurs, loadStats } = useStats()

const loading = ref(true)
const students = ref([])
const search = ref('')

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return t('home.greetMorning')
  if (h < 18) return t('home.greetAfternoon')
  return t('home.greetEvening')
})

async function charger() {
  loading.value = true
  try {
    const [, res] = await Promise.all([loadStats(true), api.getEtudiants({ size: 1000 })])
    students.value = res.data || []
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    loading.value = false
  }
}

// Étudiants dont la moyenne est exploitable (une moyenne à 0 signifie « pas encore de notes »)
const noted = computed(() => students.value.filter(s => (toNumber(s.moyenne_generale) || 0) > 0))
const ranked = computed(() => [...noted.value].sort((a, b) => b.moyenne_generale - a.moyenne_generale))
const top = computed(() => ranked.value.slice(0, 5))
const major = computed(() => ranked.value[0] || null)
const toSupport = computed(() => [...ranked.value].reverse().filter(s => s.moyenne_generale < 10).slice(0, 4))

const averageAll = computed(() =>
  noted.value.length ? noted.value.reduce((sum, s) => sum + Number(s.moyenne_generale), 0) / noted.value.length : 0
)
const successRate = computed(() =>
  noted.value.length ? (noted.value.filter(s => s.moyenne_generale >= 10).length / noted.value.length) * 100 : 0
)

const classes = computed(() => {
  const map = {}
  students.value.forEach(s => {
    const key = s.classe || '—'
    if (!map[key]) map[key] = { name: key, count: 0, sum: 0, noted: 0 }
    map[key].count++
    const m = toNumber(s.moyenne_generale) || 0
    if (m > 0) { map[key].sum += m; map[key].noted++ }
  })
  return Object.values(map)
    .map(c => ({ ...c, avg: c.noted ? c.sum / c.noted : 0 }))
    .sort((a, b) => a.name.localeCompare(b.name))
})
const maxCount = computed(() => Math.max(1, ...classes.value.map(c => c.count)))

const kpis = computed(() => [
  { key: 'students', icon: 'fa-users', tone: 'primary', value: students.value.length, decimals: 0, sub: t('home.kpiStudentsSub', { db: indicateurs.db, json: indicateurs.json }) },
  { key: 'average', icon: 'fa-graduation-cap', tone: 'info', value: averageAll.value, decimals: 2, suffix: '/ 20', sub: t('home.kpiAverageSub', { n: noted.value.length }) },
  { key: 'success', icon: 'fa-circle-check', tone: 'success', value: successRate.value, decimals: 1, suffix: '%', sub: t('home.kpiSuccessSub') },
  { key: 'archived', icon: 'fa-box-archive', tone: 'warning', value: indicateurs.archives, decimals: 0, sub: t('home.kpiArchivedSub') }
])

const shortcuts = computed(() => [
  { to: '/ajouter', icon: 'fa-user-plus', tone: 'primary', title: t('home.actionAdd'), text: t('home.actionAddText') },
  { to: { name: 'liste', query: { source: 'JSON' } }, icon: 'fa-file-import', tone: 'info', title: t('home.actionImport'), text: t('home.actionImportText') },
  { to: '/dashboard', icon: 'fa-chart-pie', tone: 'purple', title: t('home.actionAnalytics'), text: t('home.actionAnalyticsText') },
  { to: '/archive', icon: 'fa-box-archive', tone: 'warning', title: t('home.actionArchive'), text: t('home.actionArchiveText') }
])

function lancerRecherche() {
  const q = search.value.trim()
  router.push({ name: 'liste', query: q ? { q } : {} })
}
function ouvrirFiche(s) { router.push({ name: 'fiche', params: { numero: s.numero } }) }
function ouvrirClasse(name) { router.push({ name: 'liste', query: { classe: name } }) }

onMounted(charger)
</script>

<template>
  <div class="container home">
    <!-- Bandeau principal -->
    <section class="hero">
      <div class="hero-copy">
        <h1>{{ greeting }}, {{ t('nav.admin') }}</h1>
        <p class="lead">
          <template v-if="!loading">{{ t('home.lead', { students: students.length, classes: classes.length }) }}</template>
          <template v-else>{{ t('home.leadLoading') }}</template>
        </p>

        <form class="hero-search" role="search" @submit.prevent="lancerRecherche">
          <i class="fa-solid fa-magnifying-glass"></i>
          <input v-model="search" type="text" :placeholder="t('home.searchPlaceholder')" :aria-label="t('home.searchPlaceholder')">
          <button type="submit" class="btn-accent">{{ t('common.search') }}</button>
        </form>

        <div class="hero-links">
          <router-link to="/etudiants" class="hero-link"><i class="fa-solid fa-users"></i> {{ t('nav.registry') }}</router-link>
          <router-link to="/classes" class="hero-link"><i class="fa-solid fa-school"></i> {{ t('nav.classes') }}</router-link>
          <router-link to="/dashboard" class="hero-link"><i class="fa-solid fa-chart-pie"></i> {{ t('nav.analytics') }}</router-link>
        </div>
      </div>

      <button v-if="major" class="major" @click="ouvrirFiche(major)">
        <span class="major-title">{{ t('home.topAverage') }}</span>
        <span class="major-body">
          <ScoreRing :value="major.moyenne_generale" :size="104" :stroke="9" />
          <span class="major-id">
            <StudentAvatar :nom="major.nom" :prenom="major.prenom" :size="40" />
            <strong>{{ major.prenom }} {{ major.nom }}</strong>
            <small>{{ major.classe }}</small>
            <MentionPill :moyenne="major.moyenne_generale" />
          </span>
        </span>
        <span class="major-cta">{{ t('palette.openFile') }} <i class="fa-solid fa-arrow-right"></i></span>
      </button>
      <div v-else-if="loading" class="major major-skeleton"><div class="skeleton" style="height:100%"></div></div>
    </section>

    <!-- Indicateurs -->
    <section class="kpis" :aria-label="t('home.kpiLabel')">
      <article v-for="k in kpis" :key="k.key" class="card kpi">
        <span class="kpi-icon" :class="k.tone"><i class="fa-solid" :class="k.icon"></i></span>
        <div class="kpi-body">
          <h3>{{ t(`home.kpi_${k.key}`) }}</h3>
          <p v-if="!loading" class="kpi-value">
            <AnimatedNumber :value="k.value" :decimals="k.decimals" /><small v-if="k.suffix"> {{ k.suffix }}</small>
          </p>
          <div v-else class="skeleton skeleton-kpi"></div>
          <span class="kpi-sub">{{ loading ? '' : k.sub }}</span>
        </div>
      </article>
    </section>

    <EmptyState
      v-if="!loading && !students.length"
      :title="t('home.emptyTitle')" :text="t('home.emptyText')"
    >
      <router-link to="/ajouter" class="btn btn-primary"><i class="fa-solid fa-user-plus"></i> {{ t('nav.newStudent') }}</router-link>
    </EmptyState>

    <template v-else>
      <div class="grid-2">
        <!-- Meilleurs résultats -->
        <section class="card">
          <header class="card-head">
            <div>
              <h2>{{ t('home.bestResults') }}</h2>
              <p class="card-sub">{{ t('home.bestResultsSub') }}</p>
            </div>
            <router-link to="/etudiants" class="btn btn-ghost btn-sm">{{ t('home.seeAll') }}</router-link>
          </header>
          <ol class="ranking">
            <template v-if="loading">
              <li v-for="n in 5" :key="n"><div class="skeleton" style="height:44px;width:100%"></div></li>
            </template>
            <template v-else>
            <li v-for="(s, i) in top" :key="s.numero">
              <button class="rank-row" @click="ouvrirFiche(s)">
                <span class="rank-pos num">{{ i + 1 }}</span>
                <StudentAvatar :nom="s.nom" :prenom="s.prenom" :size="38" />
                <span class="rank-id">
                  <strong>{{ s.prenom }} {{ s.nom }}</strong>
                  <small>{{ s.classe }}</small>
                </span>
                <span class="rank-score">
                  <span class="bar"><span :style="{ width: `${(s.moyenne_generale / 20) * 100}%`, background: toneVar(mentionFor(s.moyenne_generale).tone) }"></span></span>
                  <strong class="num">{{ Number(s.moyenne_generale).toFixed(2) }}</strong>
                </span>
                <MentionPill class="rank-mention" :moyenne="s.moyenne_generale" />
              </button>
            </li>
            </template>
          </ol>
        </section>

        <!-- Répartition par classe -->
        <section class="card">
          <header class="card-head">
            <div>
              <h2>{{ t('home.byClass') }}</h2>
              <p class="card-sub">{{ t('home.byClassSub') }}</p>
            </div>
            <router-link to="/classes" class="btn btn-ghost btn-sm">{{ t('home.details') }}</router-link>
          </header>
          <ul class="class-list">
            <template v-if="loading">
              <li v-for="n in 6" :key="n"><div class="skeleton" style="height:34px;width:100%"></div></li>
            </template>
            <template v-else>
            <li v-for="c in classes" :key="c.name">
              <button class="class-row" @click="ouvrirClasse(c.name)">
                <span class="class-name">{{ c.name }}</span>
                <span class="bar class-bar"><span :style="{ width: `${(c.count / maxCount) * 100}%`, background: 'var(--primary)' }"></span></span>
                <span class="class-count num">{{ c.count }}</span>
                <span class="class-avg num" :style="{ color: toneVar(mentionFor(c.avg).tone) }">{{ c.avg ? c.avg.toFixed(2) : '–' }}</span>
              </button>
            </li>
            </template>
          </ul>
          <p class="legend">{{ t('home.classLegend') }}</p>
        </section>
      </div>

      <div class="grid-2 second">
        <!-- À accompagner -->
        <section class="card">
          <header class="card-head">
            <div>
              <h2>{{ t('home.toSupport') }}</h2>
              <p class="card-sub">{{ t('home.toSupportSub') }}</p>
            </div>
          </header>
          <ul class="support-list">
            <li v-if="!loading && !toSupport.length" class="all-good">
              <i class="fa-solid fa-circle-check"></i> {{ t('home.allGood') }}
            </li>
            <li v-for="s in toSupport" :key="s.numero">
              <button class="rank-row" @click="ouvrirFiche(s)">
                <StudentAvatar :nom="s.nom" :prenom="s.prenom" :size="38" />
                <span class="rank-id">
                  <strong>{{ s.prenom }} {{ s.nom }}</strong>
                  <small>{{ s.classe }}</small>
                </span>
                <span class="rank-score"><strong class="num" style="color: var(--danger)">{{ Number(s.moyenne_generale).toFixed(2) }}</strong></span>
                <MentionPill class="rank-mention" :moyenne="s.moyenne_generale" />
              </button>
            </li>
          </ul>
        </section>

        <!-- Actions rapides -->
        <section class="card card-pad">
          <h2 class="actions-title">{{ t('home.quickActions') }}</h2>
          <div class="shortcuts">
            <router-link v-for="a in shortcuts" :key="a.title" :to="a.to" class="shortcut">
              <span class="kpi-icon" :class="a.tone"><i class="fa-solid" :class="a.icon"></i></span>
              <strong>{{ a.title }}</strong>
              <small>{{ a.text }}</small>
            </router-link>
          </div>
        </section>
      </div>
    </template>

    <footer class="about">
      <p>{{ t('home.about', { name: APP_NAME }) }}</p>
      <div class="stack">
        <span v-for="s in STACK" :key="s" class="chip">{{ s }}</span>
        <a :href="GITHUB_URL" target="_blank" rel="noopener" class="chip gh"><i class="fa-brands fa-github"></i> GitHub</a>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.home { display: flex; flex-direction: column; gap: 20px; }

/* ----- Bandeau : papier réglé de registre, marge safran ----- */
.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.8fr);
  gap: 32px;
  align-items: center;
  padding: 40px 40px 40px 64px;
  border-radius: 20px;
  color: #d3e6e7;
  background-color: #0c3a40;
  background-image: repeating-linear-gradient(to bottom, transparent 0 35px, rgba(255, 255, 255, 0.045) 35px 36px);
  overflow: hidden;
}
[data-theme="dark"] .hero { background-color: #0a2a2f; }
.hero::before {
  content: ""; position: absolute; left: 36px; top: 0; bottom: 0; width: 2px;
  background: var(--accent); opacity: 0.85;
}
.hero-copy { position: relative; }
.hero h1 { color: #fff; font-size: clamp(28px, 3.4vw, 40px); margin-bottom: 10px; }
.lead { margin: 0 0 26px; font-size: 16px; max-width: 52ch; color: #b4cfd1; }

.hero-search {
  display: flex; align-items: center; gap: 8px; max-width: 560px;
  background: var(--card-bg); border-radius: 14px; padding: 6px 6px 6px 16px;
  box-shadow: 0 12px 28px -12px rgba(0, 0, 0, 0.5);
}
.hero-search i { color: var(--muted); }
.hero-search input {
  flex: 1; min-width: 0; border: none; outline: none; background: transparent;
  font-family: inherit; font-size: 15px; color: var(--ink); padding: 10px 4px;
}
.hero-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.hero-link {
  display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px; border-radius: 999px;
  color: #d3e6e7; font-weight: 600; font-size: 13px; text-decoration: none;
  border: 1px solid rgba(255, 255, 255, 0.18); transition: background-color 0.15s ease;
}
.hero-link:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }

.major {
  position: relative; display: flex; flex-direction: column; gap: 14px; text-align: left;
  background: var(--card-bg); color: var(--text); border: none; border-radius: 18px;
  padding: 22px; box-shadow: 0 24px 40px -18px rgba(0, 0, 0, 0.55);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.major:hover { transform: translateY(-3px); box-shadow: 0 30px 46px -18px rgba(0, 0, 0, 0.6); }
.major-title { font-family: var(--font-display); font-weight: 600; font-size: 15px; color: var(--ink); }
.major-body { display: flex; align-items: center; gap: 18px; }
.major-id { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; min-width: 0; }
.major-id strong { color: var(--ink); font-size: 15px; line-height: 1.25; }
.major-id small { color: var(--muted); font-size: 13px; }
.major-cta { font-size: 13px; font-weight: 700; color: var(--primary); }
.major-skeleton { min-height: 200px; padding: 0; overflow: hidden; }

/* ----- Indicateurs ----- */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }
.kpi { display: flex; gap: 14px; padding: 18px 20px; align-items: flex-start; }
.kpi-icon {
  flex: none; width: 42px; height: 42px; border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center; font-size: 17px;
}
.kpi-icon.primary { background: var(--primary-soft); color: var(--primary); }
.kpi-icon.info { background: var(--info-soft); color: var(--info); }
.kpi-icon.success { background: var(--success-soft); color: var(--success); }
.kpi-icon.warning { background: var(--warning-soft); color: var(--warning); }
.kpi-icon.purple { background: var(--purple-soft); color: var(--purple); }
.kpi-body { min-width: 0; }
.kpi-body h3 { margin: 0; font-family: var(--font-body); font-size: 13px; font-weight: 600; color: var(--muted); }
.kpi-value { margin: 4px 0 2px; font-family: var(--font-display); font-size: 30px; font-weight: 700; color: var(--ink); line-height: 1.1; }
.kpi-value small { font-size: 14px; font-weight: 600; color: var(--muted); font-family: var(--font-body); }
.kpi-sub { font-size: 12.5px; color: var(--muted); }
.kpi .skeleton-kpi { margin: 8px 0 6px; }

/* ----- Grilles ----- */
.grid-2 { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 20px; }
.grid-2.second { grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); }

.ranking, .support-list, .class-list { list-style: none; margin: 0; padding: 10px 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.rank-row {
  width: 100%; background: transparent; color: var(--text); text-align: left;
  padding: 9px 10px; border-radius: 12px; gap: 12px; font-weight: 500;
}
.rank-row:hover { background: var(--surface-2); }
.rank-pos { width: 22px; text-align: center; font-family: var(--font-display); font-weight: 700; color: var(--muted); }
.ranking li:first-child .rank-pos { color: var(--accent); }
.rank-id { display: flex; flex-direction: column; min-width: 0; flex: 1; line-height: 1.25; }
.rank-id strong { color: var(--ink); font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-id small { color: var(--muted); font-size: 12.5px; }
.rank-score { display: flex; align-items: center; gap: 10px; width: 150px; }
.rank-score .bar { flex: 1; }
.rank-score strong { color: var(--ink); min-width: 44px; text-align: right; }
.rank-mention { min-width: 88px; text-align: center; }

.class-row { width: 100%; background: transparent; color: var(--text); padding: 7px 10px; border-radius: 10px; gap: 12px; font-weight: 600; }
.class-row:hover { background: var(--surface-2); }
.class-name { width: 62px; text-align: left; color: var(--ink); }
.class-bar { flex: 1; height: 8px; }
.class-count { width: 28px; text-align: right; color: var(--muted); }
.class-avg { width: 46px; text-align: right; }
.legend { margin: 0; padding: 0 24px 18px; font-size: 12.5px; color: var(--muted); }

.all-good { display: flex; align-items: center; gap: 10px; padding: 18px 12px; color: var(--success); font-weight: 600; }

.actions-title { margin-bottom: 14px; }
.shortcuts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.shortcut {
  display: flex; flex-direction: column; gap: 4px; padding: 14px; border-radius: 14px;
  border: 1px solid var(--border); text-decoration: none; background: var(--surface-2);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}
.shortcut:hover { border-color: var(--primary); background: var(--card-bg); }
.shortcut .kpi-icon { margin-bottom: 8px; }
.shortcut strong { color: var(--ink); font-size: 14px; }
.shortcut small { color: var(--muted); font-size: 12.5px; line-height: 1.4; }

.about { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; padding: 6px 4px; color: var(--muted); font-size: 13px; }
.about p { margin: 0; }
.stack { display: flex; gap: 8px; flex-wrap: wrap; }
.chip.gh { text-decoration: none; }
.chip.gh:hover { border-color: var(--primary); color: var(--primary); }

@media (max-width: 1100px) {
  .hero { grid-template-columns: 1fr; padding: 32px 24px 32px 52px; }
  .hero::before { left: 26px; }
  .major { max-width: 420px; }
  .grid-2, .grid-2.second { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .rank-score { width: auto; }
  .rank-score .bar, .rank-mention { display: none; }
  .shortcuts { grid-template-columns: 1fr; }
}
</style>
