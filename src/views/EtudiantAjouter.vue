<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { moyenneMatiere, toNumber, mentionFor, toneVar } from '../utils/students'
import StudentAvatar from '../components/StudentAvatar.vue'
import ScoreRing from '../components/ScoreRing.vue'
import MentionPill from '../components/MentionPill.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const isSubmitting = ref(false)

const form = reactive({
  code: '',
  numero: '',
  nom: '',
  prenom: '',
  date_naissance: '',
  classe: '6emeA'
})

const matieres = [
  { key: 'Math', label: 'Mathématiques' },
  { key: 'PC', label: 'Physique-Chimie (PC)' },
  { key: 'Francais', label: 'Français' },
  { key: 'Anglais', label: 'Anglais' },
  { key: 'SVT', label: 'SVT' },
  { key: 'HG', label: 'Histoire-Géo (HG)' }
]

const notes = reactive(Object.fromEntries(matieres.map(m => [m.key, { devoir: '', examen: '' }])))
const classesOptions = ['6emeA', '6emeB', '5emeA', '5emeB', '4emeA', '4emeB', '3emeA', '3emeB']

// Règles identiques à celles du backend (code AAA000, matricule de 7 caractères)
const errors = computed(() => ({
  code: form.code && !/^[A-Z]{3}\d{3}$/.test(form.code.trim().toUpperCase()) ? t('add.errCode') : '',
  numero: form.numero && form.numero.trim().length !== 7 ? t('add.errNumero') : '',
  nom: form.nom && form.nom.trim().length < 2 ? t('add.errShort') : '',
  prenom: form.prenom && form.prenom.trim().length < 2 ? t('add.errShort') : ''
}))
const hasErrors = computed(() => Object.values(errors.value).some(Boolean))

// Aperçu en direct : même formule que l'envoi — (devoir + 2 × examen) / 3, moyenne sur les 6 matières
const apercu = computed(() =>
  matieres.map(m => {
    const dev = toNumber(notes[m.key].devoir) || 0
    const ex = toNumber(notes[m.key].examen) || 0
    return { ...m, moyenne: moyenneMatiere([dev], ex), filled: notes[m.key].devoir !== '' || notes[m.key].examen !== '' }
  })
)
const moyenneGenerale = computed(() => apercu.value.reduce((s, m) => s + m.moyenne, 0) / apercu.value.length)
const filledCount = computed(() => apercu.value.filter(m => m.filled).length)

async function validerEtEnvoyer() {
  if (hasErrors.value) return
  isSubmitting.value = true
  const notesPayload = {}
  matieres.forEach(m => {
    const dev = parseFloat(notes[m.key].devoir) || 0.0
    const ex = parseFloat(notes[m.key].examen) || 0.0
    notesPayload[m.key] = {
      devoirs: [dev],
      examen: ex,
      moyenne: parseFloat(((dev + (ex * 2)) / 3).toFixed(2))
    }
  })

  // Conversion YYYY-MM-DD -> DD/MM/YYYY attendu par le validator Pydantic
  const parts = form.date_naissance.split('-')
  const dateFormatee = `${parts[2]}/${parts[1]}/${parts[0]}`

  const payload = {
    code: form.code.trim().toUpperCase(),
    numero: form.numero.trim(),
    nom: form.nom.trim(),
    prenom: form.prenom.trim(),
    date_naissance: dateFormatee,
    classe: form.classe,
    notes: notesPayload
  }

  try {
    await api.ajouterEtudiant(payload)
    toast.success(t('toast.created'))
    router.push({ name: 'fiche', params: { numero: payload.numero } })
  } catch (e) {
    toast.error(e.message || t('add.checkData'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="container">
    <header class="page-head">
      <div>
        <h1>{{ t('add.title') }}</h1>
        <p>{{ t('add.subtitle') }}</p>
      </div>
    </header>

    <div class="layout">
      <form class="card form-card" @submit.prevent="validerEtEnvoyer">
        <div class="block">
          <div class="section-title"><i class="fa-solid fa-user"></i> {{ t('add.personalInfo') }}</div>
          <div class="form-grid-perso">
            <div class="form-group">
              <label for="add-prenom">{{ t('add.prenom') }}</label>
              <input id="add-prenom" v-model="form.prenom" type="text" required placeholder="Ex : Awa">
              <span v-if="errors.prenom" class="err">{{ errors.prenom }}</span>
            </div>
            <div class="form-group">
              <label for="add-nom">{{ t('add.nom') }}</label>
              <input id="add-nom" v-model="form.nom" type="text" required placeholder="Ex : Diallo">
              <span v-if="errors.nom" class="err">{{ errors.nom }}</span>
            </div>
            <div class="form-group">
              <label for="add-code">{{ t('add.code') }}</label>
              <input id="add-code" v-model="form.code" type="text" required maxlength="6" placeholder="AAD001" :class="{ invalid: errors.code }">
              <span v-if="errors.code" class="err">{{ errors.code }}</span>
              <span v-else class="hint">{{ t('add.codeHint') }}</span>
            </div>
            <div class="form-group">
              <label for="add-numero">{{ t('add.numero') }}</label>
              <input id="add-numero" v-model="form.numero" type="text" required maxlength="7" placeholder="44DSW78" :class="{ invalid: errors.numero }">
              <span v-if="errors.numero" class="err">{{ errors.numero }}</span>
              <span v-else class="hint">{{ t('add.numeroHint') }}</span>
            </div>
            <div class="form-group">
              <label for="add-date">{{ t('add.birthDate') }}</label>
              <input id="add-date" v-model="form.date_naissance" type="date" required>
            </div>
            <div class="form-group">
              <label for="add-classe">{{ t('add.classe') }}</label>
              <select id="add-classe" v-model="form.classe" required>
                <option v-for="c in classesOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="section-title"><i class="fa-solid fa-graduation-cap"></i> {{ t('add.initialGrades') }}</div>
          <div class="notes-grid">
            <div v-for="m in matieres" :key="m.key" class="matiere-card">
              <div class="matiere-header">{{ m.label }}</div>
              <div class="matiere-inputs">
                <div class="form-group">
                  <label :for="`devoir-${m.key}`">{{ t('add.homework') }}</label>
                  <input :id="`devoir-${m.key}`" v-model="notes[m.key].devoir" type="number" step="0.01" min="0" max="20" placeholder="0.0">
                </div>
                <div class="form-group">
                  <label :for="`examen-${m.key}`">{{ t('add.exam') }}</label>
                  <input :id="`examen-${m.key}`" v-model="notes[m.key].examen" type="number" step="0.01" min="0" max="20" placeholder="0.0">
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="btn-group">
          <router-link to="/etudiants" class="btn btn-muted">{{ t('common.cancel') }}</router-link>
          <button type="submit" class="btn-primary btn-lg" :disabled="isSubmitting || hasErrors">
            <i class="fa-solid fa-floppy-disk"></i> {{ isSubmitting ? t('common.loading') : t('add.submit') }}
          </button>
        </div>
      </form>

      <!-- Aperçu en direct de la fiche -->
      <aside class="card preview" :aria-label="t('add.preview')">
        <h2>{{ t('add.preview') }}</h2>
        <div class="pv-id">
          <StudentAvatar :nom="form.nom || '?'" :prenom="form.prenom || '?'" :size="56" />
          <div>
            <strong>{{ (form.prenom || form.nom) ? `${form.prenom} ${form.nom}` : t('add.previewName') }}</strong>
            <small class="num">{{ form.classe }}<template v-if="form.numero"> · {{ form.numero }}</template></small>
          </div>
        </div>

        <div class="pv-score">
          <ScoreRing :value="moyenneGenerale" :size="112" :stroke="10" />
          <MentionPill :moyenne="moyenneGenerale" />
        </div>

        <ul class="pv-list">
          <li v-for="m in apercu" :key="m.key">
            <span>{{ m.label.split(' (')[0] }}</span>
            <span class="bar"><span :style="{ width: `${(m.moyenne / 20) * 100}%`, background: toneVar(mentionFor(m.moyenne).tone) }"></span></span>
            <strong class="num">{{ m.moyenne.toFixed(1) }}</strong>
          </li>
        </ul>
        <p class="pv-foot">{{ t('add.filled', { n: filledCount, total: matieres.length }) }}</p>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: minmax(0, 1fr) 330px; gap: 20px; align-items: start; }
.form-card { padding: 28px; display: flex; flex-direction: column; gap: 30px; }
.err { font-size: 12px; color: var(--danger); }
.invalid { border-color: var(--danger) !important; }
.btn-group { margin-top: 0; }

.notes-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.matiere-card { background: var(--surface-2); border: 1px solid var(--border); padding: 14px; border-radius: 12px; display: flex; flex-direction: column; gap: 10px; }
.matiere-header { font-family: var(--font-display); font-weight: 600; color: var(--ink); font-size: 14px; }
.matiere-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

.preview { position: sticky; top: calc(var(--topbar-h) + 20px); padding: 22px; display: flex; flex-direction: column; gap: 18px; }
.preview h2 { margin: 0; font-size: 16px; }
.pv-id { display: flex; align-items: center; gap: 12px; }
.pv-id div { display: flex; flex-direction: column; line-height: 1.3; min-width: 0; }
.pv-id strong { color: var(--ink); overflow-wrap: anywhere; }
.pv-id small { color: var(--muted); }
.pv-score { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 8px 0; }
.pv-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.pv-list li { display: grid; grid-template-columns: 92px 1fr 34px; align-items: center; gap: 10px; font-size: 13px; }
.pv-list li > span:first-child { color: var(--muted); }
.pv-list strong { text-align: right; color: var(--ink); }
.pv-foot { margin: 0; font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--border); padding-top: 12px; }

@media (max-width: 1100px) {
  .layout { grid-template-columns: 1fr; }
  .preview { position: static; order: -1; }
}
@media (max-width: 700px) {
  .notes-grid { grid-template-columns: 1fr; }
  .form-card { padding: 20px; }
}
</style>
