import { ipcMain, app } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync } from 'fs'

const HISTORY_FILE = join(app.getPath('userData'), 'sql_history.json')

interface HistoryItem {
  id: string
  question: string
  sql: string
  elapsed: number
  success: boolean
  timestamp: string
}

function load(): HistoryItem[] {
  try {
    if (!existsSync(HISTORY_FILE)) return []
    return JSON.parse(readFileSync(HISTORY_FILE, 'utf-8'))
  } catch { return [] }
}

function save(items: HistoryItem[]) {
  writeFileSync(HISTORY_FILE, JSON.stringify(items.slice(-200), null, 2), 'utf-8')
}

export function registerHistoryIpc() {
  ipcMain.handle('history:list', () => load())

  ipcMain.handle('history:save', (_, item: HistoryItem) => {
    const items = load()
    item.id = Date.now().toString(36)
    item.timestamp = new Date().toISOString()
    items.push(item)
    save(items)
    return { ok: true }
  })

  ipcMain.handle('history:clear', () => {
    save([])
    return { ok: true }
  })
}
