import { ipcMain } from 'electron'

const DANGER_KEYWORDS = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM']

function checkDanger(sql: string): string | null {
  const upper = sql.toUpperCase()
  // DELETE FROM 不带 WHERE 危险
  if (upper.includes('DELETE FROM') && !upper.includes('WHERE')) {
    return '⚠️ DELETE FROM 缺少 WHERE 条件！执行将删除所有数据。请添加 WHERE 条件后重试。'
  }
  for (const kw of DANGER_KEYWORDS) {
    if (upper.includes(kw.toUpperCase())) {
      return `⚠️ 高危操作: ${kw}。该操作不可逆，确认执行？`
    }
  }
  return null
}

export function registerSqlIpc() {
  ipcMain.handle('sql:generate', async (_, question: string) => {
    try {
      const axios = (await import('axios')).default
      const res = await axios.post('http://localhost:8000/api/query', { question }, { timeout: 120000 })
      return {
        success: res.data.success,
        sql: res.data.sql || '',
        answer: res.data.answer || '',
        error: res.data.error || null,
      }
    } catch (e: any) {
      return { success: false, sql: '', answer: '', error: e?.message || 'AI 接口请求失败' }
    }
  })

  ipcMain.handle('sql:run', async (_, sql: string) => {
    // 高危拦截
    const danger = checkDanger(sql)
    if (danger) {
      return { success: false, error: danger, data: null, blocked: true }
    }

    const start = Date.now()
    try {
      const axios = (await import('axios')).default
      const isWrite = /^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)/i.test(sql)
      const res = await axios.post('http://localhost:8000/api/execute', {
        sql,
        read_only: !isWrite,  // 写操作允许执行
      }, { timeout: 30000 })

      return {
        success: res.data.success,
        data: res.data.data || null,
        error: res.data.error || null,
        sqlType: isWrite ? sql.trim().split(/\s+/)[0].toUpperCase() : 'SELECT',
        elapsed: Date.now() - start,
        affectedRows: res.data.data?.row_count ?? 0,
      }
    } catch (e: any) {
      return {
        success: false,
        error: e?.response?.data?.detail ?? e?.message ?? 'SQL 执行失败',
        data: null,
        elapsed: Date.now() - start,
      }
    }
  })
}
