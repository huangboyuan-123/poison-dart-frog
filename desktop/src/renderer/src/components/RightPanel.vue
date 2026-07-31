<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ResultTable from './ResultTable.vue'
import ResultLog from './ResultLog.vue'
import HistoryPanel from './HistoryPanel.vue'

const result = ref<SqlResult | null>(null)
const sqlType = ref('—')
const elapsed = ref('—')
const affectedRows = ref(0)

function onResult(e: CustomEvent) {
  const r = e.detail as SqlResult
  result.value = r
  elapsed.value = r.elapsed ? `${r.elapsed}ms` : '—'
  affectedRows.value = r.affectedRows ?? r.data?.row_count ?? 0
  sqlType.value = r.sqlType || 'SELECT'
}

onMounted(() => { window.addEventListener('sql-result', onResult as any) })
onUnmounted(() => { window.removeEventListener('sql-result', onResult as any) })
</script>

<template>
  <div class="right-panel">
    <!-- 执行状态栏 -->
    <div class="result-bar">
      <span class="rb-item">类型: <b>{{ sqlType }}</b></span>
      <span class="rb-item">耗时: <b>{{ elapsed }}</b></span>
      <span class="rb-item">行数: <b>{{ affectedRows }}</b></span>
      <span v-if="result" class="rb-status" :class="{ ok: result.success, err: !result.success }">
        {{ result.success ? '✅ 执行成功' : '❌ 执行失败' }}
      </span>
    </div>

    <!-- 结果区 -->
    <div class="result-area">
      <!-- SELECT 表格 -->
      <ResultTable v-if="result?.success && result.data?.columns?.length" :data="result.data" />

      <!-- DML/DDL 文本 -->
      <ResultLog v-else-if="result" :result="result" />

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <span class="empty-icon">▹</span>
        <p>在左侧输入问题并执行 SQL</p>
        <p class="sub">查询结果将显示在这里</p>
      </div>
    </div>

    <!-- 历史记录 -->
    <HistoryPanel />
  </div>
</template>

<style scoped>
.right-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.result-bar {
  display: flex; align-items: center; gap: 16px; padding: 6px 12px;
  border-bottom: 1px solid var(--border); flex-shrink: 0; background: var(--bg-panel);
  font-size: 12px; color: var(--text-gray);
}
.rb-item b { color: var(--text-white); font-weight: 500; }
.rb-status { margin-left: auto; font-weight: 600; }
.rb-status.ok { color: var(--success); }
.rb-status.err { color: var(--danger); }
.result-area { flex: 1; min-height: 0; overflow-y: auto; }
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; color: var(--text-muted);
}
.empty-icon { font-size: 36px; color: var(--text-muted); opacity: 0.3; margin-bottom: 8px; }
.empty-state p { font-size: 13px; }
.empty-state .sub { font-size: 11px; margin-top: 4px; }
</style>
