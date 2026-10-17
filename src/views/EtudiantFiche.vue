<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { exportBulletinPdf } from '../utils/export'
import { toNumber, mentionFor, toneVar, parseBirthDate, ageFrom } from '../utils/students'
import StudentAvatar from '../components/StudentAvatar.vue'
import ScoreRing from '../components/ScoreRing.vue'
import MentionPill from '../components/MentionPill.vue'
import EmptyState from '../components/EmptyState.vue'

const props = defineProps({ numero: { type: String, required: true } })

const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()
const { confirmDialog } = useConfirm()

const loading = ref(true)
const notFound = ref(false)
const busy = ref(false)
const student = ref(null)
const notes = ref([])
const classmates = ref([])

const normaliserNotes = list =>
  (list || []).map(n => ({
    id: n.note_id,
    matiere: n.nom_matiere,
    devoirs: (Array.isArray(n.note_devoir) ? n.note_devoir : [n.note_devoir])
      .map(v => toNumber(v))
      .filter(v => v !== null),
    examen: toNumber(n.note_examen) ?? 0,
    moyenne: toNumber(n.moyenne_matiere) ?? 0
  }))

async function charger() {
  loading.value = true
  notFound.value = false
  try {
    const found = await api.getEtudiant(props.numero)
    if (!found) { notFound.value = true; student.value = null; return }
    student.value = found
    // Le détail des notes n'existe en base que pour les étudiants DB ; le rang vient de la classe entière
    const [rawNotes, mates] = await Promise.all([
      found.provenance === 'DB' ? api.getNotes(found.numero).catch(() => []) : Promise.resolve([]),
      api.getEtudiantsParClasse(found.classe).catch(() => [])
    ])
    notes.value = normaliserNotes(rawNotes)
    classmates.value = mates
  } catch (e) {
    notFound.value = true
    toast.error(e.message || t('common.loadError'))
  } finally {
    loading.value = false
  }
}

const moyenne = computed(() => toNumber(student.value?.moyenne_generale) || 0)
const mention = computed(() => mentionFor(moyenne.value))
const isJson = computed(() => student.value?.provenance === 'JSON')
const isArchived = computed(() => !!student.value?.est_archive)

const birthDate = computed(() => parseBirthDate(student.value?.date_naissance))
const birthLabel = computed(() =>
  birthDate.value
    ? new Intl.DateTimeFormat(locale.value, { day: 'numeric', month: 'long', year: 'numeric' }).format(birthDate.value)
    : '–'
)
const age = computed(() => ageFrom(birthDate.value))

const classRanking = computed(() =>
  classmates.value.filter(s => (toNumber(s.moyenne_generale) || 0) > 0).sort((a, b) => b.moyenne_generale - a.moyenne_generale)
)
const rank = computed(() => {
  const idx = classRanking.value.findIndex(s => s.numero === student.value?.numero)
  return idx === -1 ? null : idx + 1
})
const classAverage = computed(() =>
  classRanking.value.length ? classRanking.value.reduce((s, x) => s + Number(x.moyenne_generale), 0) / classRanking.value.length : 0
)
const delta = computed(() => moyenne.value - classAverage.value)

const bestSubject = computed(() => [...notes.value].sort((a, b) => b.moyenne - a.moyenne)[0] || null)
const weakSubject = computed(() => [...notes.value].sort((a, b) => a.moyenne - b.moyenne)[0] || null)
const validated = computed(() => notes.value.filter(n => n.moyenne >= 10).length)

const fullName = computed(() => (student.value ? `${student.value.prenom} ${student.value.nom}` : ''))

async function copierMatricule() {
  try {
    await navigator.clipboard.writeText(student.value.numero)
    toast.info(t('fiche.copied'), 2000)
  } catch (e) { /* presse-papiers indisponible */ }
}

function modifier() {
  router.push({
    name: 'modifier',
    params: { numero: student.value.numero },
    query: { nom: student.value.nom, prenom: student.value.prenom, classe: student.value.classe }
  })
}

async function executer(action, confirmation, succes, apres) {
  if (confirmation) {
    const ok = await confirmDialog(confirmation)
    if (!ok) return
  }
  busy.value = true
  try {
    await action()
    toast.success(succes)
    await (apres ? apres() : charger())
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    busy.value = false
  }
}

const archiver = () => executer(() => api.archiverEtudiant(student.value.numero), { message: t('confirmMsg.archive') }, t('toast.archived'))
const restaurer = () => executer(() => api.restaurerEtudiant(student.value.numero), { message: t('confirmMsg.restore') }, t('toast.restored'))
const supprimer = () =>
  executer(() => api.supprimerEtudiant(student.value.numero), { message: t('confirmMsg.delete'), danger: true }, t('toast.deleted'), () => router.push('/etudiants'))
const importer = () => executer(() => api.importerSelection([student.value.numero]), null, t('toast.importSuccess'))

function telechargerBulletin() {
  exportBulletinPdf({
    student: student.value,
    notes: notes.value,
    average: moyenne.value,
    mention: t(`mention.${mention.value.key}`),
    appreciation: t(`fiche.appreciation.${mention.value.key}`),
    rank: rank.value,
    classSize: classRanking.value.length,
    classAverage: classAverage.value,
    birthLabel: birthLabel.value,
    labels: {
      title: t('fiche.bulletinTitle'),
      id: t('fiche.identity'),
      code: t('table.code'),
      numero: t('table.numero'),
      classe: t('table.classe'),
      birth: t('fiche.birth'),
      subject: t('edit.subject'),
      homework: t('add.homework'),
      exam: t('add.exam'),
      average: t('table.moyenne'),
      general: t('fiche.generalAverage'),
      rank: t('fiche.rank'),
      classAvg: t('fiche.classAverage'),
      generated: t('fiche.generatedOn')
    }
  })
}

watch(() => props.numero, charger)
onMounted(charger)
</script>

<template>
  <div class="container fiche">
    <router-link to="/etudiants" class="btn btn-back"><i class="fa-solid fa-arrow-left"></i> {{ t('nav.backToList') }}</router-link>

    <!-- Chargement -->
    <template v-if="loading">
      <div class="card" style="padding: 28px;"><div class="skeleton" style="height: 96px;"></div></div>
      <div class="layout">
        <div class="card" style="padding: 28px;"><div class="skeleton" style="height: 300px;"></div></div>
        <div class="card" style="padding: 28px;"><div class="skeleton" style="height: 300px;"></div></div>
      </div>
    </template>

    <!-- Introuvable -->
    <div v-else-if="notFound" class="card">
      <EmptyState icon="fa-user-slash" :title="t('fiche.notFoundTitle')" :text="t('fiche.notFoundText', { numero })">
        <router-link to="/etudiants" class="btn btn-primary">{{ t('nav.registry') }}</router-link>
      </EmptyState>
    </div>

    <template v-else-if="student">
      <div v-if="isArchived" class="banner archived">
        <i class="fa-solid fa-box-archive"></i> {{ t('fiche.archivedBanner') }}
        <button class="btn-sm btn-muted" :disabled="busy" @click="restaurer">{{ t('archive.restore') }}</button>
      </div>

      <!-- En-tête de la fiche -->
      <section class="card profile">
        <StudentAvatar :nom="student.nom" :prenom="student.prenom" :size="88" />
        <div class="identity">
          <h1>{{ fullName }}</h1>
          <div class="chips">
            <span class="chip"><i class="fa-solid fa-school"></i> {{ student.classe }}</span>
            <span :class="['badge', `badge-${student.provenance.toLowerCase()}`]">{{ student.provenance === 'DB' ? t('filters.sourceDb') : t('filters.sourceJson') }}</span>
            <span v-if="isArchived" class="badge badge-archive">{{ t('fiche.archived') }}</span>
          </div>
          <dl class="facts">
            <div><dt>{{ t('table.code') }}</dt><dd class="num">{{ student.code }}</dd></div>
            <div>
              <dt>{{ t('fiche.matricule') }}</dt>
              <dd class="num">
                {{ student.numero }}
                <button class="copy" :title="t('fiche.copy')" :aria-label="t('fiche.copy')" @click="copierMatricule"><i class="fa-regular fa-copy"></i></button>
              </dd>
            </div>
            <div><dt>{{ t('fiche.birth') }}</dt><dd>{{ birthLabel }}<span v-if="age !== null" class="muted"> · {{ t('fiche.years', { n: age }) }}</span></dd></div>
          </dl>
        </div>
        <div class="actions">
          <button class="btn-primary" @click="modifier"><i class="fa-solid fa-user-pen"></i> {{ t('fiche.edit') }}</button>
          <button class="btn-muted" :disabled="!notes.length" @click="telechargerBulletin"><i class="fa-solid fa-file-pdf"></i> {{ t('fiche.report') }}</button>
          <button v-if="isJson" class="btn-success" :disabled="busy" @click="importer"><i class="fa-solid fa-download"></i> {{ t('fiche.importDb') }}</button>
          <template v-else>
            <button v-if="!isArchived" class="btn-muted" :disabled="busy" @click="archiver"><i class="fa-solid fa-box-archive"></i> {{ t('table.archive') }}</button>
            <button class="btn-ghost danger" :disabled="busy" :title="t('table.delete')" :aria-label="t('table.delete')" @click="supprimer"><i class="fa-solid fa-trash-can"></i></button>
          </template>
        </div>
      </section>

      <div class="layout">
        <!-- Synthèse -->
        <section class="card summary">
          <ScoreRing :value="moyenne" :size="156" :stroke="12" />
          <MentionPill :moyenne="moyenne" class="big-pill" />
          <p class="appreciation">{{ t(`fiche.appreciation.${mention.key}`) }}</p>

          <ul class="stats">
            <li>
              <span><i class="fa-solid fa-ranking-star"></i> {{ t('fiche.rank') }}</span>
              <strong v-if="rank" class="num">{{ rank }}<small> / {{ classRanking.length }}</small></strong>
              <strong v-else>–</strong>
            </li>
            <li>
              <span><i class="fa-solid fa-people-group"></i> {{ t('fiche.classAverage') }}</span>
              <strong class="num">
                {{ classAverage ? classAverage.toFixed(2) : '–' }}
                <small v-if="classAverage" :style="{ color: delta >= 0 ? 'var(--success)' : 'var(--danger)' }">
                  {{ delta >= 0 ? '+' : '' }}{{ delta.toFixed(2) }}
                </small>
              </strong>
            </li>
            <li v-if="notes.length">
              <span><i class="fa-solid fa-circle-check"></i> {{ t('fiche.validated') }}</span>
              <strong class="num">{{ validated }}<small> / {{ notes.length }}</small></strong>
            </li>
            <li v-if="bestSubject">
              <span><i class="fa-solid fa-arrow-trend-up"></i> {{ t('fiche.best') }}</span>
              <strong>{{ bestSubject.matiere }}</strong>
            </li>
            <li v-if="weakSubject && weakSubject !== bestSubject">
              <span><i class="fa-solid fa-arrow-trend-down"></i> {{ t('fiche.weak') }}</span>
              <strong>{{ weakSubject.matiere }}</strong>
            </li>
          </ul>
        </section>

        <!-- Résultats par matière -->
        <section class="card results">
          <header class="card-head">
            <div>
              <h2>{{ t('fiche.results') }}</h2>
              <p class="card-sub">{{ t('fiche.resultsSub') }}</p>
            </div>
          </header>

          <div v-if="isJson" class="notice">
            <i class="fa-solid fa-circle-info"></i>
            <div>
              <strong>{{ t('fiche.jsonTitle') }}</strong>
              <p>{{ t('fiche.jsonText') }}</p>
            </div>
            <button class="btn-success btn-sm" :disabled="busy" @click="importer">{{ t('fiche.importDb') }}</button>
          </div>

          <EmptyState v-else-if="!notes.length" icon="fa-book-open" :title="t('fiche.noGrades')" :text="t('fiche.noGradesText')">
            <button class="btn-primary btn-sm" @click="modifier">{{ t('fiche.edit') }}</button>
          </EmptyState>

          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{{ t('edit.subject') }}</th>
                  <th>{{ t('add.homework') }}</th>
                  <th style="text-align:center">{{ t('add.exam') }}</th>
                  <th style="min-width: 180px">{{ t('table.moyenne') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="n in notes" :key="n.id">
                  <td><strong class="subject">{{ n.matiere }}</strong></td>
                  <td>
                    <div class="homework">
                      <span v-for="(d, i) in n.devoirs" :key="i" class="chip num">{{ d }}</span>
                      <span v-if="!n.devoirs.length" class="muted">–</span>
                    </div>
                  </td>
                  <td class="num" style="text-align:center"><strong>{{ n.examen }}</strong></td>
                  <td>
                    <div class="score-cell">
                      <strong class="num" :style="{ color: toneVar(mentionFor(n.moyenne).tone) }">{{ n.moyenne.toFixed(2) }}</strong>
                      <span class="bar"><span :style="{ width: `${(n.moyenne / 20) * 100}%`, background: toneVar(mentionFor(n.moyenne).tone) }"></span></span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="notes.length" class="formula">{{ t('fiche.formula') }}</p>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.fiche { display: flex; flex-direction: column; gap: 20px; }
.fiche > .btn-back { align-self: flex-start; margin-bottom: -6px; }

.banner {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 12px 16px; border-radius: 12px; background: var(--warning-soft); color: var(--ink); font-weight: 600;
}
.banner i { color: var(--warning); }
.banner button { margin-left: auto; }

.profile { display: flex; align-items: center; gap: 24px; padding: 26px 28px; flex-wrap: wrap; }
.identity { flex: 1; min-width: 260px; }
.identity h1 { margin: 0 0 10px; font-size: 30px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.facts { display: flex; gap: 28px; flex-wrap: wrap; margin: 0; }
.facts dt { font-size: 12.5px; color: var(--muted); font-weight: 600; }
.facts dd { margin: 2px 0 0; color: var(--ink); font-weight: 600; }
.muted { color: var(--muted); font-weight: 500; }
.copy { background: transparent; color: var(--muted); padding: 2px 6px; margin-left: 2px; border-radius: 6px; }
.copy:hover { background: var(--hover); color: var(--primary); }
.actions { display: flex; gap: 10px; flex-wrap: wrap; align-self: flex-start; }
.btn-ghost.danger { color: var(--danger); }
.btn-ghost.danger:hover:not(:disabled) { background: var(--danger-soft); }

.layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 20px; align-items: start; }

.summary { display: flex; flex-direction: column; align-items: center; padding: 28px 24px; gap: 12px; }
.big-pill { font-size: 13px; padding: 4px 14px; }
.appreciation { margin: 4px 0 6px; text-align: center; color: var(--text); max-width: 30ch; }
.stats { list-style: none; margin: 8px 0 0; padding: 0; width: 100%; border-top: 1px solid var(--border); }
.stats li { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.stats li:last-child { border-bottom: none; }
.stats span { color: var(--muted); font-size: 13.5px; display: flex; align-items: center; gap: 8px; }
.stats span i { width: 16px; text-align: center; color: var(--primary); }
.stats strong { color: var(--ink); text-align: right; }
.stats strong small { font-size: 12.5px; font-weight: 600; color: var(--muted); }

.subject { color: var(--ink); }
.homework { display: flex; gap: 6px; flex-wrap: wrap; }
.score-cell { display: flex; align-items: center; gap: 12px; }
.score-cell strong { min-width: 44px; }
.score-cell .bar { flex: 1; height: 8px; }
.formula { margin: 0; padding: 12px 24px 18px; font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--border); }

.notice { display: flex; gap: 14px; align-items: flex-start; margin: 20px 24px; padding: 16px; border-radius: 12px; background: var(--info-soft); }
.notice > i { color: var(--info); margin-top: 3px; }
.notice div { flex: 1; }
.notice p { margin: 2px 0 0; color: var(--text); font-size: 13.5px; }

@media (max-width: 1000px) {
  .layout { grid-template-columns: 1fr; }
  .actions { align-self: stretch; }
}
</style>
