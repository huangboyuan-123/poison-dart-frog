<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const dbOk = ref(false)
const historyCount = ref(0)
let timer: any = null

async function check() {
  try {
    // 简单 ping 后端
    const res = await fetch('http://localhost:8000/health')
    const d = await res.json()
    dbOk.value = d.database === true
  } catch { dbOk.value = false }
  try {
    const h = await window.api.getHistory()
    historyCount.value = h.length
  } catch {}
}

onMounted(() => { check(); timer = setInterval(check, 15000) })
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <footer class="statusbar">
    <div class="s-left">
      <span class="dot" :class="dbOk ? 'ok' : 'err'" />
      <span>{{ dbOk ? 'MySQL 已连接' : 'MySQL 断开' }}</span>
    </div>
    <div class="s-right">
      <span>历史: {{ historyCount }} 条</span>
    </div>
  </footer>
</template>

<style scoped>
.statusbar {
  height: 26px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 12px; background: var(--bg-primary); border-top: 1px solid var(--border);
  font-size: 11px; color: var(--text-gray); flex-shrink: 0;
}
.s-left, .s-right { display: flex; align-items: center; gap: 6px; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot.ok { background: var(--success); box-shadow: 0 0 4px rgba(63,185,80,0.5); }
.dot.err { background: var(--danger); }
</style>
