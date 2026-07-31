<script setup lang="ts">
import { inject, ref, computed } from 'vue'
import { DocumentCopy, VideoPlay, Download, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const sqlText = inject('sqlText', ref(''))
const generated = inject('generated', ref(false))

const executing = ref(false)
const useTx = ref(false)
const result = ref<SqlResult | null>(null)

// 通知右栏更新 (通过自定义事件)
const emit = defineEmits<{ result: [SqlResult] }>()

function highlightSQL(sql: string): string {
  let esc = sql.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const kw = ['SELECT','FROM','WHERE','AND','OR','NOT','IN','LIKE','BETWEEN','JOIN','LEFT','RIGHT','INNER','OUTER','ON','AS','GROUP BY','ORDER BY','HAVING','LIMIT','OFFSET','UNION','INSERT','UPDATE','DELETE','DROP','CREATE','ALTER','TABLE','INTO','VALUES','SET','COUNT','SUM','AVG','MAX','MIN','DISTINCT','DATE_SUB','DATE_ADD','NOW','CURRENT_TIMESTAMP','INFORMATION_SCHEMA','TABLE_NAME','COLUMN_NAME','EXPLAIN','INDEX','PRIMARY','KEY','FOREIGN','REFERENCES','CASCADE','NULL','NOT','DEFAULT','AUTO_INCREMENT','VARCHAR','INT','BIGINT','DECIMAL','TEXT','DATETIME','TIMESTAMP','BOOLEAN','FROM_UNIXTIME','UNIX_TIMESTAMP']
  for (const k of kw) {
    esc = esc.replace(new RegExp(`\\b${k}\\b`, 'gi'), m => `<span class="k">${m}</span>`)
  }
  esc = esc.replace(/'([^']*)'/g, `<span class="s">'$1'</span>`)
  esc = esc.replace(/\b(\d+\.?\d*)\b/g, `<span class="n">$1</span>`)
  return esc
}

async function onCopy() {
  if (!sqlText.value) return
  await navigator.clipboard.writeText(sqlText.value)
  ElMessage.success('SQL 已复制')
}

async function onExecute() {
  if (!sqlText.value || executing.value) return
  executing.value = true
  const r = await window.api.runSql(sqlText.value)
  result.value = r
  window.dispatchEvent(new CustomEvent('sql-result', { detail: r }))
  // 保存历史
  await window.api.saveHistory({ question: '', sql: sqlText.value, elapsed: r.elapsed || 0, success: r.success })
  executing.value = false
}

function onExport() {
  if (!result.value?.data) return
  const csv = [result.value.data.columns.join(',')]
    .concat(result.value.data.rows.map((r: any[]) => r.join(',')))
    .join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = 'result.csv'; a.click()
}
</script>

<template>
  <div class="sql-section">
    <div class="sql-header">
      <span class="sec-title">SQL 预览</span>
      <div class="sql-actions">
        <el-button size="small" text :icon="DocumentCopy" @click="onCopy" :disabled="!sqlText">复制</el-button>
      </div>
    </div>
    <pre class="sql-code" v-html="sqlText ? highlightSQL(sqlText) : '<span class=comment>-- AI 生成的 SQL 将显示在这里</span>'"></pre>
    <div class="sql-footer">
      <el-button type="primary" size="small" :icon="VideoPlay" :loading="executing" :disabled="!sqlText" @click="onExecute">执行 SQL</el-button>
      <el-button size="small" :icon="Download" :disabled="!result?.data" @click="onExport">导出 CSV</el-button>
      <el-checkbox v-model="useTx" size="small" class="tx-cb">开启事务</el-checkbox>
      <span v-if="result" class="exec-info" :class="{ err: !result.success }">
        <el-icon v-if="result.success"><Check /></el-icon>
        {{ result.success ? `${result.affectedRows ?? 0} 行 · ${result.elapsed}ms` : result.error }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.sql-section { flex: 1; display: flex; flex-direction: column; overflow: hidden; border-top: 1px solid var(--border); }
.sql-header { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; flex-shrink: 0; }
.sec-title { font-size: 11px; font-weight: 600; color: var(--text-gray); text-transform: uppercase; letter-spacing: 0.5px; }
.sql-actions { display: flex; gap: 2px; }
.sql-code {
  flex: 1; margin: 0 10px 8px; padding: 10px 12px; overflow: auto; white-space: pre;
  background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius);
  font-family: var(--font-mono); font-size: 12px; line-height: 1.7;
  color: var(--text-white); tab-size: 2;
}
.sql-code :deep(.k) { color: #6CB6FF; font-weight: 600; }
.sql-code :deep(.s) { color: #96D0A0; }
.sql-code :deep(.n) { color: #F0B679; }
.sql-code :deep(.comment) { color: var(--text-muted); font-style: italic; }
.sql-footer {
  display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  border-top: 1px solid var(--border); flex-shrink: 0;
}
.tx-cb { margin-left: auto; }
.exec-info { font-size: 11px; color: var(--success); display: flex; align-items: center; gap: 4px; }
.exec-info.err { color: var(--danger); }
</style>
