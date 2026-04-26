<template>
  <div class="match-center-content">
    <div class="mc-title">智能匹配状态</div>

    <!-- 当前匹配中 -->
    <div v-if="assignedTasks.length > 0" class="mc-section">
      <div class="mc-section-title">
        <span class="mc-dot green"></span>当前匹配中
      </div>
      <div class="mc-grid" :class="gridClass(assignedTasks.length)">
        <div
          v-for="task in assignedTasks"
          :key="task.id"
          class="mc-match-card matched"
        >
          <div class="mc-match-row">
            <div class="mc-entity">
              <span class="mc-entity-icon car-icon">{{ task.cable_car_id }}</span>
              <span class="mc-entity-name">{{ task.cable_car_name }}</span>
            </div>
            <div class="mc-match-arrow">
              <div class="mc-arrow-line matched">
                <div class="mc-arrow-particle"></div>
              </div>
              <span
                v-if="task.grade_name"
                class="mc-arrow-label"
                :style="{ color: task.grade_color }"
              >
                {{ task.grade_name }}
              </span>
            </div>
            <div class="mc-entity">
              <span class="mc-entity-icon vehicle-icon">🚛</span>
              <span class="mc-entity-name">{{ task.vehicle_name }}</span>
            </div>
          </div>
          <div class="mc-match-status">车辆送料中，等待返程自动完成...</div>
        </div>
      </div>
    </div>

    <!-- 等待匹配车辆 -->
    <div v-if="waitingCars.length > 0" class="mc-section">
      <div class="mc-section-title">
        <span class="mc-dot yellow"></span>等待匹配车辆
      </div>
      <div class="mc-grid" :class="gridClass(waitingCars.length)">
        <div
          v-for="car in waitingCars"
          :key="car.id"
          class="mc-match-card waiting"
        >
          <div class="mc-match-row">
            <div class="mc-entity">
              <span class="mc-entity-icon car-icon">{{ car.id }}</span>
              <span class="mc-entity-name">{{ car.name }}</span>
            </div>
            <div class="mc-match-info">
              <span
                v-if="getCarGrade(car)"
                class="mc-grade-tag"
                :style="{
                  background: getCarGrade(car)!.color + '18',
                  color: getCarGrade(car)!.color,
                  border: '1px solid ' + getCarGrade(car)!.color + '44'
                }"
              >
                {{ getCarGrade(car)!.name }}
              </span>
              <span class="mc-wait-text">等待同级配车辆送料</span>
            </div>
          </div>
          <div class="mc-match-sub">
            匹配车辆: {{ getMatchingVehicles(car).length > 0 ? getMatchingVehicles(car).map(v => v.name).join(', ') : '暂无' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 待设置级配 -->
    <div v-if="ungradedCars.length > 0" class="mc-section">
      <div class="mc-section-title">
        <span class="mc-dot gray"></span>待设置级配
      </div>
      <div class="mc-grid" :class="gridClass(ungradedCars.length)">
        <div
          v-for="car in ungradedCars"
          :key="car.id"
          class="mc-match-card ungraded"
        >
          <div class="mc-match-row">
            <div class="mc-entity">
              <span class="mc-entity-icon car-icon">{{ car.id }}</span>
              <span class="mc-entity-name">{{ car.name }}</span>
            </div>
            <div class="mc-match-info">
              <span class="mc-wait-text">返程中，请设置级配</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="assignedTasks.length === 0 && waitingCars.length === 0 && ungradedCars.length === 0"
      class="mc-empty"
    >
      <div class="mc-empty-icon">📡</div>
      <p>系统正在实时监测中</p>
      <p class="mc-empty-sub">识别到缆机返程且设置级配后，将自动匹配送料车辆</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { CableCar } from '@/types'

const store = useDispatchStore()

const assignedTasks = computed(() =>
  store.activeTasks.filter(t => t.status === 'assigned')
)

const returningCars = computed(() =>
  store.cableCars.filter(c => c.direction === 'returning' && c.status === 'returning')
)

const waitingCars = computed(() =>
  returningCars.value.filter(c => c.grade_id > 0)
)

const ungradedCars = computed(() =>
  returningCars.value.filter(c => !c.grade_id || c.grade_id === 0)
)

const gridClass = (count: number) => {
  if (count <= 2) return 'mc-grid-single'
  return 'mc-grid-double'
}

const getCarGrade = (car: CableCar) => {
  return store.grades.find(g => g.id === car.grade_id)
}

const getMatchingVehicles = (car: CableCar) => {
  return store.vehicles.filter(
    v => v.grade_id === car.grade_id && v.status !== 'assigned' && v.direction === 'going'
  )
}
</script>

<style scoped>
.match-center-content {
  padding: 16px 20px;
}

.mc-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 14px;
  letter-spacing: 3px;
}

.mc-section {
  margin-bottom: 14px;
}

.mc-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  font-weight: 500;
}

.mc-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.mc-dot.green {
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
}

.mc-dot.yellow {
  background: var(--accent-yellow);
  box-shadow: 0 0 6px var(--accent-yellow);
}

.mc-dot.gray {
  background: var(--text-muted);
}

/* 响应式网格 */
.mc-grid {
  display: grid;
  gap: 10px;
}

.mc-grid-single {
  grid-template-columns: 1fr;
}

.mc-grid-double {
  grid-template-columns: 1fr 1fr;
}

.mc-match-card {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  transition: all 0.2s ease;
}

.mc-match-card:hover {
  background: rgba(0, 0, 0, 0.35);
  transform: translateY(-1px);
}

.mc-match-card.matched {
  border-left: 3px solid var(--accent-green);
}

.mc-match-card.waiting {
  border-left: 3px solid var(--accent-yellow);
}

.mc-match-card.ungraded {
  border-left: 3px solid var(--text-muted);
  opacity: 0.7;
}

.mc-match-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mc-entity {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 90px;
}

.mc-entity-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.mc-entity-icon.car-icon {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 136, 0.1));
  border: 1px solid rgba(0, 212, 255, 0.3);
  color: var(--accent-blue);
}

.mc-entity-icon.vehicle-icon {
  background: none;
  font-size: 22px;
}

.mc-entity-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.mc-match-arrow {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.mc-arrow-line {
  width: 100%;
  height: 2px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.mc-arrow-line.matched {
  background: rgba(0, 255, 136, 0.3);
}

.mc-arrow-particle {
  position: absolute;
  top: 0;
  left: -30%;
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, transparent, var(--accent-green), transparent);
  animation: arrow-flow 2s linear infinite;
}

@keyframes arrow-flow {
  0% { left: -30%; }
  100% { left: 100%; }
}

.mc-arrow-label {
  font-size: 11px;
  font-weight: 500;
}

.mc-match-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.mc-grade-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.mc-wait-text {
  font-size: 12px;
  color: var(--text-muted);
}

.mc-match-status {
  margin-top: 10px;
  font-size: 12px;
  color: var(--accent-green);
  text-align: center;
  opacity: 0.8;
}

.mc-match-sub {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}

.mc-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.mc-empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.mc-empty p {
  font-size: 14px;
  margin-bottom: 6px;
}

.mc-empty-sub {
  font-size: 12px;
  opacity: 0.6;
}
</style>
