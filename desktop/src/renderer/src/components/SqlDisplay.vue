<script setup lang="ts">
import { computed } from 'vue'
import { DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{ sql: string | null }>()

const hasSql = computed(() => !!props.sql)

function copySql() {
  if (!props.sql) return
  navigator.clipboard.writeText(props.sql)
  ElMessage.success('SQL 已复制到剪贴板')
}

function highlightSQL(sql: string): string {
  // 简单的关键字高亮
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS',
    'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET', 'UNION',
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TABLE',
    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT',
    'DATE_SUB', 'DATE_ADD', 'NOW', 'CURRENT_TIMESTAMP',
    'INFORMATION_SCHEMA', 'TABLE_NAME', 'COLUMN_NAME',
  ]
  let escaped = sql
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 关键字高亮
  for (const kw of keywords) {
    const re = new RegExp(`\\b${kw}\\b`, 'gi')
    escaped = escaped.replace(re, `<span class="sql-kw">${kw}</span>`)
  }
  // 字符串高亮
  escaped = escaped.replace(/'([^']*)'/g, `<span class="sql-str">'$1'</span>`)
  // 数字高亮
  escaped = escaped.replace(/\b(\d+\.?\d*)\b/g, `<span class="sql-num">$1</span>`)

  return escaped
}
</script>

<template>
  <div v-if="hasSql" class="sql-display fade-in">
    <el-card>
      <template #header>
        <div class="sql-header">
          <span class="sql-label">💻 生成的 SQL</span>
          <el-button size="small" text @click="copySql">
            <el-icon><DocumentCopy /></el-icon> 复制
          </el-button>
        </div>
      </template>
      <pre class="sql-code" v-html="highlightSQL(sql!)"></pre>
    </el-card>
  </div>
</template>

<style scoped>
.sql-display {
  margin-bottom: 12px;
}
.sql-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sql-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sql-code {
  background: #0d1117;
  border: 1px solid rgba(99,102,241,0.1);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-primary);
}
.sql-code :deep(.sql-kw) { color: #c084fc; font-weight: 600; }
.sql-code :deep(.sql-str) { color: #34d399; }
.sql-code :deep(.sql-num) { color: #fbbf24; }
</style>
