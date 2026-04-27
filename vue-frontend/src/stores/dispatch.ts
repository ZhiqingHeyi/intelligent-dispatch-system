import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CableCar, Vehicle, Grade, Task, ManualState, StateType, AiConfig, AiChatMessage, AiSchedulerStatus, AiExperienceSummary } from '@/types'
import { STATE_CONFIG } from '@/types'
import * as api from '@/api/dispatch'

export const useDispatchStore = defineStore('dispatch', () => {
  const cableCars = ref<CableCar[]>([])
  const vehicles = ref<Vehicle[]>([])
  const grades = ref<Grade[]>([])
  const activeTasks = ref<Task[]>([])
  const recentTasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastSyncTime = ref<number>(Date.now())
  
  const selectedCableCar = ref<number | null>(null)
  const selectedVehicle = ref<number | null>(null)

  const aiConfig = ref<AiConfig>({
    api_url: 'https://api.openai.com/v1/chat/completions',
    api_key: '',
    model: 'gpt-4o',
    temperature: 0.3,
    max_tokens: 2048,
    enabled: false,
    auto_dispatch_enabled: false,
    dispatch_interval: 180,
  })

  const aiChatMessages = ref<AiChatMessage[]>([])
  const aiChatLoading = ref(false)
  const aiSchedulerStatus = ref<AiSchedulerStatus | null>(null)
  const aiExperienceSummary = ref<AiExperienceSummary | null>(null)
  const aiPanelOpen = ref(false)
  const aiConfigModalOpen = ref(false)

  const returningCableCars = computed(() => 
    cableCars.value.filter(c => c.direction === 'returning' || c.state === 'returning')
  )
  
  const goingVehicles = computed(() => 
    vehicles.value.filter(v => v.direction === 'going')
  )
  
  const completedTasks = computed(() => 
    recentTasks.value.filter(t => t.status === 'completed')
  )

  const getCableCarDisplayState = (car: CableCar) => {
    const manualState = car.manual_state as ManualState
    const autoState = (car.state || car.direction) as StateType
    
    if (manualState && manualState !== 'normal' && STATE_CONFIG[manualState]) {
      return {
        state: manualState,
        ...STATE_CONFIG[manualState]
      }
    }
    
    if (autoState && STATE_CONFIG[autoState as StateType]) {
      return {
        state: autoState as StateType,
        ...STATE_CONFIG[autoState as StateType]
      }
    }
    
    return {
      state: 'returning' as StateType,
      ...STATE_CONFIG.returning
    }
  }

  const aiApiConfigured = computed(() => !!aiConfig.value.api_key_configured || !!aiConfig.value.api_key)

  const fetchData = async () => {
    loading.value = true
    
    try {
      const { data } = await api.fetchStatus()
      cableCars.value = data.cable_cars
      vehicles.value = data.vehicles
      grades.value = data.grades
      activeTasks.value = data.active_tasks
      recentTasks.value = data.recent_tasks
      error.value = null
      lastSyncTime.value = Date.now()
    } catch (e) {
      error.value = '数据同步失败'
      console.error('Fetch data error:', e)
    } finally {
      loading.value = false
    }
  }

  const setCableCarState = async (carId: number, manualState: ManualState) => {
    const carIndex = cableCars.value.findIndex(c => c.id === carId)
    if (carIndex === -1) return { success: false, message: '缆机不存在' }
    
    const originalState = cableCars.value[carIndex].manual_state
    cableCars.value[carIndex].manual_state = manualState
    
    try {
      await api.setCableCarState(carId, manualState)
      return { success: true }
    } catch (e) {
      cableCars.value[carIndex].manual_state = originalState
      console.error('Set state error:', e)
      return { success: false, message: '服务器更新失败' }
    }
  }

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

  const setVehicleGrade = async (vehicleId: number, gradeId: number) => {
    const vehicleIndex = vehicles.value.findIndex(v => v.id === vehicleId)
    if (vehicleIndex === -1) return { success: false }
    
    const originalGrade = vehicles.value[vehicleIndex].grade_id
    vehicles.value[vehicleIndex].grade_id = gradeId
    
    try {
      await api.setVehicleGrade(vehicleId, gradeId)
      return { success: true }
    } catch (e) {
      vehicles.value[vehicleIndex].grade_id = originalGrade
      return { success: false }
    }
  }

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

  const selectCableCar = (id: number | null) => {
    if (id !== null && selectedCableCar.value === id) {
      selectedCableCar.value = null
    } else {
      selectedCableCar.value = id
    }
    selectedVehicle.value = null
  }

  const selectVehicle = (id: number | null) => {
    const vehicle = vehicles.value.find(v => v.id === id)
    if (vehicle && vehicle.status === 'assigned') return
    
    if (id !== null && selectedVehicle.value === id) {
      selectedVehicle.value = null
    } else {
      selectedVehicle.value = id
    }
  }

  const fetchAiConfig = async () => {
    try {
      const { data } = await api.getAiConfig()
      if (data.success && data.config) {
        aiConfig.value = { ...aiConfig.value, ...data.config }
      }
    } catch (e) {
      console.error('Fetch AI config error:', e)
    }
  }

  const saveAiConfigAction = async (config: Partial<AiConfig>) => {
    try {
      const { data } = await api.saveAiConfig(config)
      if (data.success) {
        await fetchAiConfig()
      }
      return { success: data.success, message: data.message, verified: data.verified }
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '保存失败'
      return { success: false, message: msg }
    }
  }

  const sendAiChat = async (message: string) => {
    aiChatLoading.value = true
    const userMsg: AiChatMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      created_at: new Date().toLocaleString('zh-CN')
    }
    aiChatMessages.value.push(userMsg)

    try {
      const { data } = await api.aiChat(message)
      const assistantMsg: AiChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        tool_results: data.tool_results || [],
        created_at: new Date().toLocaleString('zh-CN')
      }
      aiChatMessages.value.push(assistantMsg)
      if ((data as any).error_type === 'config_missing') {
        aiConfigModalOpen.value = true
      }
      await fetchData()
      return { success: data.success }
    } catch (e: any) {
      let errorMsg = '⚠️ AI服务连接失败'
      if (e?.response) {
        const detail = e?.response?.data?.response || e?.response?.data?.message
        if (detail) errorMsg = detail
      }
      const msg: AiChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: errorMsg,
        tool_results: [],
        created_at: new Date().toLocaleString('zh-CN')
      }
      aiChatMessages.value.push(msg)
      return { success: false }
    } finally {
      aiChatLoading.value = false
    }
  }

  const triggerAiDispatch = async () => {
    aiChatLoading.value = true
    const userMsg: AiChatMessage = {
      id: Date.now(),
      role: 'user',
      content: '🔄 执行智能调度',
      created_at: new Date().toLocaleString('zh-CN')
    }
    aiChatMessages.value.push(userMsg)

    try {
      const { data } = await api.aiDispatch()
      const assistantMsg: AiChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        tool_results: data.tool_results || [],
        created_at: new Date().toLocaleString('zh-CN')
      }
      aiChatMessages.value.push(assistantMsg)
      if ((data as any).error_type === 'config_missing') {
        aiConfigModalOpen.value = true
      }
      await fetchData()
      return { success: data.success }
    } catch (e: any) {
      let errorMsg = '⚠️ AI调度执行失败'
      if (e?.response) {
        const detail = e?.response?.data?.response || e?.response?.data?.message
        if (detail) {
          errorMsg = detail
        }
      }
      const msg: AiChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: errorMsg + '\n\n💡 建议: 点击⚙按钮检查AI模型配置是否正确',
        created_at: new Date().toLocaleString('zh-CN')
      }
      aiChatMessages.value.push(msg)
      return { success: false }
    } finally {
      aiChatLoading.value = false
    }
  }

  const fetchAiChatHistory = async () => {
    try {
      const { data } = await api.getAiChatHistory()
      if (data.success && data.history) {
        aiChatMessages.value = data.history
      }
    } catch (e) {
      console.error('Fetch chat history error:', e)
    }
  }

  const clearAiChatHistoryAction = async () => {
    try {
      await api.clearAiChatHistory()
      aiChatMessages.value = []
    } catch (e) {
      console.error('Clear chat history error:', e)
    }
  }

  const fetchAiScheduler = async () => {
    try {
      const { data } = await api.getAiScheduler()
      if (data.success && data.status) {
        aiSchedulerStatus.value = data.status
      }
    } catch (e) {
      console.error('Fetch AI scheduler error:', e)
    }
  }

  const startAiSchedulerAction = async () => {
    try {
      const { data } = await api.startAiScheduler()
      await fetchAiScheduler()
      return data
    } catch (e) {
      console.error('Start AI scheduler error:', e)
      return { success: false, message: '启动失败' }
    }
  }

  const stopAiSchedulerAction = async () => {
    try {
      const { data } = await api.stopAiScheduler()
      await fetchAiScheduler()
      return data
    } catch (e) {
      console.error('Stop AI scheduler error:', e)
      return { success: false, message: '停止失败' }
    }
  }

  const fetchAiExperience = async () => {
    try {
      const { data } = await api.getAiExperience({ limit: 5 })
      if (data.success && data.summary) {
        aiExperienceSummary.value = data.summary
      }
    } catch (e) {
      console.error('Fetch AI experience error:', e)
    }
  }

  const toggleAiPanel = () => {
    aiPanelOpen.value = !aiPanelOpen.value
  }

  return {
    cableCars,
    vehicles,
    grades,
    activeTasks,
    recentTasks,
    loading,
    error,
    lastSyncTime,
    selectedCableCar,
    selectedVehicle,
    aiConfig,
    aiChatMessages,
    aiChatLoading,
    aiSchedulerStatus,
    aiExperienceSummary,
    aiPanelOpen,
    aiConfigModalOpen,
    returningCableCars,
    goingVehicles,
    completedTasks,
    getCableCarDisplayState,
    aiApiConfigured,
    fetchData,
    setCableCarState,
    setCableCarGrade,
    setVehicleGrade,
    createTask,
    selectCableCar,
    selectVehicle,
    fetchAiConfig,
    saveAiConfigAction,
    sendAiChat,
    triggerAiDispatch,
    fetchAiChatHistory,
    clearAiChatHistoryAction,
    fetchAiScheduler,
    startAiSchedulerAction,
    stopAiSchedulerAction,
    fetchAiExperience,
    toggleAiPanel,
  }
})
