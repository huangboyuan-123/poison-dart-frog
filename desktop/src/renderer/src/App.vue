<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import TitleBar from './components/TitleBar.vue'
import LeftPanel from './components/LeftPanel.vue'
import RightPanel from './components/RightPanel.vue'
import StatusBar from './components/StatusBar.vue'

const splitX = ref(42)
const dragging = ref(false)
let startX = 0, startW = 0

function onMouseDown(e: MouseEvent) {
  dragging.value = true; startX = e.clientX; startW = splitX.value
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
function onMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  const dx = e.clientX - startX
  const w = startW + (dx / window.innerWidth) * 100
  splitX.value = Math.min(Math.max(w, 28), 72)
}
function onMouseUp() {
  dragging.value = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
}
</script>

<template>
  <div class="app-shell">
    <TitleBar />
    <div class="app-body">
      <div class="left-pane" :style="{ width: splitX + '%' }">
        <LeftPanel />
      </div>
      <div class="split-line" @mousedown="onMouseDown">
        <div class="split-handle" />
      </div>
      <div class="right-pane" :style="{ flex: 1 }">
        <RightPanel />
      </div>
    </div>
    <StatusBar />
  </div>
</template>

<style>
.app-shell { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.app-body { flex: 1; display: flex; min-height: 0; overflow: hidden; }
.left-pane { display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
.right-pane { display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
.split-line {
  width: 4px; cursor: col-resize; background: transparent;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: background 0.15s;
}
.split-line:hover, .split-line:active { background: var(--accent); }
.split-handle { width: 2px; height: 32px; background: var(--text-muted); border-radius: 1px; }
.split-line:hover .split-handle { background: white; }
</style>
