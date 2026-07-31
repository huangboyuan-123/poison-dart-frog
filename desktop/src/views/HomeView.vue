<script setup lang="ts">
import { ref } from 'vue'
import QueryInput from '../components/QueryInput.vue'
import SqlDisplay from '../components/SqlDisplay.vue'
import ResultTable from '../components/ResultTable.vue'
import AnswerPanel from '../components/AnswerPanel.vue'
import { queryDatabase, type QueryResponse } from '../api'

const queryInputRef = ref<InstanceType<typeof QueryInput> | null>(null)

const sql = ref<string | null>(null)
const data = ref<Record<string, unknown> | null>(null)
const answer = ref<string | null>(null)
const error = ref<string | null>(null)

async function handleSubmit(question: string) {
  // 清空之前的结果
  sql.value = null
  data.value = null
  answer.value = null
  error.value = null

  try {
    const res = await queryDatabase(question)
    const r: QueryResponse = res.data

    sql.value = r.sql ?? null
    data.value = r.data ?? null
    answer.value = r.answer ?? null
    error.value = r.error ?? null

    if (!r.success && !r.error) {
      error.value = '查询失败，请检查后端日志'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? '网络请求失败，请确认 API 服务是否已启动'
  }
}
</script>

<template>
  <div class="home-view">
    <div class="main-content">
      <!-- 输入区 -->
      <QueryInput ref="queryInputRef" @submit="handleSubmit" />

      <!-- 结果区 -->
      <div class="results-area">
        <!-- 等待状态 -->
        <div v-if="!sql && !answer && !error" class="empty-state">
          <div class="empty-icon">◆</div>
          <p class="empty-title">SQLAgent Desktop</p>
          <p class="empty-desc">输入自然语言问题，AI 将为你生成 SQL 并查询数据库</p>
        </div>

        <SqlDisplay :sql="sql" />
        <ResultTable :data="data" />
        <AnswerPanel :answer="answer" :error="error" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  overflow: hidden;
}
.results-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 48px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  opacity: 0.6;
}
.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
