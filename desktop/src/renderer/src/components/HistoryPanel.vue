<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Clock, Delete } from '@element-plus/icons-vue'

const items = ref<HistoryItem[]>([])
const expanded = ref(false)

async function load() { items.value = await window.api.getHistory() }
onMounted(load)

async function onClear() {
  await window.api.clearHistory()
  items.value = []
}

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

// 监听新结果来刷新
window.addEventListener('sql-result', () => setTimeout(load, 500))
</script>

<template>
  <div class="history-wrap" :class="{ open: expanded }">
    <div class="history-header" @click="expanded = !expanded">
      <span class="hh-title"><el-icon><Clock /></el-icon> 历史记录 ({{ items.length }})</span>
      <div class="hh-actions">
        <el-button v-if="expanded && items.length" size="small" text :icon="Delete" @click.stop="onClear" />
        <span class="arrow">{{ expanded ? '▼' : '▲' }}</span>
      </div>
    </div>
    <div v-if="expanded" class="history-list">
      <div v-for="item in items" :key="item.id" class="h-item">
        <div class="hi-meta">
          <span :class="item.success ? 'ok' : 'err'">{{ item.success ? '✅' : '❌' }}</span>
          <span class="hi-time">{{ formatTime(item.timestamp) }}</span>
          <span class="hi-elapsed">{{ item.elapsed }}ms</span>
        </div>
        <pre class="hi-sql">{{ item.sql }}</pre>
      </div>
      <div v-if="!items.length" class="hi-empty">暂无历史记录</div>
    </div>
  </div>
</template>

<style scoped>
.history-wrap { border-top: 1px solid var(--border); flex-shrink: 0; }
.history-wrap.open { flex-shrink: 0; max-height: 40%; }
.history-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 12px; cursor: pointer; font-size: 11px; color: var(--text-gray);
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
  transition: background 0.15s;
}
.history-header:hover { background: var(--bg-hover); }
.hh-title { display: flex; align-items: center; gap: 6px; }
.hh-actions { display: flex; align-items: center; gap: 4px; }
.arrow { font-size: 10px; }
.history-list { max-height: 200px; overflow-y: auto; }
.h-item { padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 12px; }
.hi-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.hi-time { color: var(--text-muted); font-size: 11px; }
.hi-elapsed { color: var(--text-muted); font-size: 10px; }
.ok { color: var(--success); } .err { color: var(--danger); }
.hi-sql {
  font-family: var(--font-mono); font-size: 11px; color: var(--text-gray);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 100%;
}
.hi-empty { padding: 20px; text-align: center; color: var(--text-muted); font-size: 12px; }
</style>
