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
        <MatchCenter />
      </div>
      
      <!-- 任务列表 -->
      <TaskList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDispatchStore } from '@/stores/dispatch'
import DataMonitor from './DataMonitor.vue'
import TaskList from './TaskList.vue'
import MatchCenter from './MatchCenter.vue'

const store = useDispatchStore()
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
  overflow-y: auto;
  min-height: 0;
}

.match-area::-webkit-scrollbar {
  width: 4px;
}

.match-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.match-area::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.2);
  border-radius: 2px;
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

.match-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  min-width: 280px;
}

.match-item.empty {
  opacity: 0.5;
  border-style: dashed;
}

.match-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.match-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.match-grade {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.match-grade.no-grade {
  background: rgba(255, 71, 87, 0.1);
  color: var(--accent-red);
  border: 1px solid rgba(255, 71, 87, 0.3);
}

.match-placeholder {
  color: var(--text-muted);
  font-size: 14px;
}

.match-arrow {
  font-size: 24px;
  color: var(--accent-blue);
  opacity: 0.5;
}

.match-actions {
  display: flex;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  color: #000;
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.match-warning {
  margin-top: 16px;
  padding: 10px 16px;
  background: rgba(255, 159, 67, 0.1);
  border: 1px solid rgba(255, 159, 67, 0.3);
  border-radius: 8px;
  color: #ff9f43;
  font-size: 13px;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

@keyframes fadeOutUp {
  from { opacity: 1; transform: translateX(-50%) translateY(0); }
  to { opacity: 0; transform: translateX(-50%) translateY(-20px); }
}
</style>
