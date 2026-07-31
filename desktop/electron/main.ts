import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { join } from 'path'
import { registerDbConfigIpc } from './ipc/db-config'
import { registerSqlIpc } from './ipc/sql-runner'
import { registerHistoryIpc } from './ipc/history'

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 780,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    backgroundColor: '#1E2128',
    webPreferences: {
      preload: join(__dirname, '../preload/main.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // 窗口控制
  ipcMain.on('win:minimize', () => mainWindow?.minimize())
  ipcMain.on('win:maximize', () => {
    mainWindow?.isMaximized() ? mainWindow.unmaximize() : mainWindow?.maximize()
  })
  ipcMain.on('win:close', () => mainWindow?.close())
  ipcMain.handle('win:isMaximized', () => mainWindow?.isMaximized())

  mainWindow.on('maximize', () => mainWindow?.webContents.send('win:maximize-change', true))
  mainWindow.on('unmaximize', () => mainWindow?.webContents.send('win:maximize-change', false))

  mainWindow.on('ready-to-show', () => mainWindow?.show())

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  const url = process.env['ELECTRON_RENDERER_URL']
  if (url) {
    mainWindow.loadURL(url)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  registerDbConfigIpc()
  registerSqlIpc()
  registerHistoryIpc()
  createWindow()
  app.on('activate', () => { if (!BrowserWindow.getAllWindows().length) createWindow() })
})

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
