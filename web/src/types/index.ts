// types/index.ts
export interface MessagePart {
  type: 'text' | 'image' | 'file' | 'file_url'
  content: string
  filename?: string
  url?: string
}

export interface Message {
  id: number
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  ts: string
  kind?: 'text' | 'image'
  imageUrl?: string
  parts?: MessagePart[]
}

export interface Session {
  id: string
  name: string
  lastMessage?: string
  createdAt: string
}

export interface CSVMeta {
  sessionId: string
  columns: string[]
  types: Record<string, string>
  stats: {
    rows: number
    original_rows: number
    columns: number
    sampled: boolean
    memory_usage: number
    detailed_stats: Record<string, any>
  }
  uploadedAt: string
}
