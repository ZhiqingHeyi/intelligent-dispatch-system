<template>
  <div 
    class="cable-car-card"
    :class="[displayState.state, { selected: isSelected }]"
    @click="$emit('select')"
  >
    <div class="card-glow-border"></div>
    
    <!-- 顶部：名称和状态 -->
    <div class="cc-top">
      <div class="cc-name-row">
        <span class="cc-id-badge">{{ car.id }}</span>
        <span class="cc-name">{{ car.name }}</span>
      </div>
      <span 
        class="cc-direction"
        :class="displayState.state"
        :style="{
          background: `${displayState.color}18`,
          color: displayState.color,
          border: `1px solid ${displayState.color}44`
        }"
      >
        {{ displayState.label }}
      </span>
    </div>
    
    <!-- 中间：位置信息 -->
    <div class="cc-info">
      <div class="cc-info-item">
        <span class="label">位置区域</span>
        <span class="value">{{ car.location || '-' }}</span>
      </div>
      <div class="cc-info-item">
        <span class="label">X坐标</span>
        <span class="value">{{ car.latitude?.toFixed(1) || '-' }}</span>
      </div>
      <div class="cc-info-item">
        <span class="label">Y坐标</span>
        <span class="value">{{ car.longitude?.toFixed(1) || '-' }}</span>
      </div>
      <div class="cc-info-item">
        <span class="label">X速度</span>
        <span class="value" :class="{ neg: car.xspeed < 0 }">
          {{ car.xspeed?.toFixed(2) || '0.00' }}
        </span>
      </div>
    </div>
    
    <!-- 底部：级配和状态 -->
    <div class="cc-grade">
      <span class="cc-grade-label">级配:</span>
      <span 
        class="cc-grade-badge"
        :class="{ 'no-grade': !grade }"
        :style="grade ? {
          background: `${grade.color}18`,
          color: grade.color,
          border: `1px solid ${grade.color}44`
        } : {}"
        @click.stop="$emit('set-grade')"
      >
        {{ grade ? grade.name : '点击设置' }}
      </span>
      <div class="flex-spacer"></div>
      <span 
        class="cc-state-indicator"
        :class="displayState.state"
        :style="{
          background: `${displayState.color}15`,
          color: displayState.color,
          border: `1px solid ${displayState.color}30`
        }"
      >
        {{ displayState.label }}
      </span>
      <span 
        class="cc-grade-badge state-btn"
        @click.stop="$emit('set-state')"
      >
        设置状态
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { CableCar } from '@/types'

const props = defineProps<{
  car: CableCar
  isSelected: boolean
}>()

defineEmits<{
  select: []
  'set-grade': []
  'set-state': []
}>()

const store = useDispatchStore()

const displayState = computed(() => store.getCableCarDisplayState(props.car))

const grade = computed(() => store.grades.find(g => g.id === props.car.grade_id))
</script>

<style scoped>
.cable-car-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  backdrop-filter: blur(10px);
  transition: all 0.25s ease;
  cursor: pointer;
}

.cable-car-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.cable-car-card.selected {
  border-color: var(--accent-blue);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);
}

/* 状态边框色 */
.cable-car-card.normal { border-color: rgba(0, 255, 136, 0.35); }
.cable-car-card.rest { border-color: rgba(192, 132, 252, 0.35); }
.cable-car-card.other { border-color: rgba(136, 136, 136, 0.35); }
.cable-car-card.loading { border-color: rgba(255, 217, 61, 0.35); }
.cable-car-card.delivering { border-color: rgba(0, 212, 255, 0.35); }
.cable-car-card.unloading { border-color: rgba(255, 107, 107, 0.35); }
.cable-car-card.returning { border-color: rgba(0, 255, 136, 0.35); }

.card-glow-border {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), transparent, rgba(0, 255, 136, 0.1));
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cable-car-card:hover .card-glow-border {
  opacity: 1;
}

.cc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.cc-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cc-id-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 136, 0.1));
  border: 1px solid rgba(0, 212, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Orbitron', monospace;
  font-size: 13px;
  font-weight: 700;
  color: var(--accent-blue);
}

.cc-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.cc-direction {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
  letter-spacing: 1px;
}

.cc-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.cc-info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.cc-info-item .label {
  color: var(--text-muted);
}

.cc-info-item .value {
  color: var(--text-primary);
  font-weight: 500;
}

.cc-info-item .value.neg {
  color: var(--accent-green);
}

.cc-grade {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(30, 58, 110, 0.3);
}

.cc-grade-label {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.cc-grade-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  white-space: nowrap;
}

.cc-grade-badge:hover {
  filter: brightness(1.3);
  transform: scale(1.05);
}

.cc-grade-badge.no-grade {
  background: rgba(74, 82, 112, 0.1);
  color: var(--text-muted);
  border: 1px dashed var(--text-muted);
}

.cc-grade-badge.state-btn {
  background: rgba(100, 100, 100, 0.1);
  color: #888;
  border: 1px solid rgba(100, 100, 100, 0.3);
  margin-left: 4px;
}

.cc-grade-badge.state-btn:hover {
  background: rgba(100, 100, 100, 0.2);
}

.flex-spacer {
  flex: 1;
}

.cc-state-indicator {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}
</style>
