import { contextBridge, ipcRenderer } from 'electron'

// 暴露安全的 IPC API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  isMaximized: () => ipcRenderer.invoke('window-is-maximized'),
  onMaximizeChange: (callback: (maximized: boolean) => void) => {
    ipcRenderer.on('window-maximize-change', (_event, maximized) => callback(maximized))
  },
})
