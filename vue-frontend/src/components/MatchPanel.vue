<template>
  <div class="panel-center">
    <div class="panel-header">
      <span class="panel-title">◆ 调度匹配</span>
    </div>
    
    <div class="panel-body">
      <DataMonitor />
      
      <div class="match-area">
        <MatchCenter />
      </div>
      
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
  border-radius: clamp(10px, 1vw, 14px);
  overflow-y: auto;
  min-height: 0;
}

@media screen and (max-width: 1200px) {
  .match-area {
    border-radius: 10px;
  }
}

.match-area::-webkit-scrollbar {
  width: 4px;
}

.match-area::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
  border-radius: 2px;
}

.match-area::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
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
  background: var(--btn-gradient);
  border: none;
  border-radius: 6px;
  color: var(--btn-gradient-text);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.match-selected button:hover,
.match-action button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px var(--accent-blue-bg);
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
  background: var(--bg-subtle);
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
  background: var(--accent-red-bg);
  color: var(--accent-red);
  border: 1px solid var(--accent-red-border);
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
  background: var(--btn-gradient);
  color: var(--btn-gradient-text);
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 16px var(--accent-blue-bg);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: var(--bg-subtle);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-subtle-hover);
  color: var(--text-primary);
}

.match-warning {
  margin-top: 16px;
  padding: 10px 16px;
  background: var(--accent-yellow-bg);
  border: 1px solid var(--accent-yellow-border);
  border-radius: 8px;
  color: var(--accent-yellow);
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
