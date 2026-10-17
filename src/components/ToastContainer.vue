<script setup>
import { useToast } from '../composables/useToast'

const { toasts, remove } = useToast()

const icons = {
  success: 'fa-circle-check',
  error: 'fa-circle-exclamation',
  info: 'fa-circle-info',
  warning: 'fa-triangle-exclamation'
}
</script>

<template>
  <div class="toast-container" role="status" aria-live="polite">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" :class="['toast', `toast-${t.type}`]">
        <i :class="['fa-solid', icons[t.type]]"></i>
        <span>{{ t.message }}</span>
        <button class="toast-close" :aria-label="$t('common.close')" @click="remove(t.id)">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 360px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--card-bg, #fff);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  font-weight: 600;
  border-left: 4px solid var(--info);
  color: var(--text, #334155);
}

.toast-success { border-left-color: var(--success); }
.toast-success i:first-child { color: var(--success); }
.toast-error { border-left-color: var(--danger); }
.toast-error i:first-child { color: var(--danger); }
.toast-info { border-left-color: var(--info); }
.toast-info i:first-child { color: var(--info); }
.toast-warning { border-left-color: var(--warning); }
.toast-warning i:first-child { color: var(--warning); }

.toast span { flex: 1; }

.toast-close {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--muted, #64748b);
  font-size: 13px;
}

.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(30px); }
.toast-leave-to { opacity: 0; transform: translateX(30px); }
</style>
