<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getHealth, type HealthResponse } from '../api'

const health = ref<HealthResponse | null>(null)
const apiOnline = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

async function checkHealth() {
  try {
    const res = await getHealth()
    health.value = res.data
    apiOnline.value = true
  } catch {
    apiOnline.value = false
    health.value = null
  }
}

onMounted(() => {
  checkHealth()
  timer = setInterval(checkHealth, 15000) // 每15秒检查一次
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <footer class="status-bar">
    <div class="status-left">
      <span class="status-dot" :class="{ online: apiOnline, offline: !apiOnline }" />
      <span class="status-text">{{ apiOnline ? 'API 已连接' : 'API 离线' }}</span>
    </div>
    <div class="status-right">
      <span v-if="health" class="status-item">
        MySQL: {{ health.database ? 'OK' : '离线' }}
        <span class="mini-dot" :class="{ ok: health.database, fail: !health.database }" />
      </span>
      <span v-if="health" class="status-item">
        LLM: {{ health.llm ? 'OK' : '离线' }}
        <span class="mini-dot" :class="{ ok: health.llm, fail: !health.llm }" />
      </span>
      <span v-if="health" class="status-version">v{{ health.version }}</span>
    </div>
  </footer>
</template>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 28px;
  padding: 0 14px;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-default);
  flex-shrink: 0;
  font-size: 11px;
}
.status-left, .status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.status-dot.online { background: var(--color-success); box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.status-dot.offline { background: var(--color-error); }
.status-text { color: var(--text-secondary); }
.status-item { color: var(--text-muted); display: flex; align-items: center; gap: 4px; }
.mini-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  display: inline-block;
}
.mini-dot.ok { background: var(--color-success); }
.mini-dot.fail { background: var(--color-error); }
.status-version { color: var(--text-muted); }
</style>
