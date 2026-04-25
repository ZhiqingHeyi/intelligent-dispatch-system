<template>
  <div class="dashboard">
    <!-- 加载动画 -->
    <LoadingScreen v-if="loading && !initialized" />
    
    <!-- 主界面 -->
    <template v-else>
      <AppHeader />
      
      <main class="main-content">
        <!-- 左侧：缆机状态 -->
        <CableCarPanel />
        
        <!-- 中间：调度匹配 -->
        <MatchPanel />
        
        <!-- 右侧：运输车辆 -->
        <VehiclePanel />
      </main>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import AppHeader from '@/components/AppHeader.vue'
import LoadingScreen from '@/components/LoadingScreen.vue'
import CableCarPanel from '@/components/CableCarPanel.vue'
import MatchPanel from '@/components/MatchPanel.vue'
import VehiclePanel from '@/components/VehiclePanel.vue'

const store = useDispatchStore()
const loading = ref(true)
const initialized = ref(false)
let intervalId: number | null = null

onMounted(async () => {
  await store.fetchData()
  loading.value = false
  initialized.value = true
  
  // 启动轮询
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
/* 全局样式 */
:root {
  --bg-primary: #020617;
  --bg-card: rgba(8, 16, 40, 0.6);
  --border-color: rgba(30, 58, 110, 0.4);
  --text-primary: #e8efff;
  --text-secondary: #8b92b4;
  --text-muted: #5a6380;
  --accent-blue: #00d4ff;
  --accent-green: #00ff88;
  --accent-yellow: #ffd93d;
  --accent-red: #ff6b6b;
  --accent-purple: #c084fc;
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
}

.dashboard {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(0, 100, 255, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 200, 100, 0.03) 0%, transparent 50%),
    var(--bg-primary);
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr 360px;
  gap: 14px;
  padding: 14px;
  overflow: hidden;
}
</style>
