<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { toNumber, mentionFor, toneVar } from '../utils/students'
import SkeletonRows from '../components/SkeletonRows.vue'
import StudentAvatar from '../components/StudentAvatar.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const { confirmDialog } = useConfirm()

const liste = ref([])
const isLoading = ref(true)

async function chargerArchives() {
  isLoading.value = true
  try {
    const result = await api.getEtudiants({ uniquement_archives: true, size: 1000 })
    liste.value = result.data || []
  } catch (e) {
    toast.error(e.message || t('common.loadError'))
  } finally {
    isLoading.value = false
  }
}

async function restaurer(numero) {
  const ok = await confirmDialog({ message: t('confirmMsg.restore') })
  if (!ok) return
  try {
    await api.restaurerEtudiant(numero)
    toast.success(t('toast.restored'))
    chargerArchives()
  } catch (e) { toast.error(e.message) }
}

async function supprimerDefinitif(numero) {
  const ok = await confirmDialog({ message: t('confirmMsg.deleteArchive'), danger: true })
  if (!ok) return
  try {
    await api.supprimerEtudiant(numero)
    toast.success(t('toast.deleted'))
    chargerArchives()
  } catch (e) { toast.error(e.message) }
}

function ouvrirFiche(s) { router.push({ name: 'fiche', params: { numero: s.numero } }) }
function onRowClick(event, s) {
  if (event.target.closest('button, a')) return
  ouvrirFiche(s)
}

onMounted(chargerArchives)
</script>

<template>
  <div class="container">
    <header class="page-head">
      <div>
        <h1>{{ t('archive.title') }}</h1>
        <p>{{ t('archive.subtitle') }}</p>
      </div>
    </header>

    <section class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{{ t('archive.nomPrenom') }}</th>
              <th>{{ t('table.numero') }}</th>
              <th>{{ t('table.classe') }}</th>
              <th>{{ t('table.moyenne') }}</th>
              <th style="width: 140px; text-align: right;">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <SkeletonRows v-if="isLoading" :columns="5" :rows="5" />
            <tr v-else-if="liste.length === 0">
              <td colspan="5">
                <EmptyState icon="fa-box-open" :title="t('archive.noArchived')" :text="t('archive.emptyHint')">
                  <router-link to="/etudiants" class="btn btn-muted btn-sm">{{ t('nav.registry') }}</router-link>
                </EmptyState>
              </td>
            </tr>
            <template v-else>
              <tr v-for="s in liste" :key="s.numero" class="row-link" @click="onRowClick($event, s)">
                <td>
                  <div class="student-cell">
                    <StudentAvatar :nom="s.nom" :prenom="s.prenom" :size="38" />
                    <div class="student-id">
                      <strong>{{ s.prenom }} {{ s.nom }}</strong>
                      <small class="num">{{ s.code }}</small>
                    </div>
                  </div>
                </td>
                <td class="num">{{ s.numero }}</td>
                <td><span class="chip">{{ s.classe }}</span></td>
                <td>
                  <strong class="num" :style="{ color: toneVar(mentionFor(s.moyenne_generale).tone) }">
                    {{ toNumber(s.moyenne_generale) ? Number(s.moyenne_generale).toFixed(2) : '–' }}
                  </strong>
                </td>
                <td style="text-align: right; white-space: nowrap;">
                  <button class="action-icon-btn view" :aria-label="t('table.viewFile')" :title="t('table.viewFile')" @click="ouvrirFiche(s)"><i class="fa-solid fa-eye"></i></button>
                  <button class="action-icon-btn restore" :aria-label="t('archive.restore')" :title="t('archive.restore')" @click="restaurer(s.numero)"><i class="fa-solid fa-trash-arrow-up"></i></button>
                  <button class="action-icon-btn delete" :aria-label="t('archive.delete')" :title="t('archive.delete')" @click="supprimerDefinitif(s.numero)"><i class="fa-solid fa-trash-can"></i></button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.student-cell { display: flex; align-items: center; gap: 12px; }
.student-id { display: flex; flex-direction: column; line-height: 1.25; }
.student-id strong { color: var(--ink); }
.student-id small { color: var(--muted); font-size: 12.5px; }
</style>
