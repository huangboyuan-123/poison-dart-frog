<script setup lang="ts">
import TitleBar from './components/TitleBar.vue'
import SchemaTree from './components/SchemaTree.vue'
import HistoryList from './components/HistoryList.vue'
import StatusBar from './components/StatusBar.vue'
import HomeView from './views/HomeView.vue'
</script>

<template>
  <div class="app-shell">
    <TitleBar />
    <div class="app-body">
      <SchemaTree />
      <HomeView />
      <HistoryList />
    </div>
    <StatusBar />
  </div>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--bg-primary);
  color: var(--text-primary);
}
.app-body {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}
</style>
