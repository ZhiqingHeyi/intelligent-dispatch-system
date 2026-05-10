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
          <div class="mc-match-status">
            缆机送料或车辆返程后自动完成
          </div>
        </div>
      </div>
    </div>

    <!-- 双向匹配等待区 -->
    <div v-if="waitingCars.length > 0 || waitingVehicles.length > 0" class="mc-section">
      <div class="mc-section-title">
        <span class="mc-dot yellow"></span>等待匹配
      </div>
      <div class="mc-bidirectional">
        <!-- 左列：缆机等车 -->
        <div class="mc-bd-column" v-if="waitingCars.length > 0">
          <div class="mc-bd-header">
            <span class="mc-bd-header-icon">🏗️</span>
            <span>缆机等车</span>
          </div>
          <div class="mc-bd-list">
            <div
              v-for="car in waitingCars"
              :key="'car-' + car.id"
              class="mc-bd-item car-waiting"
            >
              <div class="mc-bd-item-top">
                <span class="mc-bd-item-id">{{ car.id }}号</span>
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
              </div>
              <div class="mc-bd-item-sub">
                可匹配车辆: {{ getMatchingVehiclesForCar(car).length > 0 ? getMatchingVehiclesForCar(car).map(v => v.name).join(', ') : '暂无' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 中间连接线 -->
        <div class="mc-bd-connector" v-if="waitingCars.length > 0 && waitingVehicles.length > 0">
          <div class="mc-bd-line"></div>
          <div class="mc-bd-arrows">
            <span class="mc-bd-arrow-left">◀</span>
            <span class="mc-bd-arrow-right">▶</span>
          </div>
        </div>

        <!-- 右列：车辆等缆机 -->
        <div class="mc-bd-column" v-if="waitingVehicles.length > 0">
          <div class="mc-bd-header">
            <span class="mc-bd-header-icon">🚛</span>
            <span>车辆等缆机</span>
          </div>
          <div class="mc-bd-list">
            <div
              v-for="v in waitingVehicles"
              :key="'v-' + v.id"
              class="mc-bd-item vehicle-waiting"
            >
              <div class="mc-bd-item-top">
                <span class="mc-bd-item-id">{{ v.name }}</span>
                <span
                  v-if="getVehicleGrade(v)"
                  class="mc-grade-tag"
                  :style="{
                    background: getVehicleGrade(v)!.color + '18',
                    color: getVehicleGrade(v)!.color,
                    border: '1px solid ' + getVehicleGrade(v)!.color + '44'
                  }"
                >
                  {{ getVehicleGrade(v)!.name }}
                </span>
              </div>
              <div class="mc-bd-item-sub">
                可匹配缆机: {{ getMatchingCarsForVehicle(v).length > 0 ? getMatchingCarsForVehicle(v).map(c => c.name).join(', ') : '暂无' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待设置级配的缆机 -->
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
              <span class="mc-wait-text">已到装料区，请设置级配</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="assignedTasks.length === 0 && waitingCars.length === 0 && waitingVehicles.length === 0 && ungradedCars.length === 0"
      class="mc-empty"
    >
      <div class="mc-empty-icon">📡</div>
      <p>系统正在实时监测中</p>
      <p class="mc-empty-sub">识别到缆机接料或车辆送料后，将自动匹配</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { CableCar, Vehicle } from '@/types'

const store = useDispatchStore()

const assignedTasks = computed(() =>
  store.activeTasks.filter(t => t.status === 'assigned')
)

// 缆机等待区：在装料区接料中 + 有级配 + 未被分配
const waitingCars = computed(() =>
  store.cableCars.filter(c =>
    c.state === 'loading' &&
    c.grade_id > 0 &&
    c.status !== 'assigned'
  )
)

// 车辆等待区：送料途中(going) + 有级配 + 未被分配
const waitingVehicles = computed(() =>
  store.vehicles.filter(v =>
    v.direction === 'going' &&
    v.grade_id > 0 &&
    v.status !== 'assigned'
  )
)

// 未设置级配的缆机：在装料区但没有级配
const ungradedCars = computed(() =>
  store.cableCars.filter(c =>
    c.state === 'loading' &&
    (!c.grade_id || c.grade_id === 0) &&
    c.status !== 'assigned'
  )
)

const gridClass = (count: number) => {
  if (count <= 2) return 'mc-grid-single'
  return 'mc-grid-double'
}

const getCarGrade = (car: CableCar) => {
  return store.grades.find(g => g.id === car.grade_id)
}

const getVehicleGrade = (vehicle: Vehicle) => {
  return store.grades.find(g => g.id === vehicle.grade_id)
}

// 缆机可匹配的车辆
const getMatchingVehiclesForCar = (car: CableCar) => {
  return store.vehicles.filter(
    v => v.grade_id === car.grade_id && v.status !== 'assigned' && v.direction === 'going'
  )
}

// 车辆可匹配的缆机
const getMatchingCarsForVehicle = (vehicle: Vehicle) => {
  return store.cableCars.filter(
    c => c.grade_id === vehicle.grade_id && c.status !== 'assigned' && c.state === 'loading'
  )
}
</script>

<style scoped>
.match-center-content {
  padding: clamp(12px, 1.5vh, 16px) clamp(16px, 1.5vw, 20px);
}

@media screen and (max-width: 1200px) {
  .match-center-content {
    padding: 12px 16px;
  }
}

.mc-title {
  font-size: clamp(13px, 1.4vw, 15px);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: clamp(10px, 1.2vh, 14px);
  letter-spacing: clamp(2px, 0.3vw, 3px);
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
  background: var(--match-card-bg);
  border: 1px solid var(--border-color);
  border-radius: clamp(8px, 1vw, 12px);
  padding: clamp(12px, 1.5vh, 16px) clamp(16px, 1.5vw, 20px);
  transition: all 0.2s ease;
}

.mc-match-card:hover {
  background: var(--match-card-hover-bg);
  transform: translateY(-1px);
}

.mc-match-card.matched {
  border-left: 3px solid var(--accent-green);
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
  background: var(--id-badge-bg);
  border: 1px solid var(--id-badge-border);
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
  background: var(--accent-blue-border);
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.mc-arrow-line.matched {
  background: var(--accent-green-border);
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

/* 双向匹配区域 */
.mc-bidirectional {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.mc-bd-column {
  flex: 1;
  min-width: 0;
}

.mc-bd-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
  justify-content: center;
}

.mc-bd-header-icon {
  font-size: 14px;
}

.mc-bd-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mc-bd-item {
  background: var(--match-card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s ease;
}

.mc-bd-item:hover {
  background: var(--match-card-hover-bg);
}

.mc-bd-item.car-waiting {
  border-left: 3px solid var(--accent-yellow);
}

.mc-bd-item.vehicle-waiting {
  border-left: 3px solid var(--accent-blue);
}

.mc-bd-item-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.mc-bd-item-id {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.mc-bd-item-sub {
  font-size: 11px;
  color: var(--text-muted);
}

/* 中间连接器 */
.mc-bd-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  gap: 4px;
}

.mc-bd-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(180deg, var(--accent-yellow), var(--accent-blue));
  border-radius: 1px;
  opacity: 0.5;
}

.mc-bd-arrows {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: var(--text-muted);
}

.mc-bd-arrow-left {
  color: var(--accent-yellow);
}

.mc-bd-arrow-right {
  color: var(--accent-blue);
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
