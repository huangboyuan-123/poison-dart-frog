/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

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

interface SqlResult {
  success: boolean
  data: { columns: string[]; rows: any[][]; row_count: number } | null
  error: string | null
  sqlType?: string
  elapsed?: number
  affectedRows?: number
  blocked?: boolean
}

interface HistoryItem {
  id: string
  question: string
  sql: string
  elapsed: number
  success: boolean
  timestamp: string
}

interface WindowApi {
  minimize: () => void
  maximize: () => void
  close: () => void
  isMaximized: () => Promise<boolean>
  onMaximizeChange: (cb: (v: boolean) => void) => void
  getDbConfigs: () => Promise<DbConfig[]>
  saveDbConfig: (cfg: DbConfig) => Promise<{ ok: boolean }>
  deleteDbConfig: (id: string) => Promise<{ ok: boolean }>
  testConnection: (cfg: DbConfig) => Promise<{ ok: boolean; message: string }>
  generateSql: (question: string) => Promise<{ success: boolean; sql: string; answer: string; error: string | null }>
  runSql: (sql: string) => Promise<SqlResult>
  getHistory: () => Promise<HistoryItem[]>
  saveHistory: (item: Omit<HistoryItem, 'id' | 'timestamp'>) => Promise<{ ok: boolean }>
  clearHistory: () => Promise<{ ok: boolean }>
  exportResult: (data: any, format: string) => Promise<{ filePath: string }>
}

interface Window {
  api: WindowApi
}
