import { reactive } from 'vue'

const state = reactive({
  visible: false,
  title: '',
  message: '',
  confirmLabel: '',
  cancelLabel: '',
  danger: false,
  resolver: null
})

export function useConfirm() {
  function confirmDialog({ title = '', message, confirmLabel, cancelLabel, danger = false }) {
    return new Promise(resolve => {
      state.title = title
      state.message = message
      state.confirmLabel = confirmLabel
      state.cancelLabel = cancelLabel
      state.danger = danger
      state.visible = true
      state.resolver = resolve
    })
  }

  function handle(result) {
    state.visible = false
    if (state.resolver) {
      state.resolver(result)
      state.resolver = null
    }
  }

  return { state, confirmDialog, handle }
}
