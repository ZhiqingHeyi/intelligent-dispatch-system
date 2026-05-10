import axios from 'axios'
import type { StatusResponse, AiConfig, AiChatResponse, AiSchedulerStatus } from '@/types'

// 生产环境使用完整URL，开发环境使用相对路径
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const fetchStatus = () => {
  return api.get<StatusResponse>('/status')
}

export const setCableCarGrade = (carId: number, gradeId: number) => {
  return api.post(`/cable-car/${carId}/grade`, { grade_id: gradeId })
}

export const setCableCarState = (carId: number, manualState: string) => {
  return api.post(`/cable-car/${carId}/state`, { manual_state: manualState })
}

export const setVehicleGrade = (vehicleId: number, gradeId: number) => {
  return api.post(`/vehicle/${vehicleId}/grade`, { grade_id: gradeId })
}

export const createTask = (cableCarId: number, vehicleId: number, gradeId: number) => {
  return api.post('/dispatch', {
    cable_car_id: cableCarId,
    vehicle_id: vehicleId,
    grade_id: gradeId,
  })
}

export const completeTask = (taskId: number) => {
  return api.post(`/task/${taskId}/complete`)
}

export const cancelTask = (taskId: number) => {
  return api.post(`/task/${taskId}/cancel`)
}

export const aiChat = (message: string) => {
  return api.post<AiChatResponse>('/ai/chat', { message })
}

export const aiDispatch = () => {
  return api.post<AiChatResponse>('/ai/dispatch')
}

export const getAiConfig = () => {
  return api.get<{ success: boolean; config: AiConfig }>('/ai/config')
}

export const saveAiConfig = (config: Partial<AiConfig>) => {
  return api.post<{ success: boolean; message: string; verified: boolean; errors?: string[] }>('/ai/config', config)
}

export const testAiConnection = (config: Partial<AiConfig>) => {
  return api.post<{ success: boolean; message: string }>('/ai/config/test', config)
}

export const getAiScheduler = () => {
  return api.get<{ success: boolean; status: AiSchedulerStatus }>('/ai/scheduler')
}

export const startAiScheduler = () => {
  return api.post('/ai/scheduler/start')
}

export const stopAiScheduler = () => {
  return api.post('/ai/scheduler/stop')
}

export const getAiChatHistory = (limit = 50) => {
  return api.get('/ai/chat/history', { params: { limit } })
}

export const clearAiChatHistory = () => {
  return api.delete('/ai/chat/history')
}

export const getAiExperience = (params?: { grade_id?: number; outcome?: string; limit?: number }) => {
  return api.get('/ai/experience', { params })
}

export const updateExperienceOutcome = (expId: number, data: { outcome: string; detail?: string; operator_override?: boolean; override_reason?: string }) => {
  return api.post(`/ai/experience/${expId}/outcome`, data)
}

export default api
