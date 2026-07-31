<script setup lang="ts">
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const emit = defineEmits<{ submit: [question: string] }>()
const question = ref('')
const loading = ref(false)

async function onSubmit() {
  const q = question.value.trim()
  if (!q || loading.value) return
  loading.value = true
  try {
    await emit('submit', q)
  } finally {
    loading.value = false
  }
}

function onClear() {
  question.value = ''
}

defineExpose({ setLoading: (v: boolean) => { loading.value = v } })
</script>

<template>
  <div class="query-input-wrap">
    <div class="input-row">
      <el-input
        v-model="question"
        size="large"
        placeholder="输入自然语言问题，例如：查询过去30天销售额最高的10个产品"
        :disabled="loading"
        clearable
        @clear="onClear"
        @keyup.enter="onSubmit"
      >
        <template #prefix>
          <el-icon class="input-icon"><Promotion /></el-icon>
        </template>
      </el-input>
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        :disabled="!question.trim()"
        @click="onSubmit"
      >
        {{ loading ? '查询中...' : '发送' }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.query-input-wrap {
  margin-bottom: 12px;
}
.input-row {
  display: flex;
  gap: 10px;
}
.input-row :deep(.el-input) {
  flex: 1;
}
.input-icon {
  color: var(--accent-purple);
  font-size: 18px;
}
</style>
