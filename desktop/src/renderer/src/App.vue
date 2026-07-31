<script setup lang="ts">
import { ref } from 'vue'
import TitleBar from './components/TitleBar.vue'
import SchemaTree from './components/SchemaTree.vue'
import HistoryList from './components/HistoryList.vue'
import StatusBar from './components/StatusBar.vue'
import HomeView from './views/HomeView.vue'

const schemaTreeRef = ref<InstanceType<typeof SchemaTree> | null>(null)
const historyListRef = ref<InstanceType<typeof HistoryList> | null>(null)

function onHistorySelect(question: string) {
  // 点击历史记录后可以通过事件传递给 HomeView
  // 简化处理：向全局事件总线发送
  window.dispatchEvent(new CustomEvent('history-select', { detail: question }))
}
</script>

<template>
  <div class="app-shell">
    <TitleBar />
    <div class="app-body">
      <SchemaTree ref="schemaTreeRef" />
      <HomeView />
      <HistoryList ref="historyListRef" @select="onHistorySelect" />
    </div>
    <StatusBar />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-primary);
}
.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
