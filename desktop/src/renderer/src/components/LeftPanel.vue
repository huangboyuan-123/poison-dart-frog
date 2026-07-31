<script setup lang="ts">
import { ref, provide } from 'vue'
import { Refresh, Plus, Connection } from '@element-plus/icons-vue'
import DbConfigDialog from './DbConfigDialog.vue'
import NaturalInput from './NaturalInput.vue'
import SqlPreview from './SqlPreview.vue'

const dbConfigs = ref<DbConfig[]>([])
const currentDb = ref<DbConfig | null>(null)
const showDialog = ref(false)
const testing = ref(false)
const testMsg = ref('')

async function loadConfigs() {
  dbConfigs.value = await window.api.getDbConfigs()
  if (!currentDb.value && dbConfigs.value.length) currentDb.value = dbConfigs.value[0]
}
loadConfigs()

async function onTest() {
  if (!currentDb.value) return
  testing.value = true
  const r = await window.api.testConnection(currentDb.value)
  testMsg.value = r.message
  testing.value = false
  setTimeout(() => { testMsg.value = '' }, 3000)
}

async function onSaved(cfg: DbConfig) {
  await window.api.saveDbConfig(cfg)
  showDialog.value = false
  await loadConfigs()
  currentDb.value = dbConfigs.value.find(c => c.id === cfg.id) || null
}

// 提供给子组件
const sqlText = ref('')
const generated = ref(false)
provide('sqlText', sqlText)
provide('generated', generated)

async function onGenerate(question: string) {
  generated.value = true
  const r = await window.api.generateSql(question)
  if (r.success && r.sql) {
    sqlText.value = r.sql
  } else {
    sqlText.value = `-- 生成失败: ${r.error || '未知错误'}`
  }
}
</script>

<template>
  <div class="left-panel">
    <!-- DB 配置栏 -->
    <div class="db-bar">
      <el-select v-model="currentDb" value-key="id" placeholder="选择数据库" size="small" class="db-select" @change="testMsg=''">
        <el-option v-for="c in dbConfigs" :key="c.id" :label="`${c.name} (${c.type})`" :value="c" />
      </el-select>
      <el-button size="small" :icon="Plus" circle @click="showDialog = true; currentDb = null" title="新增连接" />
      <el-button size="small" :icon="Connection" :type="testMsg ? (testMsg.includes('成功') ? 'success' : 'danger') : 'default'" :loading="testing" circle @click="onTest" title="测试连接" />
      <span v-if="testMsg" class="test-msg" :class="{ ok: testMsg.includes('成功') }">{{ testMsg }}</span>
    </div>

    <!-- 输入区 -->
    <NaturalInput @generate="onGenerate" />

    <!-- SQL 预览 -->
    <SqlPreview />
  </div>

  <DbConfigDialog v-if="showDialog" :config="currentDb" @save="onSaved" @close="showDialog = false" />
</template>

<style scoped>
.left-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.db-bar {
  display: flex; align-items: center; gap: 6px; padding: 8px 10px;
  border-bottom: 1px solid var(--border); flex-shrink: 0; background: var(--bg-panel);
}
.db-select { flex: 1; }
.test-msg { font-size: 11px; color: var(--danger); white-space: nowrap; }
.test-msg.ok { color: var(--success); }
</style>
