<template>
  <div 
    class="vehicle-card"
    :class="{ 
      selected: isSelected,
      delivering: vehicle.state === 'delivering' || vehicle.state === 'delivering_pause',
      returning: vehicle.state === 'returning',
      assigned: vehicle.status === 'assigned'
    }"
    @click="handleClick"
  >
    <div class="card-glow-border"></div>
    
    <div class="vc-top">
      <span class="vc-name">{{ vehicle.name }}</span>
      <span 
        class="vc-status"
        :class="statusClass"
        :style="statusStyle"
      >
        {{ statusLabel }}
      </span>
    </div>
    
    <div class="vc-bottom">
      <span 
        class="vc-grade-badge"
        :class="{ 'no-grade': !grade }"
        :style="grade ? {
          background: grade.color + '18',
          color: grade.color,
          border: '1px solid ' + grade.color + '44'
        } : {}"
        @click.stop="$emit('set-grade')"
      >
        {{ grade ? grade.name : '设置级配' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { Vehicle } from '@/types'

// 方案A：新的状态显示（基于位置+方向+速度）
const STATE_LABELS: Record<string, string> = {
  standby: '待命',           // 接料区/停车区
  delivering: '送料中',      // 送料途中移动
  delivering_pause: '送料暂停', // 送料途中停止
  unloading: '卸料中',       // 卸料区移动
  unloading_wait: '卸料等待', // 卸料区等待
  returning: '返程中',       // 返程
  // 兼容旧状态
  loading: '接料中',
  stopped: '停止'
}

const STATE_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  standby: { bg: 'rgba(255,217,61,0.12)', color: '#ffd93d', border: 'rgba(255,217,61,0.3)' },          // 黄色 - 待命
  delivering: { bg: 'rgba(0,212,255,0.12)', color: '#00d4ff', border: 'rgba(0,212,255,0.3)' },       // 蓝色 - 送料中
  delivering_pause: { bg: 'rgba(90,140,255,0.12)', color: '#5a8cff', border: 'rgba(90,140,255,0.3)' }, // 浅蓝 - 送料暂停
  unloading: { bg: 'rgba(255,107,107,0.12)', color: '#ff6b6b', border: 'rgba(255,107,107,0.3)' },    // 红色 - 卸料中
  unloading_wait: { bg: 'rgba(255,159,159,0.12)', color: '#ff9f9f', border: 'rgba(255,159,159,0.3)' }, // 粉红 - 卸料等待
  returning: { bg: 'var(--accent-green-bg)', color: 'var(--accent-green)', border: 'var(--accent-green-border)' }, // 绿色 - 返程
  // 兼容旧状态
  loading: { bg: 'rgba(255,217,61,0.12)', color: '#ffd93d', border: 'rgba(255,217,61,0.3)' },
  stopped: { bg: 'var(--bg-subtle)', color: 'var(--text-muted)', border: 'var(--border-subtle)' }
}

const props = defineProps<{
  vehicle: Vehicle
  isSelected: boolean
}>()

const emit = defineEmits<{
  select: []
  'set-grade': []
}>()

const store = useDispatchStore()

const grade = computed(() => store.grades.find(g => g.id === props.vehicle.grade_id))

const statusLabel = computed(() => {
  if (props.vehicle.status === 'assigned') return '已调度'
  // 优先使用后端返回的 state_label
  if (props.vehicle.state_label) return props.vehicle.state_label
  // 其次使用 state 映射
  if (props.vehicle.state && STATE_LABELS[props.vehicle.state]) {
    return STATE_LABELS[props.vehicle.state]
  }
  return '待命'
})

const statusClass = computed(() => {
  const s = props.vehicle.status
  const st = props.vehicle.state
  if (s === 'assigned') return 'assigned'
  // 基于新的 state 值返回 class
  if (st) return st
  return 'standby'
})

const statusStyle = computed(() => {
  if (props.vehicle.status === 'assigned') {
    return {
      background: 'var(--accent-purple-bg)',
      color: 'var(--accent-purple)',
      border: '1px solid var(--accent-purple-border)'
    }
  }
  const st = props.vehicle.state
  if (st && STATE_COLORS[st]) {
    const s = STATE_COLORS[st]
    return { background: s.bg, color: s.color, border: `1px solid ${s.border}` }
  }
  // 默认样式
  return {
    background: 'var(--bg-subtle)',
    color: 'var(--text-muted)',
    border: '1px solid var(--border-subtle)'
  }
})

const handleClick = () => {
  if (props.vehicle.status === 'assigned') return
  emit('select')
}
</script>

<style scoped>
.vehicle-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: clamp(8px, 1vw, 10px);
  padding: clamp(8px, 1.2vh, 12px);
  backdrop-filter: blur(10px);
  transition: all 0.25s ease;
  cursor: pointer;
  min-width: 0;
}

@media screen and (max-width: 1200px) {
  .vehicle-card {
    padding: 8px;
    border-radius: 8px;
  }
}

.vehicle-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--shadow-color);
}

.vehicle-card.selected {
  border-color: var(--accent-blue);
  box-shadow: 0 0 20px var(--accent-blue-bg);
}

/* 方案A：新的状态样式 */
.vehicle-card.standby {
  border-color: rgba(255,217,61,0.4);
}

.vehicle-card.delivering {
  border-color: var(--accent-blue-border-hover);
  animation: delivering-pulse 2s ease-in-out infinite;
}

.vehicle-card.delivering_pause {
  border-color: rgba(90,140,255,0.4);
}

.vehicle-card.unloading {
  border-color: rgba(255,107,107,0.4);
}

.vehicle-card.unloading_wait {
  border-color: rgba(255,159,159,0.4);
}

.vehicle-card.returning {
  border-color: var(--accent-green-border);
}

/* 送料中状态样式 */
.vehicle-card.delivering {
  border-color: var(--accent-blue-border-hover);
  animation: delivering-pulse 2s ease-in-out infinite;
}

.vehicle-card.assigned {
  border-color: var(--accent-purple-border);
  opacity: 0.75;
  cursor: not-allowed;
}

@keyframes delivering-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--accent-blue-bg); }
  50% { box-shadow: 0 0 12px 2px var(--accent-blue-bg); }
}

.card-glow-border {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 10px;
  background: var(--glow-border);
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.vehicle-card:hover .card-glow-border {
  opacity: 1;
}

.vc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 8px;
}

.vc-name {
  font-size: clamp(11px, 1vw, 13px);
  font-weight: 600;
  color: var(--text-primary);
}

.vc-status {
  font-size: clamp(9px, 0.8vw, 10px);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

@media screen and (max-width: 1200px) {
  .vc-name {
    font-size: 11px;
  }
  .vc-status {
    font-size: 9px;
    padding: 2px 5px;
  }
}

.vc-bottom {
  display: flex;
  align-items: center;
}

.vc-grade-badge {
  font-size: clamp(9px, 0.8vw, 10px);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

@media screen and (max-width: 1200px) {
  .vc-grade-badge {
    font-size: 9px;
    padding: 2px 5px;
  }
}

.vc-grade-badge:hover {
  filter: brightness(1.3);
  transform: scale(1.05);
}

.vc-grade-badge.no-grade {
  background: var(--grade-no-bg);
  color: var(--text-muted);
  border: 1px dashed var(--text-muted);
}

.vc-grade-badge.no-grade:hover {
  background: var(--bg-subtle-hover);
}
</style>
