<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { debounce } from '../composables/useDebounce'
import { exportToExcel, exportToPdf } from '../utils/export'
import { toNumber, mentionFor, toneVar } from '../utils/students'
import SkeletonRows from '../components/SkeletonRows.vue'
import StudentAvatar from '../components/StudentAvatar.vue'
import MentionPill from '../components/MentionPill.vue'
import ScoreRing from '../components/ScoreRing.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const { confirmDialog } = useConfirm()

const etudiants = ref([])
const isLoading = ref(true)
const pageActuelle = ref(1)
const taillePage = ref(10)
const totalGlobalDonnees = ref(0)
const ligneEnEdition = ref(null)
const editBuffer = reactive({ nom: '', prenom: '', classe: '' })
const selectedNumeros = ref([])
const filtresAvances = ref(false)
const vue = ref(localStorage.getItem('gestion-etudiants-vue') || 'table')

const filtres = reactive({ numero: '', code: '', nomPrenom: '', classe: '', source: '' })
const tri = reactive({ colonne: null, direction: 'asc' })

const classesOptions = ['6emeA', '6emeB', '5emeA', '5emeB', '4emeA', '4emeB', '3emeA', '3emeB']

// Les filtres peuvent arriver par l'URL (accueil, page Classes...)
function appliquerQuery() {
  const q = route.query
  filtres.nomPrenom = q.q ? String(q.q) : ''
  filtres.classe = q.classe ? String(q.classe) : ''
  filtres.source = q.source ? String(q.source) : ''
  filtres.numero = ''
  filtres.code = ''
}

const filtresActifs = computed(() =>
  Object.values(filtres).some(v => String(v).trim() !== '')
)

async function chargerDonnees() {
  isLoading.value = true
  const params = { page: pageActuelle.value, size: taillePage.value }
  if (filtres.numero.trim()) params.numero = filtres.numero.trim()
  if (filtres.code.trim()) params.code = filtres.code.trim()
  if (filtres.nomPrenom.trim()) params.nom_prenom = filtres.nomPrenom.trim()
  if (filtres.classe) params.classe = filtres.classe
  if (filtres.source) params.source = filtres.source

  try {
    const result = await api.getEtudiants(params)
    etudiants.value = result.data || []
    await chargerIndicateurs()
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    isLoading.value = false
  }
}

async function chargerIndicateurs() {
  try {
    const stats = await api.getStatistiques()
    const ind = stats.indicateurs
    if (filtres.source === 'DB') totalGlobalDonnees.value = ind.total_db
    else if (filtres.source === 'JSON') totalGlobalDonnees.value = ind.total_json
    else totalGlobalDonnees.value = ind.total_db + ind.total_json
  } catch (e) { /* silencieux, comme l'original */ }
}

// Tri des colonnes (côté client, sur la page affichée)
const etudiantsTries = computed(() => {
  if (!tri.colonne) return etudiants.value
  const dir = tri.direction === 'asc' ? 1 : -1
  return [...etudiants.value].sort((a, b) => {
    let va = a[tri.colonne]
    let vb = b[tri.colonne]
    if (tri.colonne === 'moyenne_generale') {
      va = parseFloat(va) || -Infinity
      vb = parseFloat(vb) || -Infinity
    } else {
      va = (va || '').toString().toLowerCase()
      vb = (vb || '').toString().toLowerCase()
    }
    if (va < vb) return -1 * dir
    if (va > vb) return 1 * dir
    return 0
  })
})

function trierPar(colonne) {
  if (tri.colonne === colonne) tri.direction = tri.direction === 'asc' ? 'desc' : 'asc'
  else { tri.colonne = colonne; tri.direction = 'asc' }
}
const iconeTri = col => (tri.colonne === col && tri.direction === 'desc' ? 'fa-arrow-down' : 'fa-arrow-up')

// Pagination
const totalPages = computed(() => Math.ceil(totalGlobalDonnees.value / taillePage.value) || 1)
const pagesAffichees = computed(() => {
  const total = totalPages.value
  const current = pageActuelle.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = new Set([1, total, current, current - 1, current + 1])
  const sorted = [...pages].filter(p => p >= 1 && p <= total).sort((a, b) => a - b)
  const out = []
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) out.push('…')
    out.push(p)
  })
  return out
})
const precedentDesactive = computed(() => pageActuelle.value === 1)
const suivantDesactive = computed(() => pageActuelle.value >= totalPages.value || etudiants.value.length < taillePage.value)
const debutPage = computed(() => (etudiants.value.length ? (pageActuelle.value - 1) * taillePage.value + 1 : 0))
const finPage = computed(() => (pageActuelle.value - 1) * taillePage.value + etudiants.value.length)

function allerPage(page) {
  if (typeof page !== 'number') return
  pageActuelle.value = page
  chargerDonnees()
}
function pagePrecedente() { if (!precedentDesactive.value) allerPage(pageActuelle.value - 1) }
function pageSuivante() { if (!suivantDesactive.value) allerPage(pageActuelle.value + 1) }
function changerTaillePage() { pageActuelle.value = 1; chargerDonnees() }

// Recherche avec debounce : filtre automatiquement pendant la frappe
const chargerDonneesDebounce = debounce(() => { pageActuelle.value = 1; chargerDonnees() }, 450)
function onFiltreChange() { chargerDonneesDebounce() }

function reinitialiserFiltres() {
  Object.keys(filtres).forEach(k => { filtres[k] = '' })
  pageActuelle.value = 1
  chargerDonnees()
}

function changerVue(mode) {
  vue.value = mode
  localStorage.setItem('gestion-etudiants-vue', mode)
}

// Édition inline
function activerInline(student) {
  ligneEnEdition.value = student.numero
  editBuffer.nom = student.nom
  editBuffer.prenom = student.prenom
  editBuffer.classe = student.classe
}
function annulerInline() { ligneEnEdition.value = null }

async function sauvegarderInline(numero) {
  const nom = editBuffer.nom.trim()
  const prenom = editBuffer.prenom.trim()
  const classe = editBuffer.classe
  if (!nom || !prenom) { toast.warning(t('toast.requiredFields')); return }
  try {
    await api.modifierEtudiant(numero, { nom, prenom, classe })
    ligneEnEdition.value = null
    toast.success(t('toast.saved'))
    chargerDonnees()
  } catch (e) {
    toast.error(e.message)
  }
}

// Actions
async function actionArchiver(numero) {
  const ok = await confirmDialog({ message: t('confirmMsg.archive') })
  if (!ok) return
  try {
    await api.archiverEtudiant(numero)
    toast.success(t('toast.archived'))
    chargerDonnees()
  } catch (e) { toast.error(e.message) }
}

async function actionSupprimer(numero) {
  const ok = await confirmDialog({ message: t('confirmMsg.delete'), danger: true })
  if (!ok) return
  try {
    await api.supprimerEtudiant(numero)
    toast.success(t('toast.deleted'))
    chargerDonnees()
  } catch (e) { toast.error(e.message) }
}

function ouvrirFiche(student) {
  router.push({ name: 'fiche', params: { numero: student.numero } })
}
function allerModifierPage(student) {
  router.push({
    name: 'modifier',
    params: { numero: student.numero },
    query: { nom: student.nom, prenom: student.prenom, classe: student.classe }
  })
}

// Clic sur une ligne = ouvrir la fiche, sauf si l'on a cliqué sur un contrôle
function onRowClick(event, student) {
  if (event.target.closest('button, input, select, a, label')) return
  ouvrirFiche(student)
}

// Sélection / import
const toutCoche = computed(() =>
  etudiants.value.length > 0 && etudiants.value.every(s => selectedNumeros.value.includes(s.numero))
)
function toutCocher(event) {
  selectedNumeros.value = event.target.checked ? etudiants.value.map(s => s.numero) : []
}

async function importerSelection() {
  const jsonSelection = etudiants.value
    .filter(s => selectedNumeros.value.includes(s.numero) && s.provenance === 'JSON')
    .map(s => s.numero)
  if (jsonSelection.length === 0) { toast.warning(t('toast.importEmpty')); return }
  try {
    const data = await api.importerSelection(jsonSelection)
    toast.success(data.message || t('toast.importSuccess'))
    selectedNumeros.value = []
    chargerDonnees()
  } catch (e) {
    toast.error(t('toast.importError'))
  }
}

function exporterExcel() { exportToExcel(etudiantsTries.value, 'etudiants.xlsx') }
function exporterPdf() { exportToPdf(etudiantsTries.value, 'etudiants.pdf') }

watch(() => route.query, () => {
  appliquerQuery()
  pageActuelle.value = 1
  chargerDonnees()
})

onMounted(() => {
  appliquerQuery()
  chargerDonnees()
})
</script>

<template>
  <div class="container">
    <header class="page-head">
      <div>
        <h1>{{ t('list.title') }}</h1>
        <p>{{ t('list.subtitle', { n: totalGlobalDonnees }) }}</p>
      </div>
      <div class="page-actions">
        <button class="btn-muted btn-sm" @click="exporterExcel"><i class="fa-solid fa-file-excel"></i> {{ t('export.excel') }}</button>
        <button class="btn-muted btn-sm" @click="exporterPdf"><i class="fa-solid fa-file-pdf"></i> {{ t('export.pdf') }}</button>
      </div>
    </header>

    <section class="card">
      <!-- Filtres -->
      <div class="filters">
        <div class="search-field">
          <i class="fa-solid fa-magnifying-glass"></i>
          <input
            v-model="filtres.nomPrenom" type="text" class="field-input"
            :placeholder="t('filters.nomPrenom')" :aria-label="t('filters.nomPrenom')" @input="onFiltreChange"
          >
        </div>
        <select v-model="filtres.classe" class="field-input" :aria-label="t('filters.allClasses')" @change="onFiltreChange">
          <option value="">{{ t('filters.allClasses') }}</option>
          <option v-for="c in classesOptions" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="filtres.source" class="field-input" :aria-label="t('filters.allSources')" @change="onFiltreChange">
          <option value="">{{ t('filters.allSources') }}</option>
          <option value="DB">{{ t('filters.sourceDb') }}</option>
          <option value="JSON">{{ t('filters.sourceJson') }}</option>
        </select>
        <button class="btn-ghost btn-sm" :aria-expanded="filtresAvances" @click="filtresAvances = !filtresAvances">
          <i class="fa-solid fa-sliders"></i> {{ t('filters.advanced') }}
        </button>
        <button v-if="filtresActifs" class="btn-ghost btn-sm" @click="reinitialiserFiltres">
          <i class="fa-solid fa-xmark"></i> {{ t('common.clear') }}
        </button>

        <div class="filters-right">
          <div class="seg" role="group" :aria-label="t('list.view')">
            <button :class="{ on: vue === 'table' }" :title="t('list.viewTable')" :aria-label="t('list.viewTable')" @click="changerVue('table')"><i class="fa-solid fa-table-list"></i></button>
            <button :class="{ on: vue === 'cards' }" :title="t('list.viewCards')" :aria-label="t('list.viewCards')" @click="changerVue('cards')"><i class="fa-solid fa-table-cells-large"></i></button>
          </div>
          <label for="row-size-select" class="sr-only">{{ t('filters.show') }}</label>
          <select id="row-size-select" v-model.number="taillePage" class="field-input" @change="changerTaillePage">
            <option :value="5">{{ t('filters.rows5') }}</option>
            <option :value="10">{{ t('filters.rows10') }}</option>
            <option :value="20">{{ t('filters.rows20') }}</option>
            <option :value="1000">{{ t('filters.rowsAll') }}</option>
          </select>
        </div>
      </div>

      <div v-if="filtresAvances" class="filters advanced">
        <input v-model="filtres.numero" type="text" class="field-input" :placeholder="t('filters.numero')" :aria-label="t('filters.numero')" @input="onFiltreChange">
        <input v-model="filtres.code" type="text" class="field-input" :placeholder="t('filters.code')" :aria-label="t('filters.code')" @input="onFiltreChange">
      </div>

      <!-- Barre de sélection -->
      <transition name="fade">
        <div v-if="selectedNumeros.length" class="bulk">
          <span><strong>{{ selectedNumeros.length }}</strong> {{ t('list.selected', selectedNumeros.length) }}</span>
          <div>
            <button class="btn-success btn-sm" @click="importerSelection"><i class="fa-solid fa-download"></i> {{ t('nav.import') }}</button>
            <button class="btn-ghost btn-sm" @click="selectedNumeros = []">{{ t('list.unselect') }}</button>
          </div>
        </div>
      </transition>

      <!-- Vue tableau -->
      <div v-if="vue === 'table'" class="table-wrap">
        <table>
          <caption class="sr-only">{{ t('list.title') }}</caption>
          <thead>
            <tr>
              <th style="width: 44px;"><input type="checkbox" :checked="toutCoche" :aria-label="t('list.selectAll')" @change="toutCocher"></th>
              <th class="th-sortable" :class="{ active: tri.colonne === 'nom' }" @click="trierPar('nom')">
                {{ t('table.student') }} <i class="fa-solid" :class="iconeTri('nom')"></i>
              </th>
              <th class="th-sortable" :class="{ active: tri.colonne === 'numero' }" @click="trierPar('numero')">
                {{ t('table.numero') }} <i class="fa-solid" :class="iconeTri('numero')"></i>
              </th>
              <th class="th-sortable" :class="{ active: tri.colonne === 'classe' }" @click="trierPar('classe')">
                {{ t('table.classe') }} <i class="fa-solid" :class="iconeTri('classe')"></i>
              </th>
              <th class="th-sortable" :class="{ active: tri.colonne === 'moyenne_generale' }" @click="trierPar('moyenne_generale')">
                {{ t('table.moyenne') }} <i class="fa-solid" :class="iconeTri('moyenne_generale')"></i>
              </th>
              <th>{{ t('table.provenance') }}</th>
              <th style="width: 176px; text-align: right;">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <SkeletonRows v-if="isLoading" :columns="7" :rows="taillePage > 10 ? 10 : taillePage" />
            <tr v-else-if="etudiantsTries.length === 0">
              <td colspan="7">
                <EmptyState icon="fa-magnifying-glass" :title="t('table.noStudents')" :text="t('list.noResultsHint')">
                  <button v-if="filtresActifs" class="btn-muted btn-sm" @click="reinitialiserFiltres">{{ t('common.clear') }}</button>
                </EmptyState>
              </td>
            </tr>
            <template v-else>
              <tr
                v-for="student in etudiantsTries" :key="student.numero"
                :class="{ 'row-link': ligneEnEdition !== student.numero }"
                @click="onRowClick($event, student)"
              >
                <template v-if="ligneEnEdition === student.numero">
                  <td><input type="checkbox" disabled></td>
                  <td>
                    <div class="edit-names">
                      <input v-model="editBuffer.prenom" type="text" class="inline-input" :aria-label="t('table.prenom')" :placeholder="t('table.prenom')">
                      <input v-model="editBuffer.nom" type="text" class="inline-input" :aria-label="t('table.nom')" :placeholder="t('table.nom')">
                    </div>
                  </td>
                  <td class="num"><strong>{{ student.numero }}</strong></td>
                  <td>
                    <select v-model="editBuffer.classe" class="inline-input" :aria-label="t('table.classe')">
                      <option v-for="c in classesOptions" :key="c" :value="c">{{ c }}</option>
                    </select>
                  </td>
                  <td class="num"><strong>{{ student.moyenne_generale || '–' }}</strong></td>
                  <td><span :class="['badge', `badge-${student.provenance.toLowerCase()}`]">{{ student.provenance }}</span></td>
                  <td style="text-align: right;">
                    <button class="action-icon-btn save" :aria-label="t('table.save')" :title="t('table.save')" @click="sauvegarderInline(student.numero)"><i class="fa-solid fa-check"></i></button>
                    <button class="action-icon-btn cancel" :aria-label="t('table.cancelEdit')" :title="t('table.cancelEdit')" @click="annulerInline"><i class="fa-solid fa-xmark"></i></button>
                  </td>
                </template>
                <template v-else>
                  <td><input v-model="selectedNumeros" type="checkbox" :value="student.numero" :aria-label="`${t('list.select')} ${student.numero}`"></td>
                  <td>
                    <div class="student-cell">
                      <StudentAvatar :nom="student.nom" :prenom="student.prenom" :size="38" />
                      <div class="student-id">
                        <strong>{{ student.prenom }} {{ student.nom }}</strong>
                        <small class="num">{{ student.code }}</small>
                      </div>
                    </div>
                  </td>
                  <td class="num">{{ student.numero }}</td>
                  <td><span class="chip">{{ student.classe }}</span></td>
                  <td>
                    <div class="score-cell">
                      <strong class="num" :style="{ color: toneVar(mentionFor(student.moyenne_generale).tone) }">
                        {{ toNumber(student.moyenne_generale) ? Number(student.moyenne_generale).toFixed(2) : '–' }}
                      </strong>
                      <span class="bar"><span :style="{ width: `${((toNumber(student.moyenne_generale) || 0) / 20) * 100}%`, background: toneVar(mentionFor(student.moyenne_generale).tone) }"></span></span>
                    </div>
                  </td>
                  <td><span :class="['badge', `badge-${student.provenance.toLowerCase()}`]">{{ student.provenance }}</span></td>
                  <td style="text-align: right; white-space: nowrap;">
                    <button class="action-icon-btn view" :aria-label="t('table.viewFile')" :title="t('table.viewFile')" @click="ouvrirFiche(student)"><i class="fa-solid fa-eye"></i></button>
                    <button class="action-icon-btn edit-inline" :aria-label="t('table.editInline')" :title="t('table.editInline')" @click="activerInline(student)"><i class="fa-solid fa-pen"></i></button>
                    <button class="action-icon-btn edit-page" :aria-label="t('table.editFull')" :title="t('table.editFull')" @click="allerModifierPage(student)"><i class="fa-solid fa-user-pen"></i></button>
                    <template v-if="student.provenance === 'DB'">
                      <button class="action-icon-btn archive" :aria-label="t('table.archive')" :title="t('table.archive')" @click="actionArchiver(student.numero)"><i class="fa-solid fa-box-archive"></i></button>
                      <button class="action-icon-btn delete" :aria-label="t('table.delete')" :title="t('table.delete')" @click="actionSupprimer(student.numero)"><i class="fa-solid fa-trash-can"></i></button>
                    </template>
                  </td>
                </template>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Vue cartes -->
      <div v-else class="cards-grid">
        <template v-if="isLoading">
          <div v-for="n in 8" :key="n" class="skeleton" style="height: 168px;"></div>
        </template>
        <EmptyState v-else-if="etudiantsTries.length === 0" icon="fa-magnifying-glass" :title="t('table.noStudents')" :text="t('list.noResultsHint')" style="grid-column: 1 / -1" />
        <template v-else>
        <article v-for="student in etudiantsTries" :key="student.numero" class="student-card" tabindex="0" @click="ouvrirFiche(student)" @keydown.enter="ouvrirFiche(student)">
          <div class="sc-top">
            <StudentAvatar :nom="student.nom" :prenom="student.prenom" :size="48" />
            <span :class="['badge', `badge-${student.provenance.toLowerCase()}`]">{{ student.provenance }}</span>
          </div>
          <strong class="sc-name">{{ student.prenom }} {{ student.nom }}</strong>
          <small class="num">{{ student.numero }} · {{ student.classe }}</small>
          <div class="sc-bottom">
            <ScoreRing :value="student.moyenne_generale" :size="56" :stroke="6" :show-max="false" />
            <MentionPill :moyenne="student.moyenne_generale" />
          </div>
        </article>
        </template>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <span class="page-info num">{{ t('pagination.range', { from: debutPage, to: finPage, total: totalGlobalDonnees }) }}</span>
        <div class="pagination-pages">
          <button :disabled="precedentDesactive" :aria-label="t('pagination.previous')" @click="pagePrecedente"><i class="fa-solid fa-angle-left"></i></button>
          <template v-for="(p, i) in pagesAffichees" :key="`${p}-${i}`">
            <span v-if="p === '…'" class="page-ellipsis">…</span>
            <button v-else :class="{ active: p === pageActuelle }" @click="allerPage(p)">{{ p }}</button>
          </template>
          <button :disabled="suivantDesactive" :aria-label="t('pagination.next')" @click="pageSuivante"><i class="fa-solid fa-angle-right"></i></button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.filters { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.filters.advanced { background: var(--surface-2); padding-top: 12px; padding-bottom: 12px; }
.filters.advanced input { min-width: 200px; }
.search-field { position: relative; flex: 1 1 260px; max-width: 380px; }
.search-field i { position: absolute; left: 13px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 13px; }
.search-field input { width: 100%; padding-left: 36px; }
.filters-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }

.seg { display: inline-flex; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.seg button { background: transparent; color: var(--muted); border-radius: 0; padding: 9px 12px; }
.seg button.on { background: var(--primary-soft); color: var(--primary); }

.bulk {
  display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  padding: 10px 20px; background: var(--primary-soft); color: var(--ink); font-size: 14px;
}
.bulk div { display: flex; gap: 8px; }

.student-cell { display: flex; align-items: center; gap: 12px; min-width: 220px; }
.student-id { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }
.student-id strong { color: var(--ink); }
.student-id small { color: var(--muted); font-size: 12.5px; }
.edit-names { display: flex; gap: 8px; min-width: 260px; }
.score-cell { display: flex; align-items: center; gap: 10px; min-width: 130px; }
.score-cell strong { min-width: 40px; }
.score-cell .bar { flex: 1; max-width: 90px; }

.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 16px; padding: 20px; }
.student-card {
  display: flex; flex-direction: column; gap: 2px; padding: 16px; cursor: pointer;
  background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.student-card:hover { border-color: var(--primary); transform: translateY(-2px); }
.sc-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.sc-name { color: var(--ink); font-family: var(--font-display); font-size: 16px; line-height: 1.25; }
.student-card small { color: var(--muted); }
.sc-bottom { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; }

@media (max-width: 700px) {
  .filters-right { margin-left: 0; width: 100%; justify-content: space-between; }
  .search-field { max-width: none; }
}
</style>
