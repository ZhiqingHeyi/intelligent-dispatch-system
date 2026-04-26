<template>
  <header class="header">
    <div class="header-scan-line"></div>
    
    <!-- 左侧装饰 -->
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
    
    <!-- 中间标题区域 -->
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
    
    <!-- 右侧装饰和时间状态 -->
    <div class="header-deco-right">
      <div class="header-top-status">
        <span class="sync-status" :class="{ online: !store.loading, offline: store.error }">
          <span class="sync-dot"></span>
          {{ store.error ? '同步异常' : '智能匹配中' }}
        </span>
        <span class="clock">{{ currentTime }}</span>
      </div>
      <div class="deco-dots">
        <span></span><span></span><span></span>
      </div>
      <div class="deco-line"></div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'

const store = useDispatchStore()
const currentTime = ref('')
let timer: number | null = null

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
  height: 90px;
  min-height: 90px;
  max-height: 90px;
  background: linear-gradient(180deg, rgba(4, 8, 20, 0.98) 0%, rgba(4, 8, 16, 0.95) 100%);
  border-bottom: 1px solid var(--border-color);
  position: relative;
  z-index: 10;
  backdrop-filter: blur(16px);
  flex-shrink: 0;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--accent-blue) 20%, 
    var(--accent-green) 50%, 
    var(--accent-blue) 80%, 
    transparent 100%);
  opacity: 0.8;
}

.header-scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 25%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #fff, transparent);
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
  padding: 12px 0 8px;
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
  background: radial-gradient(ellipse at center, 
    rgba(0, 212, 255, 0.15) 0%, 
    rgba(0, 232, 122, 0.08) 30%, 
    transparent 70%);
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
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 3px;
  color: var(--accent-blue);
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.title-divider {
  font-size: 18px;
  color: var(--accent-green);
  opacity: 0.6;
  font-weight: 300;
}

.title-main {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 4px;
  background: linear-gradient(135deg, 
    #ffffff 0%, 
    var(--accent-blue) 30%, 
    var(--accent-green) 70%, 
    #ffffff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.4));
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
  background: linear-gradient(90deg, 
    transparent, 
    rgba(0, 212, 255, 0.3), 
    rgba(0, 232, 122, 0.3), 
    rgba(0, 212, 255, 0.3), 
    transparent);
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
  background: linear-gradient(90deg, 
    rgba(0, 212, 255, 0.08) 0%, 
    rgba(0, 212, 255, 0.15) 50%, 
    rgba(0, 212, 255, 0.08) 100%);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 10px;
  font-size: 11px;
  color: var(--accent-blue);
  letter-spacing: 1px;
  white-space: nowrap;
  animation: badge-glow 3s ease-in-out infinite;
}

.header-deco-left .developer-icon {
  font-size: 8px;
  color: var(--accent-green);
  animation: icon-pulse 2s ease-in-out infinite;
}

@keyframes badge-glow {
  0%, 100% { 
    box-shadow: 0 0 4px rgba(0, 212, 255, 0.2);
    border-color: rgba(0, 212, 255, 0.3);
  }
  50% { 
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
    border-color: rgba(0, 212, 255, 0.5);
  }
}

@keyframes icon-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.subtitle-text {
  font-family: 'Orbitron', monospace;
  font-size: 9px;
  letter-spacing: 6px;
  color: var(--text-muted);
  opacity: 0.7;
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
  top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco-left { left: 20px; }
.header-deco-right { right: 20px; flex-direction: row-reverse; }

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
  color: var(--text-muted);
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
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 2px;
}
</style>
