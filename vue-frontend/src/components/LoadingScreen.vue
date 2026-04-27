<template>
  <div class="loading-screen">
    <div class="loading-content">
      <div class="loading-logo">
        <div class="logo-ring">
          <div class="ring-outer"></div>
          <div class="ring-inner"></div>
          <div class="ring-core"></div>
        </div>
      </div>
      <div class="loading-title">智能卸料动态匹配调度中心</div>
      <div class="loading-subtitle">INTELLIGENT DISPATCH CENTER</div>
      <div class="loading-bar">
        <div class="bar-track">
          <div class="bar-fill"></div>
        </div>
      </div>
      <div class="loading-status">正在连接系统...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--loading-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
}

.loading-logo {
  margin-bottom: 30px;
}

.logo-ring {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto;
}

.ring-outer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid var(--accent-blue-border);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.ring-inner {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  bottom: 10px;
  border: 2px solid var(--accent-green-border);
  border-bottom-color: var(--accent-green);
  border-radius: 50%;
  animation: spin 1s linear infinite reverse;
}

.ring-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent-blue);
  box-shadow: 0 0 20px var(--accent-blue), 0 0 40px var(--accent-blue-bg);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
  50% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.6; }
}

.loading-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.loading-subtitle {
  font-family: 'Orbitron', monospace;
  font-size: 10px;
  letter-spacing: 6px;
  color: var(--text-muted);
  margin-bottom: 30px;
}

.loading-bar {
  width: 200px;
  margin: 0 auto 16px;
}

.bar-track {
  height: 3px;
  background: var(--bg-subtle);
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  width: 30%;
  background: var(--btn-gradient);
  border-radius: 2px;
  animation: loading-slide 1.5s ease-in-out infinite;
}

@keyframes loading-slide {
  0% { width: 0%; margin-left: 0; }
  50% { width: 60%; margin-left: 20%; }
  100% { width: 0%; margin-left: 100%; }
}

.loading-status {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 2px;
}
</style>
