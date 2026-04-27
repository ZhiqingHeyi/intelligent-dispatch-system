<template>
  <div class="monitor-card">
    <div 
      class="monitor-icon"
      :style="{
        background: `${color}10`,
        color: color,
        border: `1px solid ${color}20`
      }"
    >
      <svg v-if="icon === 'return'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 14l5-5-5-5"/>
        <path d="M20 9H9.5A5.5 5.5 0 0 0 4 14.5v0A5.5 5.5 0 0 0 9.5 20H13"/>
      </svg>
      <svg v-else-if="icon === 'going'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 14L4 9l5-5"/>
        <path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/>
      </svg>
      <svg v-else-if="icon === 'active'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
      <svg v-else-if="icon === 'ai'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
      <svg v-else-if="icon === 'ai_rate'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 20V10"/>
        <path d="M12 20V4"/>
        <path d="M6 20v-6"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    </div>
    <div class="monitor-info">
      <span class="monitor-label">{{ label }}</span>
      <div class="monitor-value-row">
        <span class="monitor-value" :style="{ color }">{{ value }}</span>
        <Transition name="trend">
          <span 
            v-if="trend" 
            class="monitor-trend"
            :class="trend"
          >
            {{ trend === 'up' ? '▲' : '▼' }}
          </span>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'

const props = defineProps<{
  icon: 'return' | 'going' | 'active' | 'completed' | 'ai' | 'ai_rate'
  label: string
  value: number | string
  color: string
}>()

const trend = ref<'up' | 'down' | null>(null)
let trendTimer: number | null = null

watch(() => props.value, (newVal, oldVal) => {
  if (newVal > (oldVal ?? 0)) {
    trend.value = 'up'
  } else if (newVal < (oldVal ?? 0)) {
    trend.value = 'down'
  }
  
  if (trendTimer) clearTimeout(trendTimer)
  trendTimer = window.setTimeout(() => {
    trend.value = null
  }, 3000)
})
</script>

<style scoped>
.monitor-card {
  display: flex;
  align-items: center;
  gap: clamp(6px, 0.8vw, 10px);
  padding: clamp(8px, 1.2vh, 12px);
  background: var(--bg-subtle);
  border: 1px solid var(--border-subtle);
  border-radius: clamp(8px, 1vw, 10px);
  transition: all 0.2s ease;
}

@media screen and (max-width: 1200px) {
  .monitor-card {
    gap: 6px;
    padding: 8px;
    border-radius: 8px;
  }
}

.monitor-card:hover {
  border-color: var(--accent-blue-border-hover);
  background: var(--bg-subtle-hover);
  transform: translateY(-2px);
}

.monitor-icon {
  width: clamp(28px, 3vw, 36px);
  height: clamp(28px, 3vw, 36px);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.monitor-icon svg {
  width: clamp(16px, 1.8vw, 20px);
  height: clamp(16px, 1.8vw, 20px);
}

@media screen and (max-width: 1200px) {
  .monitor-icon {
    width: 28px;
    height: 28px;
  }
  .monitor-icon svg {
    width: 16px;
    height: 16px;
  }
}

.monitor-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.monitor-label {
  font-size: clamp(9px, 0.8vw, 10px);
  color: var(--text-muted);
  letter-spacing: 1px;
}

.monitor-value-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.monitor-value {
  font-family: 'Orbitron', monospace;
  font-size: clamp(16px, 2vw, 22px);
  font-weight: 700;
  line-height: 1;
}

@media screen and (max-width: 1200px) {
  .monitor-label {
    font-size: 9px;
  }
  .monitor-value {
    font-size: 16px;
  }
}

.monitor-trend {
  font-size: 10px;
  font-weight: 700;
}

.monitor-trend.up {
  color: var(--accent-green);
}

.monitor-trend.down {
  color: var(--accent-red);
}

.trend-enter-active,
.trend-leave-active {
  transition: all 0.3s ease;
}

.trend-enter-from,
.trend-leave-to {
  opacity: 0;
  transform: scale(0.5);
}
</style>
