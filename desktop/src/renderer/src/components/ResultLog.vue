<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ result: SqlResult }>()
const rolling = ref(false)

async function onRollback() {
  rolling.value = true
  // 执行 ROLLBACK
  await window.api.runSql('ROLLBACK')
  rolling.value = false
}
</script>

<template>
  <div class="log-wrap">
    <!-- 高危拦截 -->
    <div v-if="result.blocked" class="log danger">
      <p class="log-title">🚫 高危操作被拦截</p>
      <p>{{ result.error }}</p>
    </div>

    <!-- 成功 DML/DDL -->
    <div v-else-if="result.success" class="log success">
      <p class="log-title">✅ 执行成功</p>
      <p>受影响行数: {{ result.affectedRows ?? 0 }}</p>
      <p>耗时: {{ result.elapsed }}ms</p>
      <p v-if="result.sqlType !== 'SELECT'" class="hint">
        ⚠️ 已执行 {{ result.sqlType }} 操作，请确认数据无误
      </p>
      <el-button v-if="result.sqlType !== 'SELECT'" type="danger" size="small" :loading="rolling" @click="onRollback">
        回滚事务
      </el-button>
    </div>

    <!-- 失败 -->
    <div v-else class="log danger">
      <p class="log-title">❌ 执行失败</p>
      <p>{{ result.error }}</p>
      <p v-if="result.elapsed">耗时: {{ result.elapsed }}ms</p>
    </div>
  </div>
</template>

<style scoped>
.log-wrap { padding: 16px; }
.log { padding: 16px; border-radius: var(--radius); border: 1px solid; }
.log.success { border-color: rgba(63,185,80,0.3); background: rgba(63,185,80,0.06); }
.log.danger { border-color: rgba(224,85,85,0.3); background: rgba(224,85,85,0.06); color: var(--danger); }
.log-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.log.success .log-title { color: var(--success); }
.log p { margin-bottom: 4px; font-size: 13px; line-height: 1.6; }
.log .hint { color: var(--warning); font-size: 12px; margin-top: 8px; }
</style>
