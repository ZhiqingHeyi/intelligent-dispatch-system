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
  icon: 'return' | 'going' | 'active' | 'completed'
  label: string
  value: number
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
  gap: 10px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.monitor-card:hover {
  border-color: rgba(0, 212, 255, 0.25);
  background: rgba(0, 0, 0, 0.3);
  transform: translateY(-2px);
}

.monitor-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.monitor-icon svg {
  width: 20px;
  height: 20px;
}

.monitor-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.monitor-label {
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.monitor-value-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.monitor-value {
  font-family: 'Orbitron', monospace;
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
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
