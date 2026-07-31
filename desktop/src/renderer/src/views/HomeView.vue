<script setup lang="ts">
import { ref } from 'vue'
import QueryInput from '../components/QueryInput.vue'
import SqlDisplay from '../components/SqlDisplay.vue'
import ResultTable from '../components/ResultTable.vue'
import AnswerPanel from '../components/AnswerPanel.vue'
import { queryDatabase, type QueryResponse } from '../api'

const sql = ref<string | null>(null)
const data = ref<Record<string, unknown> | null>(null)
const answer = ref<string | null>(null)
const error = ref<string | null>(null)

async function handleSubmit(question: string) {
  sql.value = null; data.value = null; answer.value = null; error.value = null
  try {
    const res = await queryDatabase(question)
    const r: QueryResponse = res.data
    sql.value = r.sql ?? null
    data.value = r.data ?? null
    answer.value = r.answer ?? null
    error.value = r.error ?? null
    if (!r.success && !r.error) error.value = '查询失败'
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? '网络请求失败'
  }
}
</script>

<template>
  <div class="home-view">
    <QueryInput @submit="handleSubmit" />
    <div class="results-area">
      <div v-if="!sql && !answer && !error" class="empty-state">
        <span class="empty-icon">◆</span>
        <p class="empty-title">SQLAgent Desktop</p>
        <p class="empty-desc">输入自然语言问题，AI 将生成 SQL 并查询数据库</p>
      </div>
      <SqlDisplay :sql="sql" />
      <ResultTable :data="data" />
      <AnswerPanel :answer="answer" :error="error" />
    </div>
  </div>
</template>

<style scoped>
.home-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 12px 16px;
}
.results-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 2px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  padding-top: 60px;
}
.empty-icon {
  font-size: 40px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0.5;
  margin-bottom: 12px;
}
.empty-title { font-size: 18px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.empty-desc { font-size: 13px; }
</style>
