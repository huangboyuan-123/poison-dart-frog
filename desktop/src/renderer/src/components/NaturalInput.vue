<script setup lang="ts">
import { ref } from 'vue'
import { Promotion, Delete } from '@element-plus/icons-vue'

const emit = defineEmits<{ generate: [question: string] }>()
const question = ref('')
const loading = ref(false)

async function onSubmit() {
  const q = question.value.trim()
  if (!q || loading.value) return
  loading.value = true
  emit('generate', q)
  loading.value = false
}

function onClear() { question.value = '' }
</script>

<template>
  <div class="input-section">
    <el-input
      v-model="question"
      type="textarea"
      :rows="6"
      placeholder="用中文描述你想要查询/修改的数据，例如：查询本月订单总数、统计每个用户消费金额"
      resize="vertical"
      class="nl-input"
      @keyup.ctrl.enter="onSubmit"
    />
    <div class="btn-row">
      <el-button type="primary" :loading="loading" :disabled="!question.trim()" @click="onSubmit">
        <el-icon><Promotion /></el-icon> 生成 SQL
      </el-button>
      <el-button @click="onClear" :disabled="!question">
        <el-icon><Delete /></el-icon> 清空输入
      </el-button>
      <span class="hint">Ctrl+Enter 发送</span>
    </div>
  </div>
</template>

<style scoped>
.input-section { padding: 10px; flex-shrink: 0; }
.nl-input { margin-bottom: 8px; }
.btn-row { display: flex; align-items: center; gap: 8px; }
.hint { font-size: 11px; color: var(--text-muted); margin-left: auto; }
</style>
