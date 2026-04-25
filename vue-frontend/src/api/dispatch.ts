import axios from 'axios'
import type { StatusResponse, Task } from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 获取状态数据
export const fetchStatus = () => {
  return api.get<StatusResponse>('/status')
}

// 设置缆机级配
export const setCableCarGrade = (carId: number, gradeId: number) => {
  return api.post(`/cable-car/${carId}/grade`, { grade_id: gradeId })
}

// 设置缆机手动状态
export const setCableCarState = (carId: number, manualState: string) => {
  return api.post(`/cable-car/${carId}/state`, { manual_state: manualState })
}

// 设置车辆级配
export const setVehicleGrade = (vehicleId: number, gradeId: number) => {
  return api.post(`/vehicle/${vehicleId}/grade`, { grade_id: gradeId })
}

// 创建调度任务
export const createTask = (cableCarId: number, vehicleId: number, gradeId: number) => {
  return api.post('/dispatch', {
    cable_car_id: cableCarId,
    vehicle_id: vehicleId,
    grade_id: gradeId,
  })
}

// 完成任务
export const completeTask = (taskId: number) => {
  return api.post(`/task/${taskId}/complete`)
}

// 取消任务
export const cancelTask = (taskId: number) => {
  return api.post(`/task/${taskId}/cancel`)
}

export default api
