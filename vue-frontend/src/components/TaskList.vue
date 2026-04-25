<template>
  <div class="task-panel">
    <div class="task-section">
      <h4>当前任务 ({{ store.activeTasks.length }})</h4>
      <div class="task-list">
        <div 
          v-for="task in store.activeTasks" 
          :key="task.id"
          class="task-item active"
        >
          <span class="task-dot" :style="{ background: task.grade_color }"></span>
          <span class="task-text">
            {{ task.cable_car_name }} ← {{ task.vehicle_name }}
          </span>
        </div>
        <div v-if="store.activeTasks.length === 0" class="task-empty">
          暂无进行中的任务
        </div>
      </div>
    </div>
    
    <div class="task-section">
      <h4>历史记录</h4>
      <div class="task-list history">
        <div 
          v-for="task in store.recentTasks.slice(0, 5)" 
          :key="task.id"
          class="task-item"
          :class="task.status"
        >
          <span class="task-dot" :style="{ background: task.grade_color }"></span>
          <span class="task-text">
            {{ task.cable_car_name }} ← {{ task.vehicle_name }}
          </span>
          <span class="task-status">{{ task.status === 'completed' ? '已完成' : '已取消' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDispatchStore } from '@/stores/dispatch'

const store = useDispatchStore()
</script>

<style scoped>
.task-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-section h4 {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
  font-weight: 500;
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

.task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 12px;
}

.task-item.active {
  border-left: 2px solid var(--accent-green);
}

.task-item.completed {
  border-left: 2px solid var(--accent-blue);
  opacity: 0.7;
}

.task-item.cancelled {
  border-left: 2px solid var(--accent-red);
  opacity: 0.5;
}

.task-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-text {
  flex: 1;
  color: var(--text-primary);
}

.task-status {
  font-size: 10px;
  color: var(--text-muted);
}

.task-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  padding: 20px;
}
</style>
