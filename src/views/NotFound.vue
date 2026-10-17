<script setup>
import { useI18n } from 'vue-i18n'
import EmptyState from '../components/EmptyState.vue'

const { t } = useI18n()
</script>

<template>
  <div class="container container-narrow">
    <div class="card">
      <EmptyState icon="fa-compass" :title="t('notFound.heading')" :text="t('notFound.text')">
        <router-link to="/" class="btn btn-primary"><i class="fa-solid fa-house"></i> {{ t('nav.home') }}</router-link>
      </EmptyState>
    </div>
  </div>
</template>
