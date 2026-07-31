<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getSchema, type SchemaResponse } from '../api'

const loading = ref(false)
const tables = ref<SchemaResponse['tables']>([])
const error = ref('')

interface TreeNode {
  label: string
  children?: TreeNode[]
}

function buildTree(schema: SchemaResponse['tables']): TreeNode[] {
  return schema.map((t) => ({
    label: t.table,
    children: (t.columns as Array<Record<string, unknown>>).map((c) => ({
      label: `${c.name}: ${c.type}`,
    })),
  }))
}

const treeData = ref<TreeNode[]>([])

async function loadSchema() {
  loading.value = true
  error.value = ''
  try {
    const res = await getSchema()
    tables.value = res.data.tables
    treeData.value = buildTree(res.data.tables)
  } catch (e: any) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadSchema)

defineExpose({ refresh: loadSchema })
</script>

<template>
  <aside class="schema-panel">
    <div class="panel-header">
      <span class="panel-title">📊 数据库结构</span>
      <el-button size="small" text :loading="loading" @click="loadSchema">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <div v-if="error" class="schema-error">{{ error }}</div>

    <el-tree
      v-else
      :data="treeData"
      node-key="label"
      :props="{ children: 'children', label: 'label' }"
      default-expand-all
      :indent="16"
      class="schema-tree"
    >
      <template #default="{ node, data }">
        <span class="tree-node" :class="{ 'is-table': !data.children }">
          {{ node.label }}
        </span>
      </template>
    </el-tree>

    <div v-if="tables.length === 0 && !loading && !error" class="schema-empty">
      暂无数据
    </div>
  </aside>
</template>

<style scoped>
.schema-panel {
  width: 220px;
  height: 100%;
  border-right: 1px solid var(--border-default);
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
.schema-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.schema-error, .schema-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}
.tree-node {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tree-node:not(.is-table) {
  color: var(--text-primary);
  font-weight: 500;
}
</style>
