<script setup>
import { useConfirm } from '../composables/useConfirm'

const { state, handle } = useConfirm()
</script>

<template>
  <transition name="modal">
    <div v-if="state.visible" class="modal-backdrop" @click.self="handle(false)">
      <div class="modal-box" role="alertdialog" aria-modal="true" :aria-label="state.title">
        <div class="modal-icon" :class="{ danger: state.danger }">
          <i class="fa-solid" :class="state.danger ? 'fa-triangle-exclamation' : 'fa-circle-question'"></i>
        </div>
        <h3 v-if="state.title">{{ state.title }}</h3>
        <p>{{ state.message }}</p>
        <div class="modal-actions">
          <button class="btn-muted" @click="handle(false)">{{ state.cancelLabel || $t('common.cancel') }}</button>
          <button :class="state.danger ? 'btn-danger' : 'btn-primary'" @click="handle(true)">
            {{ state.confirmLabel || $t('common.confirm') }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2500;
  padding: 20px;
}

.modal-box {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 28px;
  max-width: 400px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #e0f2fe;
  color: var(--info);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 16px;
}
.modal-icon.danger { background: #ffeeed; color: var(--danger); }

.modal-box h3 { margin: 0 0 8px; color: var(--primary); font-size: 18px; }
.modal-box p { margin: 0 0 22px; color: var(--text); font-size: 14px; line-height: 1.5; }

.modal-actions { display: flex; gap: 12px; justify-content: center; }
.modal-actions button { flex: 1; justify-content: center; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.18s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-box, .modal-leave-active .modal-box { transition: transform 0.18s ease; }
.modal-enter-from .modal-box, .modal-leave-to .modal-box { transform: scale(0.94); }
</style>
