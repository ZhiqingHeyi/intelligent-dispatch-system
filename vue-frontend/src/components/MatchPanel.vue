<template>
  <div class="panel-center">
    <div class="panel-header">
      <span class="panel-title">◆ 调度匹配</span>
    </div>
    
    <div class="panel-body">
      <!-- 数据监控 -->
      <DataMonitor />
      
      <!-- 匹配区域 -->
      <div class="match-area">
        <div v-if="!store.selectedCableCar" class="match-hint">
          <div class="hint-icon">←</div>
          <p>请先选择一台返程缆机</p>
        </div>
        
        <template v-else>
          <div class="match-selected">
            <span>已选择: {{ selectedCar?.name }}</span>
            <button @click="store.selectCableCar(null)">取消</button>
          </div>
          
          <div v-if="!store.selectedVehicle" class="match-hint">
            <div class="hint-icon">→</div>
            <p>请选择一辆送料车辆</p>
          </div>
          
          <div v-else class="match-action">
            <span>已选择车辆: {{ selectedVehicle?.name }}</span>
            <button @click="createMatch" :disabled="creating">
              {{ creating ? '匹配中...' : '确认匹配' }}
            </button>
          </div>
        </template>
      </div>
      
      <!-- 任务列表 -->
      <TaskList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import DataMonitor from './DataMonitor.vue'
import TaskList from './TaskList.vue'

const store = useDispatchStore()
const creating = ref(false)

const selectedCar = computed(() => 
  store.cableCars.find(c => c.id === store.selectedCableCar)
)

const selectedVehicle = computed(() => 
  store.vehicles.find(v => v.id === store.selectedVehicle)
)

const createMatch = async () => {
  if (!store.selectedCableCar || !store.selectedVehicle) return
  
  const car = selectedCar.value
  const gradeId = car?.grade_id
  
  if (!gradeId) {
    alert('请先为缆机设置级配')
    return
  }
  
  creating.value = true
  const result = await store.createTask(
    store.selectedCableCar,
    store.selectedVehicle,
    gradeId
  )
  creating.value = false
  
  if (result.success) {
    alert('匹配成功')
  } else {
    alert('匹配失败')
  }
}
</script>

<style scoped>
.panel-center {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 0 6px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.match-area {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.match-hint {
  text-align: center;
  color: var(--text-muted);
}

.hint-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.match-selected,
.match-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.match-selected button,
.match-action button {
  padding: 8px 24px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  border: none;
  border-radius: 6px;
  color: #000;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.match-selected button:hover,
.match-action button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.3);
}

.match-selected button:disabled,
.match-action button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
</style>
