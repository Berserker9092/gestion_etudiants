import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import i18n from '../i18n'
import { APP_NAME } from '../config'

// titleKey / sectionKey : clés i18n utilisées par le fil d'Ariane et le titre de l'onglet
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { titleKey: 'login.title', public: true, layout: 'blank' }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
    meta: { titleKey: 'nav.home', sectionKey: 'nav.groupOverview' }
  },
  {
    path: '/etudiants',
    name: 'liste',
    component: () => import('../views/EtudiantsListe.vue'),
    meta: { titleKey: 'nav.registry', sectionKey: 'nav.groupStudents' }
  },
  {
    path: '/etudiants/:numero',
    name: 'fiche',
    component: () => import('../views/EtudiantFiche.vue'),
    props: true,
    meta: { titleKey: 'fiche.pageTitle', sectionKey: 'nav.registry' }
  },
  {
    path: '/classes',
    name: 'classes',
    component: () => import('../views/Classes.vue'),
    meta: { titleKey: 'nav.classes', sectionKey: 'nav.groupStudents' }
  },
  {
    path: '/ajouter',
    name: 'ajouter',
    component: () => import('../views/EtudiantAjouter.vue'),
    meta: { titleKey: 'nav.newStudent', sectionKey: 'nav.groupStudents' }
  },
  {
    path: '/modifier/:numero',
    name: 'modifier',
    component: () => import('../views/EtudiantModifier.vue'),
    props: true,
    meta: { titleKey: 'edit.pageTitle', sectionKey: 'nav.registry' }
  },
  {
    path: '/archive',
    name: 'archive',
    component: () => import('../views/Archive.vue'),
    meta: { titleKey: 'nav.archiveBox', sectionKey: 'nav.groupStudents' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { titleKey: 'nav.analytics', sectionKey: 'nav.groupOverview' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'notfound',
    component: () => import('../views/NotFound.vue'),
    meta: { titleKey: 'notFound.title' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const { t } = i18n.global
  document.title = to.meta.titleKey ? `${t(to.meta.titleKey)} | ${APP_NAME}` : APP_NAME

  // Scaffold auth : ne bloque rien tant que VITE_AUTH_ENABLED n'est pas "true"
  const { isAuthEnabled, isAuthenticated } = useAuth()
  if (isAuthEnabled && !to.meta.public && !isAuthenticated()) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  next()
})

export default router
