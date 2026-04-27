import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'dark' | 'light'

export const useThemeStore = defineStore('theme', () => {
  const savedTheme = localStorage.getItem('dispatch-theme') as ThemeMode | null
  const theme = ref<ThemeMode>(savedTheme || 'dark')

  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  const setTheme = (mode: ThemeMode) => {
    theme.value = mode
  }

  const isDark = ref(theme.value === 'dark')

  watch(theme, (val) => {
    isDark.value = val === 'dark'
    localStorage.setItem('dispatch-theme', val)
    document.documentElement.setAttribute('data-theme', val)
  }, { immediate: true })

  return {
    theme,
    isDark,
    toggleTheme,
    setTheme,
  }
})
