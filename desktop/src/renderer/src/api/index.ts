import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── 类型定义 ──

export interface QueryResponse {
  success: boolean
  question: string
  sql: string | null
  data: Record<string, unknown> | null
  answer: string | null
  error: string | null
}

export interface ExecuteResponse {
  success: boolean
  sql: string
  data: Record<string, unknown> | null
  error: string | null
}

export interface HealthResponse {
  status: string
  database: boolean
  llm: boolean
  version: string
}

export interface SchemaResponse {
  database: string
  tables: Array<{
    table: string
    columns: Array<Record<string, unknown>>
  }>
}

export interface HistoryResponse {
  total: number
  items: Array<{ role: string; content: string }>
}

// ── API 方法 ──

export function queryDatabase(question: string): Promise<{ data: QueryResponse }> {
  return api.post('/api/query', { question })
}

export function executeSQL(sql: string, readOnly = true): Promise<{ data: ExecuteResponse }> {
  return api.post('/api/execute', { sql, read_only: readOnly })
}

export function getHealth(): Promise<{ data: HealthResponse }> {
  return api.get('/health')
}

export function getSchema(): Promise<{ data: SchemaResponse }> {
  return api.get('/api/schema')
}

export function getTableSchema(table: string): Promise<{ data: Record<string, unknown> }> {
  return api.get(`/api/schema/${table}`)
}

export function getHistory(): Promise<{ data: HistoryResponse }> {
  return api.get('/api/history')
}

export default api
