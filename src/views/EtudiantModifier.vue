<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { moyenneMatiere, parseDevoirs, toNumber, mentionFor, toneVar } from '../utils/students'
import StudentAvatar from '../components/StudentAvatar.vue'
import ScoreRing from '../components/ScoreRing.vue'
import MentionPill from '../components/MentionPill.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const numero = route.params.numero
const isLoading = ref(true)
const isSubmitting = ref(false)

const profil = reactive({
  nom: route.query.nom || '',
  prenom: route.query.prenom || '',
  classe: route.query.classe || ''
})

const notes = ref([])
const classesOptions = ['6emeA', '6emeB', '5emeA', '5emeB', '4emeA', '4emeB', '3emeA', '3emeB']
const classesChoix = computed(() =>
  profil.classe && !classesOptions.includes(profil.classe) ? [profil.classe, ...classesOptions] : classesOptions
)

async function charger() {
  isLoading.value = true
  try {
    // Si la page est rechargée directement, les infos de profil ne sont plus dans l'URL : on les relit
    if (!profil.nom || !profil.prenom) {
      const found = await api.getEtudiant(numero)
      if (found) {
        profil.nom = found.nom
        profil.prenom = found.prenom
        profil.classe = found.classe
      }
    }
    const data = await api.getNotes(numero)
    notes.value = data.map(n => ({
      note_id: n.note_id,
      nom_matiere: n.nom_matiere,
      devoirsTexte: Array.isArray(n.note_devoir) ? n.note_devoir.join(', ') : n.note_devoir,
      note_examen: n.note_examen,
      moyenne_matiere: n.moyenne_matiere
    }))
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    isLoading.value = false
  }
}

// Moyennes recalculées en direct, avec la même formule que le backend
const moyennesLive = computed(() =>
  notes.value.map(n => moyenneMatiere(parseDevoirs(n.devoirsTexte), n.note_examen))
)
const moyenneGenerale = computed(() =>
  moyennesLive.value.length ? moyennesLive.value.reduce((s, v) => s + v, 0) / moyennesLive.value.length : 0
)

async function enregistrerTout() {
  isSubmitting.value = true
  const profilData = { nom: profil.nom.trim(), prenom: profil.prenom.trim(), classe: profil.classe.trim() }

  const listNotesModifiees = notes.value.map(n => ({
    note_id: n.note_id,
    note_devoir: parseDevoirs(n.devoirsTexte),
    note_examen: parseFloat(n.note_examen) || 0
  }))

  try {
    await api.modifierEtudiant(numero, profilData)
    await api.modifierNotes(numero, listNotesModifiees)
    toast.success(t('toast.notesSaved'))
    router.push({ name: 'fiche', params: { numero } })
  } catch (e) {
    toast.error(e.message || t('edit.saveError'))
  } finally {
    isSubmitting.value = false
  }
}

function annuler() { router.push({ name: 'fiche', params: { numero } }) }

onMounted(charger)
</script>

<template>
  <div class="container container-medium">
    <router-link :to="{ name: 'fiche', params: { numero } }" class="btn btn-back"><i class="fa-solid fa-arrow-left"></i> {{ t('edit.backToFile') }}</router-link>

    <header class="page-head">
      <div>
        <h1>{{ t('edit.title') }}</h1>
        <p>{{ t('edit.subtitle') }}</p>
      </div>
    </header>

    <form class="form-stack" @submit.prevent="enregistrerTout">
      <section class="card card-pad">
        <div class="head-row">
          <div class="who">
            <StudentAvatar :nom="profil.nom || '?'" :prenom="profil.prenom || '?'" :size="56" />
            <div>
              <strong>{{ profil.prenom }} {{ profil.nom }}</strong>
              <small class="num">{{ numero }}</small>
            </div>
          </div>
          <div class="live">
            <div>
              <small>{{ t('edit.liveAverage') }}</small>
              <MentionPill :moyenne="moyenneGenerale" />
            </div>
            <ScoreRing :value="moyenneGenerale" :size="84" :stroke="8" :show-max="false" />
          </div>
        </div>

        <div class="section-title" style="margin-top: 26px;"><i class="fa-solid fa-id-card"></i> {{ t('edit.studentInfo') }}</div>
        <div class="form-grid-perso">
          <div class="form-group">
            <label for="edit-numero">{{ t('edit.matricule') }}</label>
            <input id="edit-numero" type="text" :value="numero" disabled>
          </div>
          <div class="form-group">
            <label for="edit-classe">{{ t('add.classe') }}</label>
            <select id="edit-classe" v-model="profil.classe" required>
              <option v-for="c in classesChoix" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="edit-prenom">{{ t('add.prenom') }}</label>
            <input id="edit-prenom" v-model="profil.prenom" type="text" required :placeholder="t('add.prenom')">
          </div>
          <div class="form-group">
            <label for="edit-nom">{{ t('add.nom') }}</label>
            <input id="edit-nom" v-model="profil.nom" type="text" required :placeholder="t('add.nom')">
          </div>
        </div>
      </section>

      <section class="card">
        <header class="card-head">
          <div>
            <h2><i class="fa-solid fa-graduation-cap head-icon"></i> {{ t('edit.gradebook') }}</h2>
            <p class="card-sub">{{ t('edit.gradebookHint') }}</p>
          </div>
        </header>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{{ t('edit.subject') }}</th>
                <th>{{ t('edit.homeworkGrades') }}</th>
                <th style="width: 130px; text-align: center;">{{ t('edit.examGrade') }}</th>
                <th style="width: 190px;">{{ t('edit.currentAverage') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="4" style="text-align:center; color: var(--muted); padding: 28px;">{{ t('common.loading') }}</td>
              </tr>
              <tr v-else-if="!notes.length">
                <td colspan="4" style="text-align:center; color: var(--muted); padding: 28px;">{{ t('fiche.noGradesText') }}</td>
              </tr>
              <template v-else>
              <tr v-for="(n, i) in notes" :key="n.note_id">
                <td><strong style="color: var(--ink)">{{ n.nom_matiere }}</strong></td>
                <td>
                  <input v-model="n.devoirsTexte" type="text" class="inline-input" placeholder="Ex : 12, 15" :aria-label="`${t('edit.homeworkGrades')} ${n.nom_matiere}`">
                </td>
                <td style="text-align: center;">
                  <input v-model="n.note_examen" type="number" step="0.01" min="0" max="20" class="inline-input exam" :aria-label="`${t('edit.examGrade')} ${n.nom_matiere}`">
                </td>
                <td>
                  <div class="score-cell">
                    <strong class="num" :style="{ color: toneVar(mentionFor(moyennesLive[i]).tone) }">{{ moyennesLive[i].toFixed(2) }}</strong>
                    <span class="bar"><span :style="{ width: `${(moyennesLive[i] / 20) * 100}%`, background: toneVar(mentionFor(moyennesLive[i]).tone) }"></span></span>
                  </div>
                </td>
              </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>

      <div class="btn-group" style="margin-top: 0; border-top: none; padding-top: 0;">
        <button type="button" class="btn-muted" @click="annuler">{{ t('common.cancel') }}</button>
        <button type="submit" class="btn-primary btn-lg" :disabled="isSubmitting || isLoading">
          <i class="fa-solid fa-floppy-disk"></i> {{ isSubmitting ? t('common.loading') : t('edit.submit') }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.form-stack { display: flex; flex-direction: column; gap: 20px; }
.head-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
.who { display: flex; align-items: center; gap: 14px; }
.who div { display: flex; flex-direction: column; line-height: 1.3; }
.who strong { color: var(--ink); font-family: var(--font-display); font-size: 18px; }
.who small { color: var(--muted); }
.live { display: flex; align-items: center; gap: 14px; }
.live > div { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.live small { color: var(--muted); font-size: 12.5px; }
.head-icon { color: var(--primary); margin-right: 6px; }
.exam { width: 92px; text-align: center; }
.score-cell { display: flex; align-items: center; gap: 12px; }
.score-cell strong { min-width: 44px; }
.score-cell .bar { flex: 1; height: 8px; }
</style>
