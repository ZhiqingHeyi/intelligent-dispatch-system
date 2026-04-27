<template>
  <div class="data-monitor-panel">
    <div class="monitor-title">◆ 实时数据监控 ◆</div>
    <div class="monitor-grid">
      <MonitorCard
        v-for="(stat, index) in stats"
        :key="index"
        :icon="stat.icon"
        :label="stat.label"
        :value="stat.value"
        :color="stat.color"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import MonitorCard from './MonitorCard.vue'

const store = useDispatchStore()

const stats = computed(() => {
  const result: Array<{ icon: 'return' | 'going' | 'active' | 'completed' | 'ai' | 'ai_rate'; label: string; value: number | string; color: string }> = [
    {
      icon: 'return',
      label: '返程缆机',
      value: store.returningCableCars.length,
      color: '#00ff88'
    },
    {
      icon: 'going',
      label: '送料车辆',
      value: store.goingVehicles.length,
      color: '#00d4ff'
    },
    {
      icon: 'active',
      label: '进行中任务',
      value: store.activeTasks.length,
      color: '#ffd93d'
    },
    {
      icon: 'completed',
      label: '今日完成',
      value: store.completedTasks.length,
      color: '#c084fc'
    },
    {
      icon: 'ai',
      label: 'AI调度',
      value: store.aiExperienceSummary?.total ?? 0,
      color: '#00d4ff'
    },
    {
      icon: 'ai_rate',
      label: 'AI成功率',
      value: (store.aiExperienceSummary?.success_rate ?? 0) + '%',
      color: '#00ff88'
    }
  ]
  return result
})
</script>

<style scoped>
.data-monitor-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: clamp(10px, 1vw, 14px);
  padding: clamp(12px, 1.5vh, 16px);
  position: relative;
  overflow: hidden;
}

@media screen and (max-width: 1200px) {
  .data-monitor-panel {
    padding: 12px;
    border-radius: 10px;
  }
}

.data-monitor-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--monitor-radial);
  pointer-events: none;
}

.monitor-title {
  text-align: center;
  font-size: clamp(9px, 0.9vw, 11px);
  color: var(--text-muted);
  letter-spacing: clamp(2px, 0.3vw, 3px);
  margin-bottom: clamp(8px, 1vh, 12px);
  position: relative;
  z-index: 1;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(6px, 0.8vw, 10px);
  position: relative;
  z-index: 1;
}

@media screen and (max-width: 1200px) {
  .monitor-title {
    font-size: 9px;
    margin-bottom: 8px;
    letter-spacing: 2px;
  }
  .monitor-grid {
    gap: 6px;
  }
}
</style>
