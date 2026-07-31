<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ data: { columns: string[]; rows: any[][]; row_count: number } }>()

const pageSize = 100
const currentPage = ref(1)

const totalPages = computed(() => Math.ceil(props.data.row_count / pageSize))
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return props.data.rows.slice(start, start + pageSize).map(row => {
    const obj: Record<string, any> = {}
    props.data.columns.forEach((c, i) => { obj[c] = row[i] ?? '' })
    return obj
  })
})

function onPrev() { if (currentPage.value > 1) currentPage.value-- }
function onNext() { if (currentPage.value < totalPages.value) currentPage.value++ }

function onCellCopy(val: any) {
  navigator.clipboard.writeText(String(val))
}
</script>

<template>
  <div class="table-wrap">
    <el-table :data="pagedRows" stripe size="small" max-height="100%">
      <el-table-column
        v-for="col in data.columns" :key="col" :prop="col" :label="col"
        min-width="120" show-overflow-tooltip
        @cell-click="(row: any) => onCellCopy(row[col])"
      />
    </el-table>
    <div v-if="totalPages > 1" class="pager">
      <el-button size="small" :disabled="currentPage <= 1" @click="onPrev">上一页</el-button>
      <span>{{ currentPage }} / {{ totalPages }}</span>
      <el-button size="small" :disabled="currentPage >= totalPages" @click="onNext">下一页</el-button>
      <span class="total">共 {{ data.row_count }} 行</span>
    </div>
  </div>
</template>

<style scoped>
.table-wrap { padding: 8px; height: 100%; display: flex; flex-direction: column; }
.table-wrap :deep(.el-table) { flex: 1; }
.pager { display: flex; align-items: center; gap: 8px; padding: 6px 0; justify-content: center; font-size: 12px; color: var(--text-gray); }
.total { margin-left: 8px; }
</style>
