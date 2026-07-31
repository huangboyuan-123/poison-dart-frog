<script setup lang="ts">
import { ref, onMounted } from 'vue'
const isMax = ref(false)
const api = window.api

onMounted(async () => {
  isMax.value = await api.isMaximized()
  api.onMaximizeChange((v: boolean) => { isMax.value = v })
})
</script>

<template>
  <header class="titlebar">
    <div class="drag-area">
      <span class="logo">SQLAgent</span>
    </div>
    <div class="win-ctrls">
      <button @click="api.minimize()" title="最小化"><svg width="12" height="12"><line x1="2" y1="6" x2="10" y2="6" stroke="currentColor" stroke-width="1.5"/></svg></button>
      <button @click="api.maximize()" :title="isMax ? '还原' : '最大化'">
        <svg v-if="!isMax" width="12" height="12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        <svg v-else width="12" height="12"><rect x="3" y="1" width="6" height="6" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="1" y="3" width="6" height="6" fill="#1E2128" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
      <button class="btn-close" @click="api.close()" title="关闭"><svg width="12" height="12"><line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5"/></svg></button>
    </div>
  </header>
</template>

<style scoped>
.titlebar {
  height: 38px; display: flex; align-items: center;
  background: var(--bg-primary); border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.drag-area {
  flex: 1; height: 100%; display: flex; align-items: center;
  padding-left: 14px; -webkit-app-region: drag;
}
.logo { font-size: 12px; font-weight: 600; color: var(--text-gray); letter-spacing: 1px; }
.win-ctrls { display: flex; height: 100%; -webkit-app-region: no-drag; }
.win-ctrls button {
  width: 44px; border: none; background: transparent; color: var(--text-gray);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.win-ctrls button:hover { background: var(--bg-hover); color: var(--text-white); }
.btn-close:hover { background: var(--danger) !important; color: white !important; }
</style>
