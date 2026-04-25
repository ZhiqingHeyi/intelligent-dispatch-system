<template>
  <div class="loading-screen">
    <div class="loading-logo">DISPATCH CENTER</div>
    <div class="loading-bar">
      <div class="loading-bar-fill"></div>
    </div>
    <div class="loading-text">系统初始化中...</div>
  </div>
</template>

<style scoped>
.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #020617 0%, #0a1628 50%, #020617 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeOut 0.6s ease 1.2s forwards;
}

.loading-logo {
  font-family: 'Orbitron', monospace;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 8px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 40px;
  animation: pulse 2s ease-in-out infinite;
}

.loading-bar {
  width: 220px;
  height: 3px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 20px;
}

.loading-bar-fill {
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
  animation: fillBar 1.5s ease-out forwards;
}

.loading-text {
  font-size: 14px;
  color: var(--text-muted);
  letter-spacing: 4px;
  animation: fadeIn 1s ease 0.5s forwards;
  opacity: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

@keyframes fillBar {
  0% { width: 0; }
  100% { width: 100%; }
}

@keyframes fadeIn {
  to { opacity: 1; }
}

@keyframes fadeOut {
  to {
    opacity: 0;
    visibility: hidden;
  }
}
</style>
