<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import { useI18n } from 'vue-i18n'
import { api } from '../services/api'

const { t } = useI18n()
const activeTab = ref('generale')

const stats = reactive({
  moyenneClasse: '0.00',
  tauxReussite: '0%',
  max: '0.00',
  min: '0.00'
})

const chartMatieresRef = ref(null)
const chartRepartitionRef = ref(null)
const chartDistributionRef = ref(null)
const chartClassesMoyennesRef = ref(null)
const chartClassesSourcesRef = ref(null)

let chartInstances = []

function destroyCharts() {
  chartInstances.forEach(c => c.destroy())
  chartInstances = []
}

async function chargerStatistiquesEtGraphiques() {
  try {
    const [resStats, resEtudiants] = await Promise.all([
      api.getStatistiques(),
      api.getEtudiants({ size: 1000 })
    ])

    const listeEtudiants = resEtudiants.data || []
    const statsBack = resStats.indicateurs || {}

    const classesInfos = {}
    const tranchesNotes = { '0 à 5': 0, '5 à 10': 0, '10 à 12': 0, '12 à 14': 0, '14 à 16': 0, '16 à 20': 0 }
    let totalAdmis = 0, totalRedoublants = 0, totalMoyenneSomme = 0
    let noteMax = 0, noteMin = listeEtudiants.length ? 20 : 0, compteEtudiantsAvecNote = 0

    listeEtudiants.forEach(student => {
      const moy = parseFloat(student.moyenne_generale)
      const classe = student.classe || 'Inconnue'
      const source = student.provenance || 'DB'

      if (!classesInfos[classe]) {
        classesInfos[classe] = { sommeNotes: 0, totalEleves: 0, dbCount: 0, jsonCount: 0 }
      }
      if (source === 'DB') classesInfos[classe].dbCount++
      else if (source === 'JSON') classesInfos[classe].jsonCount++

      if (!isNaN(moy)) {
        compteEtudiantsAvecNote++
        totalMoyenneSomme += moy
        classesInfos[classe].sommeNotes += moy
        classesInfos[classe].totalEleves++

        if (moy > noteMax) noteMax = moy
        if (moy < noteMin) noteMin = moy

        if (moy >= 10) totalAdmis++
        else totalRedoublants++

        if (moy < 5) tranchesNotes['0 à 5']++
        else if (moy < 10) tranchesNotes['5 à 10']++
        else if (moy < 12) tranchesNotes['10 à 12']++
        else if (moy < 14) tranchesNotes['12 à 14']++
        else if (moy < 16) tranchesNotes['14 à 16']++
        else tranchesNotes['16 à 20']++
      }
    })

    const moyGeneraleGlobale = compteEtudiantsAvecNote > 0
      ? (totalMoyenneSomme / compteEtudiantsAvecNote)
      : parseFloat(statsBack.moyenne_generale_classe || 0)
    const tauxReussiteCalcule = compteEtudiantsAvecNote > 0
      ? ((totalAdmis / compteEtudiantsAvecNote) * 100)
      : parseFloat(statsBack.taux_reussite || 0)

    stats.moyenneClasse = moyGeneraleGlobale.toFixed(2)
    stats.tauxReussite = tauxReussiteCalcule.toFixed(1) + ' %'
    stats.max = (compteEtudiantsAvecNote > 0 ? noteMax : parseFloat(statsBack.note_max || 0)).toFixed(2)
    stats.min = (compteEtudiantsAvecNote > 0 ? noteMin : parseFloat(statsBack.note_min || 0)).toFixed(2)

    await nextTick()
    destroyCharts()

    // 1. Moyennes par matière
    const matieresObj = resStats.moyennes_par_matiere || {}
    const matieresLabels = Object.keys(matieresObj).length ? Object.keys(matieresObj) : ['Maths', 'Français', 'Anglais', 'Physique']
    const matieresValeurs = Object.keys(matieresObj).length ? Object.values(matieresObj) : [12, 11, 14, 10]

    chartInstances.push(new Chart(chartMatieresRef.value.getContext('2d'), {
      type: 'bar',
      data: {
        labels: matieresLabels,
        datasets: [{
          label: 'Moyenne générale',
          data: matieresValeurs,
          backgroundColor: 'rgba(52, 152, 219, 0.8)',
          borderColor: 'rgba(52, 152, 219, 1)',
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 20 } } }
    }))

    // 2. Répartition admis / redoublants
    const vAdmis = compteEtudiantsAvecNote > 0 ? totalAdmis : parseInt(statsBack.total_admis || 0)
    const vRedoub = compteEtudiantsAvecNote > 0 ? totalRedoublants : parseInt(statsBack.total_redoublants || 0)

    chartInstances.push(new Chart(chartRepartitionRef.value.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Admis', 'Redoublants'],
        datasets: [{ data: [vAdmis, vRedoub], backgroundColor: ['#2ecc71', '#e74c3c'], borderWidth: 2 }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '65%' }
    }))

    // 3. Distribution par tranche
    chartInstances.push(new Chart(chartDistributionRef.value.getContext('2d'), {
      type: 'line',
      data: {
        labels: Object.keys(tranchesNotes),
        datasets: [{
          label: "Nombre d'élèves",
          data: Object.values(tranchesNotes),
          fill: true,
          backgroundColor: 'rgba(243, 156, 18, 0.15)',
          borderColor: 'rgba(243, 156, 18, 1)',
          tension: 0.25,
          pointBackgroundColor: 'rgba(243, 156, 18, 1)'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    }))

    // Préparation données par classe
    const classesLabelsOrdonnees = Object.keys(classesInfos).sort()
    const moyennesParClasseData = []
    const sourceDbParClasseData = []
    const sourceJsonParClasseData = []

    classesLabelsOrdonnees.forEach(cls => {
      const info = classesInfos[cls]
      moyennesParClasseData.push(info.totalEleves > 0 ? (info.sommeNotes / info.totalEleves) : 0)
      sourceDbParClasseData.push(info.dbCount)
      sourceJsonParClasseData.push(info.jsonCount)
    })

    // 4. Moyennes par classe
    chartInstances.push(new Chart(chartClassesMoyennesRef.value.getContext('2d'), {
      type: 'bar',
      data: {
        labels: classesLabelsOrdonnees,
        datasets: [{
          label: 'Moyenne',
          data: moyennesParClasseData,
          backgroundColor: 'rgba(230, 126, 34, 0.8)',
          borderColor: 'rgba(230, 126, 34, 1)',
          borderWidth: 1.5,
          borderRadius: 4
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 20 } } }
    }))

    // 5. Sources par classe (stacked)
    chartInstances.push(new Chart(chartClassesSourcesRef.value.getContext('2d'), {
      type: 'bar',
      data: {
        labels: classesLabelsOrdonnees,
        datasets: [
          { label: 'Base [DB]', data: sourceDbParClasseData, backgroundColor: '#3498db' },
          { label: 'Fichier [JSON]', data: sourceJsonParClasseData, backgroundColor: '#f1c40f' }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } } }
    }))
  } catch (e) {
    console.error("Erreur d'analyse ou d'affichage :", e)
  }
}

onMounted(chargerStatistiquesEtGraphiques)
onBeforeUnmount(destroyCharts)
</script>

<template>
  <div class="container container-flat">
    <div class="header-zone">
      <h1 style="border-bottom: none; padding-bottom: 0; display:flex; align-items:center; gap:12px;">
        <i class="fa-solid fa-chart-line" style="color: var(--purple);"></i> {{ t('dashboard.title') }}
      </h1>
      <router-link to="/" class="btn-back" style="margin-bottom:0;"><i class="fa-solid fa-arrow-left"></i> {{ t('nav.backToManagement') }}</router-link>
    </div>

    <div class="tabs-container">
      <button :class="['tab-btn', { active: activeTab === 'generale' }]" @click="activeTab = 'generale'"><i class="fa-solid fa-eye"></i> {{ t('dashboard.tabGeneral') }}</button>
      <button :class="['tab-btn', { active: activeTab === 'classes' }]" @click="activeTab = 'classes'"><i class="fa-solid fa-school"></i> {{ t('dashboard.tabClasses') }}</button>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card" style="border-left: 4px solid var(--info); border-top: none;">
        <div class="kpi-info"><h3>{{ t('dashboard.avgGeneral') }}</h3><p>{{ stats.moyenneClasse }}</p></div>
        <div class="kpi-icon" style="background: #e0f2fe; color: var(--info);"><i class="fa-solid fa-graduation-cap"></i></div>
      </div>
      <div class="kpi-card" style="border-left: 4px solid var(--success); border-top: none;">
        <div class="kpi-info"><h3>{{ t('dashboard.successRate') }}</h3><p>{{ stats.tauxReussite }}</p></div>
        <div class="kpi-icon" style="background: #e0fdf4; color: var(--success);"><i class="fa-solid fa-user-check"></i></div>
      </div>
      <div class="kpi-card" style="border-left: 4px solid var(--warning); border-top: none;">
        <div class="kpi-info"><h3>{{ t('dashboard.highestAvg') }}</h3><p>{{ stats.max }}</p></div>
        <div class="kpi-icon" style="background: #fff7ed; color: var(--warning);"><i class="fa-solid fa-trophy"></i></div>
      </div>
      <div class="kpi-card" style="border-left: 4px solid var(--danger); border-top: none;">
        <div class="kpi-info"><h3>{{ t('dashboard.lowestAvg') }}</h3><p>{{ stats.min }}</p></div>
        <div class="kpi-icon" style="background: #ffeeed; color: var(--danger);"><i class="fa-solid fa-arrow-trend-down"></i></div>
      </div>
    </div>

    <div v-show="activeTab === 'generale'" class="tab-content">
      <div class="charts-grid">
        <div class="chart-wrapper">
          <h2><i class="fa-solid fa-chart-bar" style="color: var(--info);"></i> {{ t('dashboard.bySubject') }}</h2>
          <canvas ref="chartMatieresRef"></canvas>
        </div>
        <div class="chart-wrapper">
          <h2><i class="fa-solid fa-chart-pie" style="color: var(--purple);"></i> {{ t('dashboard.distribution') }}</h2>
          <canvas ref="chartRepartitionRef"></canvas>
        </div>
        <div class="chart-wrapper full-width">
          <h2><i class="fa-solid fa-chart-area" style="color: var(--warning);"></i> {{ t('dashboard.globalDistribution') }}</h2>
          <canvas ref="chartDistributionRef"></canvas>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'classes'" class="tab-content">
      <div class="charts-grid">
        <div class="chart-wrapper">
          <h2><i class="fa-solid fa-sliders" style="color: #e67e22;"></i> {{ t('dashboard.byClass') }}</h2>
          <canvas ref="chartClassesMoyennesRef"></canvas>
        </div>
        <div class="chart-wrapper">
          <h2><i class="fa-solid fa-database" style="color: #16a085;"></i> {{ t('dashboard.sourceByClass') }}</h2>
          <canvas ref="chartClassesSourcesRef"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header-zone {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid var(--border);
    padding-bottom: 15px;
    margin-bottom: 25px;
    flex-wrap: wrap;
    gap: 15px;
}

.tabs-container {
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
}
.tab-btn {
    background: none;
    border: none;
    padding: 10px 20px;
    font-size: 15px;
    font-weight: 600;
    color: var(--muted);
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.18s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}
.tab-btn:hover { background: #e2e8f0; color: var(--primary); }
.tab-btn.active { background: var(--primary); color: white; }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-bottom: 35px;
}
.kpi-card {
    padding: 22px;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kpi-info h3 { margin: 0; color: var(--muted); font-size: 13px; text-transform: uppercase; }
.kpi-info p { margin: 8px 0 0 0; font-size: 28px; font-weight: 700; color: var(--primary); }
.kpi-icon { width: 48px; height: 48px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }

.charts-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 25px;
}
.full-width { grid-column: span 2; }

@media (max-width: 900px) {
    .charts-grid, .full-width { grid-template-columns: 1fr; grid-column: span 1; }
}

.chart-wrapper {
    background: var(--card-bg);
    padding: 25px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03);
    position: relative;
    height: 320px;
    max-width: 100%;
}
.chart-wrapper h2 {
    margin-top: 0; margin-bottom: 15px; font-size: 16px; color: var(--primary); font-weight: 600;
    display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px;
}
.chart-wrapper canvas { max-height: 240px !important; width: 100% !important; }
</style>
