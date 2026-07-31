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
    emit('submit', q)
  } finally {
    loading.value = false
  }
}

defineExpose({ setLoading: (v: boolean) => { loading.value = v } })
</script>

<template>
  <div class="query-input-wrap">
    <div class="input-row">
      <el-input
        v-model="question"
        size="default"
        placeholder="输入自然语言问题，例如：查询过去30天销售额最高的10个产品"
        :disabled="loading"
        clearable
        @keyup.enter="onSubmit"
      >
        <template #prefix>
          <el-icon class="input-icon"><Promotion /></el-icon>
        </template>
      </el-input>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="!question.trim()"
        @click="onSubmit"
      >
        {{ loading ? '查询中' : '发送' }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.query-input-wrap {
  flex-shrink: 0;
  padding-bottom: 10px;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.input-row :deep(.el-input) {
  flex: 1;
}
.input-row :deep(.el-button) {
  height: 32px;
  padding: 0 16px;
  font-size: 13px;
}
.input-icon {
  color: var(--accent-purple);
  font-size: 16px;
}
</style>
