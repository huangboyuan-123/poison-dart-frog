<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getHistory, type HistoryResponse } from '../api'

const emit = defineEmits<{ select: [question: string] }>()

const items = ref<HistoryResponse['items']>([])
const loading = ref(false)

async function loadHistory() {
  loading.value = true
  try {
    const res = await getHistory()
    items.value = res.data.items.filter((i) => i.role === 'user')
  } catch {
    // 静默失败
  } finally {
    loading.value = false
  }
}

function onClick(item: { role: string; content: string }) {
  emit('select', item.content)
}

onMounted(loadHistory)

defineExpose({ refresh: loadHistory })
</script>

<template>
  <aside class="history-panel">
    <div class="panel-header">
      <span class="panel-title">📜 历史记录</span>
      <el-button size="small" text :loading="loading" @click="loadHistory">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <div v-if="items.length === 0 && !loading" class="history-empty">
      暂无记录
    </div>

    <div class="history-list">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="history-item"
        @click="onClick(item)"
      >
        <span class="history-index">{{ i + 1 }}</span>
        <span class="history-text">{{ item.content }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.history-panel {
  width: 200px;
  height: 100%;
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-default);
}
.panel-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}
.history-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 2px solid transparent;
}
.history-item:hover {
  background: var(--bg-hover);
  border-left-color: var(--accent-purple);
}
.history-index {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
}
.history-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
}
.history-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
