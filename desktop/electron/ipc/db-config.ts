import { ipcMain } from 'electron'
import Store from 'electron-store'
import { safeStorage } from 'electron'

const store = new Store({ name: 'db-configs', encryptionKey: 'sqlagent-db-key' })

interface DbConfig {
  id: string
  name: string
  type: 'mysql' | 'postgresql' | 'sqlserver' | 'sqlite'
  host: string
  port: number
  user: string
  password: string
  database: string
}

function encryptPass(pwd: string): string {
  if (safeStorage.isEncryptionAvailable()) {
    return safeStorage.encryptString(pwd).toString('base64')
  }
  return Buffer.from(pwd).toString('base64') // fallback
}

function decryptPass(enc: string): string {
  try {
    if (safeStorage.isEncryptionAvailable()) {
      return safeStorage.decryptString(Buffer.from(enc, 'base64'))
    }
  } catch {}
  return Buffer.from(enc, 'base64').toString()
}

export function registerDbConfigIpc() {
  ipcMain.handle('db:list', () => {
    const configs = (store.get('configs', []) as DbConfig[])
    return configs.map(c => ({ ...c, password: '••••••' })) // 隐藏密码
  })

  ipcMain.handle('db:save', (_, cfg: DbConfig) => {
    const configs = (store.get('configs', []) as DbConfig[])
    cfg.id = cfg.id || Date.now().toString(36)
    cfg.password = encryptPass(cfg.password)
    const idx = configs.findIndex(c => c.id === cfg.id)
    if (idx >= 0) configs[idx] = cfg
    else configs.push(cfg)
    store.set('configs', configs)
    return { ok: true }
  })

  ipcMain.handle('db:delete', (_, id: string) => {
    const configs = (store.get('configs', []) as DbConfig[]).filter(c => c.id !== id)
    store.set('configs', configs)
    return { ok: true }
  })

  ipcMain.handle('db:test', async (_, cfg: DbConfig) => {
    try {
      const axios = (await import('axios')).default
      const res = await axios.post('http://localhost:8000/api/execute', {
        sql: 'SELECT 1',
        read_only: true,
      }, { timeout: 5000 })
      return { ok: res.data.success, message: res.data.success ? '连接成功' : res.data.error }
    } catch (e: any) {
      return { ok: false, message: e?.message || '连接失败' }
    }
  })
}
