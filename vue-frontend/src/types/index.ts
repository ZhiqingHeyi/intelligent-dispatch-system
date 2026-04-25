// 状态类型
export type ManualState = 'normal' | 'rest' | 'other'
export type AutoState = 'loading' | 'delivering' | 'unloading' | 'returning'
export type StateType = ManualState | AutoState

// 级配类型
export interface Grade {
  id: number
  name: string
  color: string
}

// 缆机类型
export interface CableCar {
  id: number
  name: string
  grade_id: number
  status: string
  direction: string
  state: string
  state_label: string
  manual_state: ManualState
  location: string
  latitude: number
  longitude: number
  altitude: number
  xspeed: number
  yspeed: number
  start: number
  updated_at: string
  synced_at: string
}

// 车辆类型
export interface Vehicle {
  id: number
  tid: number
  name: string
  grade_id: number
  status: string
  direction: string
  result_x: number
  result_y: number
  speed: number
  lat: number
  lon: number
}

// 任务类型
export interface Task {
  id: number
  cable_car_id: number
  vehicle_id: number
  grade_id: number
  status: 'assigned' | 'pending' | 'completed' | 'cancelled'
  created_at: string
  completed_at: string
  cable_car_name: string
  vehicle_name: string
  grade_name: string
  grade_color: string
}

// API 响应类型
export interface StatusResponse {
  cable_cars: CableCar[]
  vehicles: Vehicle[]
  grades: Grade[]
  active_tasks: Task[]
  recent_tasks: Task[]
}

// 状态配置
export interface StateConfig {
  label: string
  color: string
  type: 'manual' | 'auto'
}

export const STATE_CONFIG: Record<StateType, StateConfig> = {
  normal: { label: '正常运行', color: '#00ff88', type: 'manual' },
  rest: { label: '休息中', color: '#c084fc', type: 'manual' },
  other: { label: '打杂中', color: '#888888', type: 'manual' },
  loading: { label: '990平台接料', color: '#ffd93d', type: 'auto' },
  delivering: { label: '送料途中', color: '#00d4ff', type: 'auto' },
  unloading: { label: '基坑卸料', color: '#ff6b6b', type: 'auto' },
  returning: { label: '返程途中', color: '#00ff88', type: 'auto' },
}
