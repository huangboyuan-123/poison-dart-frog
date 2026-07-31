import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // 窗口控制
  minimize: () => ipcRenderer.send('win:minimize'),
  maximize: () => ipcRenderer.send('win:maximize'),
  close: () => ipcRenderer.send('win:close'),
  isMaximized: () => ipcRenderer.invoke('win:isMaximized'),
  onMaximizeChange: (cb: (v: boolean) => void) =>
    ipcRenderer.on('win:maximize-change', (_, v) => cb(v)),

  // 数据库配置
  getDbConfigs: () => ipcRenderer.invoke('db:list'),
  saveDbConfig: (cfg: any) => ipcRenderer.invoke('db:save', cfg),
  deleteDbConfig: (id: string) => ipcRenderer.invoke('db:delete', id),
  testConnection: (cfg: any) => ipcRenderer.invoke('db:test', cfg),

  // SQL
  generateSql: (question: string) => ipcRenderer.invoke('sql:generate', question),
  runSql: (sql: string) => ipcRenderer.invoke('sql:run', sql),

  // 历史记录
  getHistory: () => ipcRenderer.invoke('history:list'),
  saveHistory: (item: any) => ipcRenderer.invoke('history:save', item),
  clearHistory: () => ipcRenderer.invoke('history:clear'),

  // 导出
  exportResult: (data: any, format: string) => ipcRenderer.invoke('export:result', data, format),
})
