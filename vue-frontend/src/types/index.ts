export type ManualState = 'normal' | 'rest' | 'other'
export type AutoState = 'loading' | 'delivering' | 'unloading' | 'returning'
export type StateType = ManualState | AutoState

export interface Grade {
  id: number
  name: string
  color: string
}

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

export interface Vehicle {
  id: number
  tid: number
  name: string
  grade_id: number
  status: string
  direction: string
  state: string
  state_label: string
  location: string
  result_x: number
  result_y: number
  speed: number
  lat: number
  lon: number
}

export interface Task {
  id: number
  cable_car_id: number
  vehicle_id: number
  grade_id: number
  status: 'assigned' | 'pending' | 'completed' | 'cancelled'
  car_confirmed: number
  created_at: string
  completed_at: string
  cable_car_name: string
  vehicle_name: string
  grade_name: string
  grade_color: string
}

export interface StatusResponse {
  cable_cars: CableCar[]
  vehicles: Vehicle[]
  grades: Grade[]
  active_tasks: Task[]
  recent_tasks: Task[]
}

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

export interface AiConfig {
  api_url: string
  api_key: string
  api_key_configured?: boolean
  model: string
  temperature: number
  max_tokens: number
  enabled: boolean
  auto_dispatch_enabled: boolean
  dispatch_interval: number
}

export interface AiChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_calls?: any[]
  tool_result?: any
  tool_results?: any[]
  created_at: string
}

export interface AiSchedulerStatus {
  running: boolean
  enabled: boolean
  interval: number
  api_configured: boolean
  last_dispatch_time: string
  last_dispatch_success: boolean | null
  dispatch_count: number
  started_at: string
}

export interface AiExperience {
  id: number
  cable_car_id: number
  vehicle_id: number
  grade_id: number
  grade_name: string
  cable_car_state: string
  vehicle_state: string
  cable_car_latitude: number
  vehicle_result_y: number
  ai_reasoning: string
  outcome: string
  outcome_detail: string
  operator_override: number
  override_reason: string
  created_at: string
  resolved_at: string
}

export interface AiExperienceSummary {
  total: number
  success: number
  failure: number
  pending: number
  overrides: number
  success_rate: number
}

export interface AiChatResponse {
  response: string
  tool_results: any[]
  success: boolean
}
