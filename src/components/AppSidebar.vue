<script setup>
import { computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { APP_NAME, APP_TAGLINE } from '../config'
import { useShell } from '../composables/useShell'
import { useStats } from '../composables/useStats'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { sidebarCollapsed, mobileOpen, toggleCollapse, closeMobile } = useShell()
const { indicateurs, loadStats } = useStats()
const { isAuthEnabled, logout } = useAuth()

const groups = computed(() => [
  {
    label: t('nav.groupOverview'),
    items: [
      { to: '/', icon: 'fa-house', label: t('nav.home'), match: p => p === '/' },
      { to: '/dashboard', icon: 'fa-chart-pie', label: t('nav.analytics'), match: p => p.startsWith('/dashboard') }
    ]
  },
  {
    label: t('nav.groupStudents'),
    items: [
      {
        to: '/etudiants', icon: 'fa-users', label: t('nav.registry'),
        match: p => p.startsWith('/etudiants') || p.startsWith('/modifier'),
        badge: indicateurs.db + indicateurs.json || null
      },
      { to: '/classes', icon: 'fa-school', label: t('nav.classes'), match: p => p.startsWith('/classes') },
      { to: '/ajouter', icon: 'fa-user-plus', label: t('nav.newStudent'), match: p => p.startsWith('/ajouter') },
      {
        to: '/archive', icon: 'fa-box-archive', label: t('nav.archives'),
        match: p => p.startsWith('/archive'), badge: indicateurs.archives || null
      }
    ]
  }
])

function handleLogout() {
  logout()
  closeMobile()
  router.push('/login')
}

// Les compteurs se rafraîchissent à chaque navigation (appel léger, mis en cache 4 s)
onMounted(() => loadStats(true))
watch(() => route.fullPath, () => { loadStats(); closeMobile() })
</script>

<template>
  <div v-if="mobileOpen" class="scrim" @click="closeMobile"></div>
  <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, open: mobileOpen }" :aria-label="t('nav.mainNav')">
    <router-link to="/" class="brand" :title="APP_NAME">
      <span class="brand-mark"><i class="fa-solid fa-graduation-cap"></i></span>
      <span class="brand-text">
        <strong>{{ APP_NAME }}</strong>
        <small>{{ APP_TAGLINE }}</small>
      </span>
    </router-link>

    <nav class="nav">
      <div v-for="group in groups" :key="group.label" class="nav-group">
        <p class="nav-group-label">{{ group.label }}</p>
        <router-link
          v-for="item in group.items" :key="item.to" :to="item.to"
          class="nav-item" :class="{ active: item.match(route.path) }"
          :title="item.label"
        >
          <i class="fa-solid" :class="item.icon"></i>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-foot">
      <div class="user">
        <span class="user-avatar">AD</span>
        <span class="user-text">
          <strong>{{ t('nav.admin') }}</strong>
          <small>{{ t('nav.adminRole') }}</small>
        </span>
        <button v-if="isAuthEnabled" class="icon-btn" :title="t('nav.logout')" :aria-label="t('nav.logout')" @click="handleLogout">
          <i class="fa-solid fa-right-from-bracket"></i>
        </button>
      </div>
      <button class="collapse-btn" :title="t('nav.collapse')" :aria-label="t('nav.collapse')" @click="toggleCollapse">
        <i class="fa-solid" :class="sidebarCollapsed ? 'fa-angles-right' : 'fa-angles-left'"></i>
        <span class="nav-label">{{ t('nav.collapse') }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  z-index: 60;
  transition: width 0.22s ease, transform 0.25s ease;
}
.sidebar.collapsed { width: var(--sidebar-w-collapsed); }

.brand {
  display: flex; align-items: center; gap: 12px;
  padding: 6px 8px 22px;
  text-decoration: none; color: #fff;
}
.brand-mark {
  flex: none; width: 40px; height: 40px; border-radius: 12px;
  background: var(--accent); color: #2b1d00;
  display: inline-flex; align-items: center; justify-content: center; font-size: 18px;
}
.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }
.brand-text strong { font-family: var(--font-display); font-size: 19px; letter-spacing: -0.01em; }
.brand-text small { color: var(--sidebar-text); font-size: 12px; white-space: nowrap; }

.nav { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 18px; }
.nav-group { display: flex; flex-direction: column; gap: 2px; }
.nav-group-label { margin: 0 0 6px 12px; font-size: 12.5px; font-weight: 600; color: #6f9296; }

.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 10px;
  color: var(--sidebar-text); text-decoration: none;
  font-weight: 600; font-size: 14px;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.nav-item i { width: 20px; text-align: center; font-size: 15px; flex: none; }
.nav-item:hover { background: rgba(255, 255, 255, 0.07); color: #fff; }
.nav-item.active { background: rgba(255, 255, 255, 0.12); color: #fff; }
.nav-item.active::before {
  content: ""; position: absolute; left: -14px; top: 9px; bottom: 9px; width: 4px;
  border-radius: 0 4px 4px 0; background: var(--accent);
}
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-badge {
  margin-left: auto; font-size: 12px; font-weight: 700; padding: 1px 8px; border-radius: 999px;
  background: rgba(255, 255, 255, 0.12); color: #fff; font-variant-numeric: tabular-nums;
}

.sidebar-foot { display: flex; flex-direction: column; gap: 10px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.user { display: flex; align-items: center; gap: 10px; padding: 4px 6px; }
.user-avatar {
  flex: none; width: 36px; height: 36px; border-radius: 50%;
  background: rgba(255, 255, 255, 0.14); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 700; font-size: 13px;
}
.user-text { display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }
.user-text strong { color: #fff; font-size: 13.5px; }
.user-text small { font-size: 12px; }
.icon-btn { margin-left: auto; background: transparent; color: var(--sidebar-text); padding: 8px; border-radius: 8px; }
.icon-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.collapse-btn {
  background: transparent; color: var(--sidebar-text);
  padding: 9px 12px; font-size: 13px; border-radius: 10px;
}
.collapse-btn:hover { background: rgba(255, 255, 255, 0.07); color: #fff; }
.collapse-btn i { width: 20px; text-align: center; }

/* Menu réduit : icônes seules */
.sidebar.collapsed .brand-text,
.sidebar.collapsed .nav-label,
.sidebar.collapsed .nav-group-label,
.sidebar.collapsed .user-text,
.sidebar.collapsed .icon-btn { display: none; }
.sidebar.collapsed .nav-badge { display: none; }
.sidebar.collapsed .nav-item, .sidebar.collapsed .collapse-btn { justify-content: center; }
.sidebar.collapsed .brand { justify-content: center; padding-left: 0; padding-right: 0; }
.sidebar.collapsed .user { justify-content: center; }
.sidebar.collapsed .nav-group + .nav-group { padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.08); }

.scrim { position: fixed; inset: 0; background: rgba(6, 28, 32, 0.55); z-index: 55; }

@media (max-width: 960px) {
  .sidebar, .sidebar.collapsed { width: 280px; transform: translateX(-100%); }
  .sidebar.open { transform: translateX(0); box-shadow: var(--shadow-lg); }
  .sidebar.collapsed .brand-text, .sidebar.collapsed .nav-label, .sidebar.collapsed .nav-group-label,
  .sidebar.collapsed .user-text, .sidebar.collapsed .icon-btn, .sidebar.collapsed .nav-badge { display: revert; }
  .sidebar.collapsed .nav-item, .sidebar.collapsed .collapse-btn { justify-content: flex-start; }
  .collapse-btn { display: none; }
}
</style>
