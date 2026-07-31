<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isMaximized = ref(false)

const winAPI = (window as any).electronAPI

function onMinimize() { winAPI?.minimize() }
async function onMaximize() { winAPI?.maximize() }
function onClose() { winAPI?.close() }

onMounted(() => {
  winAPI?.isMaximized().then((v: boolean) => { isMaximized.value = v })
  winAPI?.onMaximizeChange((v: boolean) => { isMaximized.value = v })
})
</script>

<template>
  <header class="titlebar">
    <div class="titlebar-drag">
      <span class="titlebar-logo">
        <span class="logo-icon">◆</span>
        SQLAgent
      </span>
    </div>
    <div class="titlebar-controls">
      <button class="ctrl-btn" @click="onMinimize" title="最小化">
        <svg width="12" height="12" viewBox="0 0 12 12"><rect y="5" width="12" height="1.5" fill="currentColor"/></svg>
      </button>
      <button class="ctrl-btn" @click="onMaximize" title="最大化">
        <svg v-if="!isMaximized" width="12" height="12" viewBox="0 0 12 12"><rect x="1" y="1" width="10" height="10" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        <svg v-else width="12" height="12" viewBox="0 0 12 12"><rect x="2" y="0" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="0" y="3" width="8" height="8" fill="var(--bg-primary)" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
      <button class="ctrl-btn ctrl-close" @click="onClose" title="关闭">
        <svg width="12" height="12" viewBox="0 0 12 12"><line x1="0" y1="0" x2="12" y2="12" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="0" x2="0" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </div>
  </header>
</template>

<style scoped>
.titlebar {
  display: flex;
  align-items: center;
  height: 38px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-default);
  flex-shrink: 0;
}
.titlebar-drag {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 14px;
  -webkit-app-region: drag;
}
.titlebar-logo {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-icon {
  font-size: 16px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.titlebar-controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}
.ctrl-btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.ctrl-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.ctrl-close:hover {
  background: #ef4444;
  color: white;
}
</style>
