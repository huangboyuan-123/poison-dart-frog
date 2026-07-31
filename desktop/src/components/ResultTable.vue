<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ data: Record<string, unknown> | null }>()

const columns = computed(() => {
  if (!props.data?.columns) return []
  return (props.data.columns as string[]).map((col: string) => ({ prop: col, label: col }))
})

const rows = computed(() => {
  if (!props.data?.rows) return []
  return (props.data.rows as unknown[][]).map((row: unknown[]) => {
    const obj: Record<string, unknown> = {}
    columns.value.forEach((col, i) => { obj[col.prop] = row[i] })
    return obj
  })
})

const rowCount = computed(() => props.data?.row_count ?? 0)
const hasData = computed(() => columns.value.length > 0)
</script>

<template>
  <div v-if="hasData" class="result-table fade-in">
    <el-card>
      <template #header>
        <div class="result-header">
          <span class="result-label">📋 查询结果</span>
          <span class="result-count">{{ rowCount }} 行</span>
        </div>
      </template>
      <el-table
        :data="rows"
        stripe
        border
        size="small"
        max-height="300"
        empty-text="无数据"
      >
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          min-width="120"
          show-overflow-tooltip
        />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.result-table {
  margin-bottom: 12px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.result-count {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 10px;
  border-radius: 10px;
}
</style>
