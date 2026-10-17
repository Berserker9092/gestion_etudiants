<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'
import { APP_NAME, APP_TAGLINE } from '../config'
import SettingsBar from '../components/SettingsBar.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { login } = useAuth()
const toast = useToast()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const showPassword = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    await login(form.username, form.password)
    router.push(route.query.redirect || '/')
  } catch (e) {
    toast.error(e.message || t('login.failed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <aside class="brand-panel">
      <div class="brand">
        <span class="brand-mark"><i class="fa-solid fa-graduation-cap"></i></span>
        <strong>{{ APP_NAME }}</strong>
      </div>
      <div class="pitch">
        <h2>{{ t('login.pitchTitle') }}</h2>
        <p>{{ t('login.pitchText') }}</p>
      </div>
      <small>{{ APP_NAME }} · {{ APP_TAGLINE }}</small>
    </aside>

    <main class="form-panel">
      <div class="settings"><SettingsBar /></div>
      <div class="login-box">
        <h1>{{ t('login.title') }}</h1>
        <p class="login-hint">{{ t('login.hint') }}</p>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="username">{{ t('login.username') }}</label>
            <input id="username" v-model="form.username" type="text" required autocomplete="username">
          </div>
          <div class="form-group">
            <label for="password">{{ t('login.password') }}</label>
            <div class="pwd">
              <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'" required autocomplete="current-password">
              <button type="button" class="eye" :aria-label="t('login.togglePassword')" @click="showPassword = !showPassword">
                <i class="fa-regular" :class="showPassword ? 'fa-eye-slash' : 'fa-eye'"></i>
              </button>
            </div>
          </div>
          <button type="submit" class="btn-primary btn-lg login-submit" :disabled="loading">
            <i class="fa-solid fa-right-to-bracket"></i>
            {{ loading ? t('login.loggingIn') : t('login.submit') }}
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(320px, 0.9fr) 1fr; }

.brand-panel {
  position: relative; display: flex; flex-direction: column; justify-content: space-between;
  padding: 40px 48px 40px 72px; color: #b4cfd1; background-color: #0c3a40;
  background-image: repeating-linear-gradient(to bottom, transparent 0 35px, rgba(255, 255, 255, 0.045) 35px 36px);
}
.brand-panel::before { content: ""; position: absolute; left: 44px; top: 0; bottom: 0; width: 2px; background: var(--accent); opacity: 0.85; }
.brand { display: flex; align-items: center; gap: 12px; color: #fff; font-family: var(--font-display); font-size: 22px; }
.brand-mark { width: 42px; height: 42px; border-radius: 12px; background: var(--accent); color: #2b1d00; display: inline-flex; align-items: center; justify-content: center; font-size: 19px; }
.pitch h2 { color: #fff; font-size: 34px; line-height: 1.15; max-width: 14ch; }
.pitch p { max-width: 38ch; font-size: 15.5px; }

.form-panel { position: relative; display: flex; align-items: center; justify-content: center; padding: 32px; }
.settings { position: absolute; top: 20px; right: 24px; }
.login-box { width: 100%; max-width: 380px; }
.login-box h1 { font-size: 30px; margin-bottom: 6px; }
.login-hint { color: var(--muted); margin: 0 0 26px; }
.login-box form { display: flex; flex-direction: column; gap: 18px; }
.pwd { position: relative; display: flex; }
.pwd input { width: 100%; padding-right: 44px; }
.eye { position: absolute; right: 4px; top: 50%; transform: translateY(-50%); background: transparent; color: var(--muted); padding: 8px 10px; }
.login-submit { justify-content: center; margin-top: 6px; }

@media (max-width: 860px) {
  .login-page { grid-template-columns: 1fr; }
  .brand-panel { padding: 28px 24px 28px 56px; gap: 24px; }
  .brand-panel::before { left: 28px; }
  .pitch h2 { font-size: 26px; max-width: none; }
}
</style>
