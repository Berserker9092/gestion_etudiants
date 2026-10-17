import { reactive } from 'vue'

const toasts = reactive([])
let uid = 0

function push(message, type = 'info', duration = 4000) {
  const id = ++uid
  toasts.push({ id, message, type })
  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }
  return id
}

function remove(id) {
  const index = toasts.findIndex(t => t.id === id)
  if (index !== -1) toasts.splice(index, 1)
}

export function useToast() {
  return {
    toasts,
    success: (msg, duration) => push(msg, 'success', duration),
    error: (msg, duration) => push(msg, 'error', duration),
    info: (msg, duration) => push(msg, 'info', duration),
    warning: (msg, duration) => push(msg, 'warning', duration),
    remove
  }
}
