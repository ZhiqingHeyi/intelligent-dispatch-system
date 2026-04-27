<template>
  <div class="task-panel">
    <div class="task-section">
      <h3>当前任务</h3>
      <div class="task-list">
        <div
          v-for="task in store.activeTasks"
          :key="task.id"
          class="task-card active"
        >
          <span class="task-grade-dot" :style="{ background: task.grade_color || '#5a6380' }"></span>
          <div class="task-info">
            <div class="task-title">{{ task.cable_car_name }} ← {{ task.vehicle_name }}</div>
            <div class="task-meta">{{ task.grade_name || '' }} · {{ task.created_at || '' }}</div>
          </div>
          <div class="task-actions">
            <button class="task-btn complete" @click="completeTask(task.id)">完成</button>
            <button class="task-btn cancel" @click="cancelTask(task.id)">取消</button>
          </div>
        </div>
        <div v-if="store.activeTasks.length === 0" class="empty-hint">暂无进行中的任务</div>
      </div>
    </div>
    
    <div class="task-section">
      <h3>历史记录</h3>
      <div class="task-list history">
        <div
          v-for="task in store.recentTasks"
          :key="task.id"
          class="task-card done"
        >
          <span class="task-grade-dot" :style="{ background: task.grade_color || '#5a6380' }"></span>
          <div class="task-info">
            <div class="task-title">{{ task.cable_car_name }} ← {{ task.vehicle_name }}</div>
            <div class="task-meta">{{ task.grade_name || '' }} · {{ task.status === 'completed' ? '已完成' : '已取消' }}</div>
          </div>
        </div>
        <div v-if="store.recentTasks.length === 0" class="empty-hint">暂无历史记录</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDispatchStore } from '@/stores/dispatch'
import * as api from '@/api/dispatch'

const store = useDispatchStore()

const completeTask = async (taskId: number) => {
  try {
    await api.completeTask(taskId)
    await store.fetchData()
  } catch (e) {
    alert('操作失败')
  }
}

const cancelTask = async (taskId: number) => {
  if (!confirm('确认取消？')) return
  try {
    await api.cancelTask(taskId)
    await store.fetchData()
  } catch (e) {
    alert('操作失败')
  }
}
</script>

<style scoped>
.task-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: clamp(10px, 1vw, 14px);
  padding: clamp(12px, 1.5vh, 16px);
  display: flex;
  flex-direction: column;
  gap: clamp(12px, 1.5vh, 16px);
}

@media screen and (max-width: 1200px) {
  .task-panel {
    padding: 12px;
    border-radius: 10px;
    gap: 12px;
  }
}

.task-section h3 {
  font-size: clamp(11px, 1vw, 12px);
  color: var(--text-muted);
  margin-bottom: clamp(8px, 1vh, 10px);
  font-weight: 500;
}

@media screen and (max-width: 1200px) {
  .task-section h3 {
    font-size: 11px;
    margin-bottom: 8px;
  }
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 120px;
  overflow-y: auto;
}

.task-list.history {
  max-height: 150px;
}

.task-card {
  display: flex;
  align-items: center;
  gap: clamp(8px, 0.8vw, 10px);
  padding: clamp(8px, 1vh, 10px) clamp(10px, 1vw, 12px);
  background: var(--bg-subtle);
  border-radius: clamp(6px, 0.8vw, 8px);
  font-size: clamp(11px, 1vw, 12px);
}

@media screen and (max-width: 1200px) {
  .task-card {
    gap: 8px;
    padding: 8px 10px;
    font-size: 11px;
    border-radius: 6px;
  }
}

.task-card.active {
  border-left: 3px solid var(--accent-green);
}

.task-card.done {
  border-left: 3px solid var(--accent-blue);
  opacity: 0.7;
}

.task-grade-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-meta {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

.task-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.task-btn {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.task-btn.complete {
  background: var(--accent-green-bg);
  color: var(--accent-green);
  border: 1px solid var(--accent-green-border);
}

.task-btn.complete:hover {
  background: var(--accent-green-bg);
  filter: brightness(1.2);
}

.task-btn.cancel {
  background: var(--accent-red-bg);
  color: var(--accent-red);
  border: 1px solid var(--accent-red-border);
}

.task-btn.cancel:hover {
  background: var(--accent-red-bg);
  filter: brightness(1.2);
}

.empty-hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  padding: 20px;
}
</style>
