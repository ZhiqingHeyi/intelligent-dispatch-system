import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CableCar, Vehicle, Grade, Task, ManualState, StateType } from '@/types'
import { STATE_CONFIG } from '@/types'
import * as api from '@/api/dispatch'

export const useDispatchStore = defineStore('dispatch', () => {
  // State
  const cableCars = ref<CableCar[]>([])
  const vehicles = ref<Vehicle[]>([])
  const grades = ref<Grade[]>([])
  const activeTasks = ref<Task[]>([])
  const recentTasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 选中的缆机和车辆
  const selectedCableCar = ref<number | null>(null)
  const selectedVehicle = ref<number | null>(null)

  // Getters
  const returningCableCars = computed(() => 
    cableCars.value.filter(c => c.direction === 'returning' || c.state === 'returning')
  )
  
  const goingVehicles = computed(() => 
    vehicles.value.filter(v => v.direction === 'going')
  )
  
  const completedTasks = computed(() => 
    recentTasks.value.filter(t => t.status === 'completed')
  )

  // 获取缆机的显示状态
  const getCableCarDisplayState = (car: CableCar) => {
    const manualState = car.manual_state as ManualState
    const autoState = car.state || car.direction as StateType
    
    if (manualState && manualState !== 'normal' && STATE_CONFIG[manualState]) {
      return {
        state: manualState,
        ...STATE_CONFIG[manualState]
      }
    } else if (autoState && STATE_CONFIG[autoState]) {
      return {
        state: autoState,
        ...STATE_CONFIG[autoState]
      }
    }
    
    return {
      state: 'normal' as StateType,
      ...STATE_CONFIG.normal
    }
  }

  // Actions
  const fetchData = async () => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await api.fetchStatus()
      cableCars.value = data.cable_cars
      vehicles.value = data.vehicles
      grades.value = data.grades
      activeTasks.value = data.active_tasks
      recentTasks.value = data.recent_tasks
    } catch (e) {
      error.value = '数据同步失败'
      console.error('Fetch data error:', e)
    } finally {
      loading.value = false
    }
  }

  // 乐观更新：设置缆机状态
  const setCableCarState = async (carId: number, manualState: ManualState) => {
    const carIndex = cableCars.value.findIndex(c => c.id === carId)
    if (carIndex === -1) return { success: false, message: '缆机不存在' }
    
    // 保存原始状态用于回滚
    const originalState = cableCars.value[carIndex].manual_state
    
    // 乐观更新本地状态
    cableCars.value[carIndex].manual_state = manualState
    
    try {
      await api.setCableCarState(carId, manualState)
      return { success: true }
    } catch (e) {
      // 回滚
      cableCars.value[carIndex].manual_state = originalState
      console.error('Set state error:', e)
      return { success: false, message: '服务器更新失败' }
    }
  }

  // 设置缆机级配
  const setCableCarGrade = async (carId: number, gradeId: number) => {
    const carIndex = cableCars.value.findIndex(c => c.id === carId)
    if (carIndex === -1) return { success: false }
    
    const originalGrade = cableCars.value[carIndex].grade_id
    cableCars.value[carIndex].grade_id = gradeId
    
    try {
      await api.setCableCarGrade(carId, gradeId)
      return { success: true }
    } catch (e) {
      cableCars.value[carIndex].grade_id = originalGrade
      return { success: false }
    }
  }

  // 创建任务
  const createTask = async (cableCarId: number, vehicleId: number, gradeId: number) => {
    try {
      await api.createTask(cableCarId, vehicleId, gradeId)
      await fetchData()
      selectedCableCar.value = null
      selectedVehicle.value = null
      return { success: true }
    } catch (e) {
      console.error('Create task error:', e)
      return { success: false }
    }
  }

  // 选择缆机
  const selectCableCar = (id: number | null) => {
    selectedCableCar.value = id
  }

  // 选择车辆
  const selectVehicle = (id: number | null) => {
    selectedVehicle.value = id
  }

  return {
    // State
    cableCars,
    vehicles,
    grades,
    activeTasks,
    recentTasks,
    loading,
    error,
    selectedCableCar,
    selectedVehicle,
    // Getters
    returningCableCars,
    goingVehicles,
    completedTasks,
    getCableCarDisplayState,
    // Actions
    fetchData,
    setCableCarState,
    setCableCarGrade,
    createTask,
    selectCableCar,
    selectVehicle,
  }
})
