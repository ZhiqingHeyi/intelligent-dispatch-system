<template>
  <header class="header">
    <div class="header-scan-line"></div>
    
    <div class="header-deco-left">
      <div class="deco-line"></div>
      <div class="deco-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="developer-badge">
        <span class="developer-icon">◆</span>
        <span class="developer-text">葛洲坝二公司自主研发</span>
      </div>
    </div>
    
    <div class="header-center-main">
      <div class="title-wrapper">
        <div class="title-glow"></div>
        <h1 class="main-title">
          <span class="title-prefix">QBT水利枢纽工程</span>
          <span class="title-divider">|</span>
          <span class="title-main">智能卸料动态匹配调度中心</span>
        </h1>
        <div class="title-underline">
          <div class="underline-core"></div>
          <div class="underline-glow"></div>
        </div>
      </div>
      <div class="subtitle-bar">
        <span class="subtitle-text">INTELLIGENT DISPATCH CENTER</span>
        <div class="subtitle-particles">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
      </div>
    </div>
    
    <div class="header-deco-right">
      <div class="header-top-status">
        <span class="sync-status" :class="{ online: syncStatus.online, offline: !syncStatus.online }">
          <span class="sync-dot"></span>
          {{ syncStatus.text }}
        </span>
        <span v-if="store.aiApiConfigured" class="ai-status-badge" :class="{ running: store.aiSchedulerStatus?.running }" @click="store.toggleAiPanel()">
          <span class="ai-badge-dot"></span>
          {{ store.aiSchedulerStatus?.running ? 'AI调度中' : 'AI就绪' }}
        </span>
        <span class="clock">{{ currentTime }}</span>
      </div>
      <div class="header-actions">
        <button class="theme-toggle" @click="themeStore.toggleTheme()" :title="themeStore.isDark ? '切换到白天模式' : '切换到夜间模式'">
          <span class="theme-icon">{{ themeStore.isDark ? '☀️' : '🌙' }}</span>
        </button>
      </div>
      <div class="deco-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="deco-line"></div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import { useThemeStore } from '@/stores/theme'

const store = useDispatchStore()
const themeStore = useThemeStore()
const currentTime = ref('')
let timer: number | null = null

// 计算同步状态：基于最后一次成功同步时间，而不是 loading 状态
const syncStatus = computed(() => {
  const timeSinceLastSync = Date.now() - store.lastSyncTime
  const isRecent = timeSinceLastSync < 10000 // 10秒内认为是在线
  
  if (store.error || !isRecent) {
    return { online: false, text: '同步异常' }
  }
  return { online: true, text: '智能匹配中' }
})

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  }) + ' ' + now.toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(() => {
  updateClock()
  timer = window.setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
  height: clamp(70px, 8vh, 90px);
  min-height: clamp(60px, 7vh, 80px);
  max-height: 100px;
  background: linear-gradient(180deg, var(--bg-header) 0%, var(--bg-header-end) 100%);
  border-bottom: 1px solid var(--border-color);
  position: relative;
  z-index: 10;
  backdrop-filter: blur(16px);
  flex-shrink: 0;
  transition: background 0.3s ease;
}

/* 响应式Header - 大屏幕 */
@media screen and (min-width: 1920px) {
  .header {
    height: 100px;
    min-height: 90px;
  }
}

/* 响应式Header - 小屏幕 */
@media screen and (max-width: 1200px) {
  .header {
    height: 65px;
    min-height: 60px;
  }
}

@media screen and (max-width: 1024px) {
  .header {
    height: 60px;
    min-height: 55px;
  }
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--header-top-line);
  opacity: 0.8;
}

.header-scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 25%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--scan-line-color), transparent);
  animation: scan-line 6s ease-in-out infinite;
  z-index: 11;
  filter: drop-shadow(0 0 6px var(--accent-green));
}

@keyframes scan-line {
  0% { left: -25%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
}

.header-center-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: clamp(8px, 1vh, 12px) 0 clamp(4px, 0.5vh, 8px);
  position: relative;
  width: 100%;
}

.title-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 200%;
  background: var(--title-glow-bg);
  pointer-events: none;
  animation: title-glow-pulse 4s ease-in-out infinite;
}

@keyframes title-glow-pulse {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
}

.main-title {
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: 'Noto Sans SC', sans-serif;
  position: relative;
  z-index: 1;
}

.title-prefix {
  font-size: clamp(13px, 1.2vw, 16px);
  font-weight: 500;
  letter-spacing: clamp(2px, 0.3vw, 3px);
  color: var(--accent-blue);
  text-shadow: 0 0 20px var(--accent-blue-bg);
}

.title-divider {
  font-size: clamp(14px, 1.3vw, 18px);
  color: var(--accent-green);
  opacity: 0.6;
  font-weight: 300;
}

.title-main {
  font-size: clamp(16px, 1.8vw, 22px);
  font-weight: 700;
  letter-spacing: clamp(2px, 0.4vw, 4px);
  background: var(--title-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 20px var(--accent-blue-bg));
}

.title-underline {
  position: relative;
  width: 50%;
  height: 2px;
  margin-top: 6px;
}

.underline-core {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    var(--accent-blue), 
    var(--accent-green), 
    var(--accent-blue), 
    transparent);
  border-radius: 2px;
}

.underline-glow {
  position: absolute;
  top: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 7px;
  background: var(--underline-glow-bg);
  filter: blur(4px);
  animation: underline-pulse 3s ease-in-out infinite;
}

@keyframes underline-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.subtitle-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
  position: relative;
}

.header-deco-left .developer-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 12px;
  padding: 3px 10px;
  background: var(--badge-bg);
  border: 1px solid var(--badge-border);
  border-radius: 10px;
  font-size: clamp(9px, 0.9vw, 11px);
  color: var(--accent-blue);
  letter-spacing: 1px;
  white-space: nowrap;
  animation: badge-glow 3s ease-in-out infinite;
}

@media screen and (max-width: 1200px) {
  .header-deco-left .developer-badge {
    padding: 2px 8px;
    margin-left: 8px;
  }
}

@media screen and (max-width: 1024px) {
  .header-deco-left .developer-badge {
    display: none;
  }
}

.header-deco-left .developer-icon {
  font-size: 8px;
  color: var(--accent-green);
  animation: icon-pulse 2s ease-in-out infinite;
}

@keyframes badge-glow {
  0%, 100% { 
    box-shadow: 0 0 4px var(--accent-blue-bg);
    border-color: var(--accent-blue-border);
  }
  50% { 
    box-shadow: 0 0 12px var(--accent-blue-bg-hover);
    border-color: var(--accent-blue-border-hover);
  }
}

@keyframes icon-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.subtitle-text {
  font-family: 'Orbitron', monospace;
  font-size: clamp(7px, 0.7vw, 9px);
  letter-spacing: clamp(3px, 0.5vw, 6px);
  color: var(--header-text-muted);
  opacity: 0.8;
}

@media screen and (max-width: 1200px) {
  .subtitle-text {
    display: none;
  }
}

.subtitle-particles {
  display: flex;
  gap: 4px;
}

.subtitle-particles span {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--accent-blue);
  animation: particle-blink 1.5s ease-in-out infinite;
}

.subtitle-particles span:nth-child(1) { animation-delay: 0s; }
.subtitle-particles span:nth-child(2) { animation-delay: 0.2s; }
.subtitle-particles span:nth-child(3) { animation-delay: 0.4s; }
.subtitle-particles span:nth-child(4) { animation-delay: 0.6s; }
.subtitle-particles span:nth-child(5) { animation-delay: 0.8s; }

@keyframes particle-blink {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); box-shadow: 0 0 6px var(--accent-blue); }
}

.header-deco-left,
.header-deco-right {
  position: absolute;
  top: clamp(10px, 1.5vh, 16px);
  display: flex;
  align-items: center;
  gap: clamp(4px, 0.6vw, 8px);
}

.header-deco-left { left: clamp(12px, 1.5vw, 20px); }
.header-deco-right { right: clamp(12px, 1.5vw, 20px); flex-direction: row-reverse; }

@media screen and (max-width: 1200px) {
  .header-deco-left,
  .header-deco-right {
    top: 8px;
  }
}

.deco-line {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, var(--accent-blue), transparent);
}

.header-deco-right .deco-line {
  background: linear-gradient(90deg, transparent, var(--accent-blue));
}

.deco-dots {
  display: flex;
  gap: 4px;
}

.deco-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent-blue);
  box-shadow: 0 0 6px var(--accent-blue);
  animation: dot-pulse 2s ease-in-out infinite;
}

.deco-dots span:nth-child(2) { animation-delay: 0.3s; }
.deco-dots span:nth-child(3) { animation-delay: 0.6s; }

@keyframes dot-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.header-top-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  margin-right: 12px;
}

.sync-status {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--header-text-muted);
}

.sync-status.online {
  color: var(--accent-green);
}

.sync-status.offline {
  color: var(--accent-red);
}

.sync-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
  animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.clock {
  font-family: 'Orbitron', monospace;
  font-size: clamp(10px, 1vw, 12px);
  color: var(--header-text-secondary);
  letter-spacing: clamp(1px, 0.2vw, 2px);
}

@media screen and (max-width: 1200px) {
  .clock {
    font-size: 10px;
  }
}

.ai-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 10px;
  color: var(--accent-blue);
  background: var(--accent-blue-bg);
  border: 1px solid var(--accent-blue-border);
  cursor: pointer;
  transition: all 0.2s;
}

.ai-status-badge:hover {
  background: var(--accent-blue-bg-hover);
  border-color: var(--accent-blue-border-hover);
}

.ai-status-badge.running {
  color: var(--accent-green);
  background: var(--accent-green-bg);
  border-color: var(--accent-green-border);
}

.ai-badge-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 4px currentColor;
}

.ai-status-badge.running .ai-badge-dot {
  animation: blink 1s ease-in-out infinite;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;
}

.theme-toggle {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  background: var(--accent-blue-bg);
  border-color: var(--accent-blue-border-hover);
  transform: scale(1.08);
}

.theme-icon {
  font-size: 16px;
  line-height: 1;
}
</style>
