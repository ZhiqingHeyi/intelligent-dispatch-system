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

const stats = computed(() => [
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
  }
])
</script>

<style scoped>
.data-monitor-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 16px;
  position: relative;
  overflow: hidden;
}

.data-monitor-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.03) 0%, transparent 40%),
    radial-gradient(circle at 80% 50%, rgba(0, 212, 255, 0.03) 0%, transparent 40%);
  pointer-events: none;
}

.monitor-title {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 3px;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  position: relative;
  z-index: 1;
}
</style>
