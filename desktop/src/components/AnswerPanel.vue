<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{ answer: string | null; error: string | null }>()

const renderedAnswer = computed(() => {
  if (!props.answer) return ''
  return marked(props.answer, { breaks: true }) as string
})

const hasContent = computed(() => !!props.answer || !!props.error)
</script>

<template>
  <div v-if="hasContent" class="answer-panel fade-in">
    <!-- 错误 -->
    <el-card v-if="error" class="error-card">
      <template #header>
        <span class="error-label">⚠️ 错误</span>
      </template>
      <p class="error-text">{{ error }}</p>
    </el-card>

    <!-- AI 分析 -->
    <el-card v-if="answer">
      <template #header>
        <span class="answer-label">🤖 AI 分析</span>
      </template>
      <div class="answer-content" v-html="renderedAnswer" />
    </el-card>
  </div>
</template>

<style scoped>
.answer-panel {
  margin-bottom: 12px;
}
.answer-label, .error-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.error-card {
  border-color: rgba(239,68,68,0.3) !important;
}
.error-text {
  color: var(--color-error);
  line-height: 1.6;
}
.answer-content {
  color: var(--text-primary);
  line-height: 1.8;
  font-size: 14px;
}
.answer-content :deep(p) { margin-bottom: 10px; }
.answer-content :deep(ul), .answer-content :deep(ol) { padding-left: 20px; margin-bottom: 10px; }
.answer-content :deep(li) { margin-bottom: 4px; }
.answer-content :deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  color: var(--accent-violet);
}
.answer-content :deep(pre) {
  background: #0d1117;
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  overflow-x: auto;
  margin-bottom: 10px;
}
.answer-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--text-primary);
}
.answer-content :deep(strong) { color: var(--accent-blue); }
.answer-content :deep(h1), .answer-content :deep(h2), .answer-content :deep(h3) {
  margin: 16px 0 8px;
  color: var(--text-primary);
}
</style>
