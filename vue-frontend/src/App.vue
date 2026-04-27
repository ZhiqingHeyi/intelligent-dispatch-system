<template>
  <div class="dashboard" :data-theme="themeStore.theme">
    <LoadingScreen v-if="loading && !initialized" />
    
    <template v-else>
      <AppHeader />
      
      <main class="main-content" :class="{ 'ai-open': store.aiPanelOpen }">
        <CableCarPanel 
          @open-grade-modal="openGradeModal"
          @open-state-modal="openStateModal"
        />
        
        <MatchPanel />
        
        <VehiclePanel @open-grade-modal="openGradeModal" />

        <AiAssistant />
      </main>

      <button class="ai-fab" :class="{ active: store.aiPanelOpen }" @click="store.toggleAiPanel()">
        <span class="fab-icon">{{ store.aiPanelOpen ? '✕' : '🤖' }}</span>
        <span v-if="!store.aiPanelOpen && store.aiApiConfigured" class="fab-badge"></span>
      </button>
      
      <GradeModal
        v-model="gradeModal.show"
        :target-id="gradeModal.targetId"
        :target-name="gradeModal.targetName"
        :current-grade-id="gradeModal.currentGradeId"
        :type="gradeModal.type"
      />
      
      <StateModal
        v-model="stateModal.show"
        :target-id="stateModal.targetId"
        :target-name="stateModal.targetName"
        :current-state="stateModal.currentState"
      />

      <AiConfigModal />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import { useThemeStore } from '@/stores/theme'
import AppHeader from '@/components/AppHeader.vue'
import LoadingScreen from '@/components/LoadingScreen.vue'
import CableCarPanel from '@/components/CableCarPanel.vue'
import MatchPanel from '@/components/MatchPanel.vue'
import VehiclePanel from '@/components/VehiclePanel.vue'
import GradeModal from '@/components/GradeModal.vue'
import StateModal from '@/components/StateModal.vue'
import AiAssistant from '@/components/AiAssistant.vue'
import AiConfigModal from '@/components/AiConfigModal.vue'

const store = useDispatchStore()
const themeStore = useThemeStore()
const loading = ref(true)
const initialized = ref(false)
let intervalId: number | null = null

const gradeModal = reactive({
  show: false,
  targetId: null as number | null,
  targetName: '',
  currentGradeId: 0,
  type: 'cable_car' as 'cable_car' | 'vehicle'
})

const stateModal = reactive({
  show: false,
  targetId: null as number | null,
  targetName: '',
  currentState: 'normal'
})

const openGradeModal = (data: { 
  id: number
  name: string
  gradeId: number
  type: 'cable_car' | 'vehicle'
}) => {
  gradeModal.targetId = data.id
  gradeModal.targetName = data.name
  gradeModal.currentGradeId = data.gradeId
  gradeModal.type = data.type
  gradeModal.show = true
}

const openStateModal = (data: {
  id: number
  name: string
  currentState: string
}) => {
  stateModal.targetId = data.id
  stateModal.targetName = data.name
  stateModal.currentState = data.currentState
  stateModal.show = true
}

onMounted(async () => {
  await store.fetchData()
  loading.value = false
  initialized.value = true
  
  intervalId = window.setInterval(() => {
    store.fetchData()
  }, 3000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style>
:root,
[data-theme="dark"] {
  --bg-primary: #020617;
  --bg-card: rgba(8, 16, 40, 0.6);
  --bg-card-hover: rgba(12, 24, 56, 0.8);
  --bg-subtle: rgba(0, 0, 0, 0.2);
  --bg-subtle-hover: rgba(0, 0, 0, 0.3);
  --bg-inset: rgba(0, 0, 0, 0.25);
  --bg-header: rgba(4, 8, 20, 0.98);
  --bg-header-end: rgba(4, 8, 16, 0.95);
  --bg-input: rgba(0, 0, 0, 0.3);
  --bg-overlay: rgba(0, 0, 0, 0.7);
  --header-text-primary: #e8efff;
  --header-text-secondary: #8b92b4;
  --header-text-muted: #5a6380;
  --border-color: rgba(30, 58, 110, 0.4);
  --border-subtle: rgba(30, 58, 110, 0.2);
  --text-primary: #e8efff;
  --text-secondary: #8b92b4;
  --text-muted: #5a6380;
  --accent-blue: #00d4ff;
  --accent-green: #00ff88;
  --accent-yellow: #ffd93d;
  --accent-red: #ff6b6b;
  --accent-purple: #c084fc;
  --accent-blue-bg: rgba(0, 212, 255, 0.1);
  --accent-blue-bg-hover: rgba(0, 212, 255, 0.15);
  --accent-blue-border: rgba(0, 212, 255, 0.2);
  --accent-blue-border-hover: rgba(0, 212, 255, 0.3);
  --accent-blue-border-strong: rgba(0, 212, 255, 0.5);
  --accent-blue-glow: rgba(0, 212, 255, 0.06);
  --accent-green-bg: rgba(0, 255, 136, 0.1);
  --accent-green-border: rgba(0, 255, 136, 0.2);
  --accent-red-bg: rgba(255, 107, 107, 0.1);
  --accent-red-border: rgba(255, 107, 107, 0.2);
  --accent-yellow-bg: rgba(255, 217, 61, 0.1);
  --accent-yellow-border: rgba(255, 217, 61, 0.3);
  --accent-purple-bg: rgba(192, 132, 252, 0.12);
  --accent-purple-border: rgba(192, 132, 252, 0.25);
  --shadow-color: rgba(0, 0, 0, 0.3);
  --shadow-heavy: rgba(0, 0, 0, 0.4);
  --scrollbar-track: rgba(0, 0, 0, 0.2);
  --scrollbar-thumb: rgba(0, 212, 255, 0.2);
  --scrollbar-thumb-hover: rgba(0, 212, 255, 0.4);
  --title-gradient: linear-gradient(135deg, #ffffff 0%, var(--accent-blue) 30%, var(--accent-green) 70%, #ffffff 100%);
  --btn-gradient: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  --btn-gradient-text: #000;
  --fab-bg: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 255, 136, 0.1));
  --fab-border: rgba(0, 212, 255, 0.3);
  --fab-active-bg: rgba(255, 107, 107, 0.15);
  --fab-active-border: rgba(255, 107, 107, 0.3);
  --deco-gradient: radial-gradient(ellipse at 20% 20%, rgba(0, 100, 255, 0.03) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(0, 200, 100, 0.03) 0%, transparent 50%);
  --loading-bg: linear-gradient(135deg, #020617 0%, #0a1628 50%, #020617 100%);
  --close-btn-bg: rgba(255, 255, 255, 0.05);
  --close-btn-hover-bg: rgba(255, 71, 87, 0.1);
  --badge-bg: linear-gradient(90deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 212, 255, 0.15) 50%, rgba(0, 212, 255, 0.08) 100%);
  --badge-border: rgba(0, 212, 255, 0.25);
  --grade-no-bg: rgba(74, 82, 112, 0.1);
  --state-btn-bg: rgba(100, 100, 100, 0.1);
  --state-btn-border: rgba(100, 100, 100, 0.3);
  --state-btn-color: #888;
  --grade-separator: rgba(30, 58, 110, 0.3);
  --id-badge-bg: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 136, 0.1));
  --id-badge-border: rgba(0, 212, 255, 0.3);
  --scan-line-color: #fff;
  --glow-border: linear-gradient(135deg, rgba(0, 212, 255, 0.1), transparent, rgba(0, 255, 136, 0.1));
  --modal-bg: var(--bg-card);
  --modal-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
  --ai-panel-gradient: radial-gradient(circle at 50% 0%, rgba(0, 212, 255, 0.05) 0%, transparent 50%), radial-gradient(circle at 50% 100%, rgba(0, 255, 136, 0.03) 0%, transparent 50%);
  --ai-scheduler-bg: rgba(0, 0, 0, 0.15);
  --ai-msg-user-bg: rgba(0, 212, 255, 0.1);
  --ai-msg-user-border: rgba(0, 212, 255, 0.15);
  --ai-msg-assistant-bg: rgba(0, 0, 0, 0.2);
  --ai-msg-avatar-bg: rgba(0, 0, 0, 0.3);
  --ai-msg-avatar-gradient: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 255, 136, 0.1));
  --ai-msg-avatar-border: rgba(0, 212, 255, 0.2);
  --ai-code-bg: rgba(0, 212, 255, 0.1);
  --config-modal-bg: linear-gradient(180deg, rgba(8, 16, 40, 0.98) 0%, rgba(4, 8, 20, 0.98) 100%);
  --monitor-radial: radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.03) 0%, transparent 40%), radial-gradient(circle at 80% 50%, rgba(0, 212, 255, 0.03) 0%, transparent 40%);
  --match-card-bg: rgba(0, 0, 0, 0.25);
  --match-card-hover-bg: rgba(0, 0, 0, 0.35);
  --title-glow-bg: radial-gradient(ellipse at center, rgba(0, 212, 255, 0.15) 0%, rgba(0, 232, 122, 0.08) 30%, transparent 70%);
  --underline-glow-bg: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), rgba(0, 232, 122, 0.3), rgba(0, 212, 255, 0.3), transparent);
  --header-top-line: linear-gradient(90deg, transparent 0%, var(--accent-blue) 20%, var(--accent-green) 50%, var(--accent-blue) 80%, transparent 100%);
  --section-title-border: rgba(0, 212, 255, 0.1);
  --toggle-bg: rgba(0, 0, 0, 0.3);
  --toggle-active-bg: rgba(0, 212, 255, 0.2);
  --toggle-active-border: rgba(0, 212, 255, 0.4);
}

[data-theme="light"] {
  /* 军用雷达/CRT荧光绿色主题 */
  --bg-primary: #0a110a;
  --bg-card: rgba(10, 20, 10, 0.85);
  --bg-card-hover: rgba(15, 30, 15, 0.9);
  --bg-subtle: rgba(0, 40, 0, 0.3);
  --bg-subtle-hover: rgba(0, 60, 0, 0.4);
  --bg-inset: rgba(0, 30, 0, 0.4);
  --bg-header: #051005;
  --bg-header-end: #0a1a0a;
  --bg-input: rgba(0, 40, 0, 0.5);
  --header-text-primary: #39ff14;
  --header-text-secondary: #7fff00;
  --header-text-muted: #4a8a4a;
  --bg-overlay: rgba(0, 10, 0, 0.8);
  --border-color: rgba(57, 255, 20, 0.3);
  --border-subtle: rgba(57, 255, 20, 0.15);
  --text-primary: #39ff14;
  --text-secondary: #7fff00;
  --text-muted: #4a8a4a;
  --accent-blue: #39ff14;
  --accent-green: #00ff41;
  --accent-yellow: #adff2f;
  --accent-red: #ff3333;
  --accent-purple: #bf00ff;
  --accent-blue-bg: rgba(57, 255, 20, 0.15);
  --accent-blue-bg-hover: rgba(57, 255, 20, 0.25);
  --accent-blue-border: rgba(57, 255, 20, 0.4);
  --accent-blue-border-hover: rgba(57, 255, 20, 0.6);
  --accent-blue-border-strong: rgba(57, 255, 20, 0.8);
  --accent-blue-glow: rgba(57, 255, 20, 0.3);
  --accent-green-bg: rgba(0, 255, 65, 0.15);
  --accent-green-border: rgba(0, 255, 65, 0.4);
  --accent-red-bg: rgba(255, 51, 51, 0.15);
  --accent-red-border: rgba(255, 51, 51, 0.4);
  --accent-yellow-bg: rgba(173, 255, 47, 0.15);
  --accent-yellow-border: rgba(173, 255, 47, 0.4);
  --accent-purple-bg: rgba(191, 0, 255, 0.15);
  --accent-purple-border: rgba(191, 0, 255, 0.4);
  --shadow-color: rgba(57, 255, 20, 0.2);
  --shadow-heavy: rgba(57, 255, 20, 0.3);
  --scrollbar-track: rgba(0, 40, 0, 0.3);
  --scrollbar-thumb: rgba(57, 255, 20, 0.4);
  --scrollbar-thumb-hover: rgba(57, 255, 20, 0.6);
  --title-gradient: linear-gradient(135deg, #39ff14 0%, #7fff00 50%, #00ff41 100%);
  --btn-gradient: linear-gradient(135deg, #39ff14, #00ff41);
  --btn-gradient-text: #000000;
  --fab-bg: linear-gradient(135deg, rgba(57, 255, 20, 0.2), rgba(0, 255, 65, 0.15));
  --fab-border: rgba(57, 255, 20, 0.5);
  --fab-active-bg: rgba(255, 51, 51, 0.2);
  --fab-active-border: rgba(255, 51, 51, 0.5);
  --deco-gradient: 
    repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(57, 255, 20, 0.03) 2px, rgba(57, 255, 20, 0.03) 4px),
    radial-gradient(ellipse at 50% 50%, rgba(57, 255, 20, 0.05) 0%, transparent 70%);
  --loading-bg: #0a110a;
  --close-btn-bg: rgba(57, 255, 20, 0.1);
  --close-btn-hover-bg: rgba(255, 51, 51, 0.2);
  --badge-bg: linear-gradient(90deg, rgba(57, 255, 20, 0.1) 0%, rgba(57, 255, 20, 0.25) 50%, rgba(57, 255, 20, 0.1) 100%);
  --badge-border: rgba(57, 255, 20, 0.5);
  --grade-no-bg: rgba(0, 40, 0, 0.4);
  --state-btn-bg: rgba(0, 40, 0, 0.4);
  --state-btn-border: rgba(57, 255, 20, 0.3);
  --state-btn-color: #4a8a4a;
  --grade-separator: rgba(57, 255, 20, 0.2);
  --id-badge-bg: linear-gradient(135deg, #39ff14, #00ff41);
  --id-badge-border: rgba(57, 255, 20, 0.5);
  --scan-line-color: #39ff14;
  --glow-border: linear-gradient(135deg, rgba(57, 255, 20, 0.3), transparent, rgba(0, 255, 65, 0.2));
  --modal-bg: rgba(10, 20, 10, 0.95);
  --modal-shadow: 0 0 40px rgba(57, 255, 20, 0.3);
  --ai-panel-gradient: 
    repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(57, 255, 20, 0.02) 2px, rgba(57, 255, 20, 0.02) 4px),
    radial-gradient(circle at 50% 0%, rgba(57, 255, 20, 0.08) 0%, transparent 50%);
  --ai-scheduler-bg: rgba(0, 30, 0, 0.4);
  --ai-msg-user-bg: rgba(57, 255, 20, 0.1);
  --ai-msg-user-border: rgba(57, 255, 20, 0.2);
  --ai-msg-assistant-bg: rgba(0, 30, 0, 0.3);
  --ai-msg-avatar-bg: rgba(0, 40, 0, 0.5);
  --ai-msg-avatar-gradient: linear-gradient(135deg, #39ff14, #00ff41);
  --ai-msg-avatar-border: rgba(57, 255, 20, 0.3);
  --ai-code-bg: rgba(57, 255, 20, 0.1);
  --config-modal-bg: rgba(10, 20, 10, 0.98);
  --monitor-radial: radial-gradient(circle at 20% 50%, rgba(0, 255, 65, 0.08) 0%, transparent 40%), radial-gradient(circle at 80% 50%, rgba(57, 255, 20, 0.08) 0%, transparent 40%);
  --match-card-bg: rgba(0, 30, 0, 0.4);
  --match-card-hover-bg: rgba(0, 40, 0, 0.5);
  --title-glow-bg: radial-gradient(ellipse at center, rgba(57, 255, 20, 0.3) 0%, transparent 70%);
  --underline-glow-bg: linear-gradient(90deg, transparent, #39ff14, #00ff41, #39ff14, transparent);
  --header-top-line: linear-gradient(90deg, transparent 0%, #39ff14 20%, #00ff41 50%, #39ff14 80%, transparent 100%);
  --section-title-border: rgba(57, 255, 20, 0.2);
  --toggle-bg: rgba(0, 40, 0, 0.5);
  --toggle-active-bg: rgba(57, 255, 20, 0.2);
  --toggle-active-border: #39ff14;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  overflow: hidden;
  transition: background 0.3s ease, color 0.3s ease;
}

.dashboard {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--deco-gradient), var(--bg-primary);
  transition: background 0.3s ease;
  position: relative;
}

/* 军用雷达CRT扫描线效果 - 仅在雷达主题(light)下显示 */
.dashboard[data-theme="light"]::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 9999;
  background: 
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 1px,
      rgba(57, 255, 20, 0.03) 1px,
      rgba(57, 255, 20, 0.03) 2px
    );
  animation: crt-flicker 0.15s infinite;
}

@keyframes crt-flicker {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.98; }
}

/* 雷达扫描动画 */
.dashboard[data-theme="light"]::before {
  content: '';
  position: fixed;
  top: -100%;
  left: 0;
  right: 0;
  height: 8px;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(57, 255, 20, 0.1) 50%,
    transparent
  );
  pointer-events: none;
  z-index: 9998;
  animation: radar-scan 4s linear infinite;
}

@keyframes radar-scan {
  0% { top: -10%; }
  100% { top: 110%; }
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(240px, 16%) 1fr minmax(260px, 18%);
  gap: clamp(10px, 1vw, 14px);
  padding: clamp(10px, 1vw, 14px);
  overflow: hidden;
  transition: grid-template-columns 0.3s ease;
}

.main-content.ai-open {
  grid-template-columns: minmax(220px, 14%) 1fr minmax(220px, 16%) minmax(300px, 22%);
}

/* 响应式布局 - 大屏幕 */
@media screen and (min-width: 1920px) {
  .main-content {
    grid-template-columns: minmax(280px, 15%) 1fr minmax(300px, 18%);
  }
  
  .main-content.ai-open {
    grid-template-columns: minmax(260px, 13%) 1fr minmax(260px, 14%) minmax(340px, 18%);
  }
}

/* 响应式布局 - 中等屏幕 */
@media screen and (max-width: 1400px) {
  .main-content {
    grid-template-columns: minmax(220px, 18%) 1fr minmax(240px, 20%);
    gap: 10px;
    padding: 10px;
  }
  
  .main-content.ai-open {
    grid-template-columns: minmax(200px, 16%) 1fr minmax(200px, 16%) minmax(280px, 20%);
  }
}

/* 响应式布局 - 小屏幕 */
@media screen and (max-width: 1200px) {
  .main-content {
    grid-template-columns: minmax(200px, 20%) 1fr minmax(220px, 22%);
    gap: 8px;
    padding: 8px;
  }
  
  .main-content.ai-open {
    grid-template-columns: minmax(180px, 16%) 1fr minmax(180px, 16%) minmax(260px, 22%);
  }
}

/* 响应式布局 - 平板/小屏幕 */
@media screen and (max-width: 1024px) {
  .main-content {
    grid-template-columns: minmax(180px, 22%) 1fr minmax(200px, 24%);
    gap: 6px;
    padding: 6px;
  }
  
  .main-content.ai-open {
    grid-template-columns: minmax(160px, 18%) 1fr minmax(160px, 18%) minmax(240px, 24%);
  }
}

.ai-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  border: 1px solid var(--fab-border);
  background: var(--fab-bg);
  color: var(--text-primary);
  font-size: 22px;
  cursor: pointer;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px var(--shadow-color);
}

.ai-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 24px var(--accent-blue-bg);
  border-color: var(--accent-blue-border-strong);
}

.ai-fab.active {
  background: var(--fab-active-bg);
  border-color: var(--fab-active-border);
}

.fab-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.fab-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
  animation: fab-pulse 2s ease-in-out infinite;
}

@keyframes fab-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}
</style>
