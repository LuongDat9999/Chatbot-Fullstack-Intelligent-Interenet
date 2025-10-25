// API client that matches the backend contract
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ApiResponse {
  ok: boolean
  error?: string
  [key: string]: any
}

interface CSVUploadResponse {
  ok: boolean
  columns?: string[]
  types?: Record<string, string>
  stats?: {
    rows: number
    original_rows: number
    columns: number
    sampled: boolean
    memory_usage: number
    detailed_stats: Record<string, any>
  }
  suggestions?: string[]
  error?: string
}

interface ImageChatResponse {
  ok: boolean
  assistant_message?: string
  text?: string
  preview?: string
  error?: string
}

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse(response: Response): Promise<any> {
  if (!response.ok) {
    try {
      const errorData = await response.json()
      console.error(`[API] Error Response - Status: ${response.status}, Error:`, errorData)
      throw new ApiError(errorData.error || response.statusText, response.status)
    } catch (parseError) {
      console.error(`[API] Error Response - Status: ${response.status}, Parse Error:`, parseError)
      throw new ApiError(response.statusText, response.status)
    }
  }
  
  return response.json()
}

export const api = {
  // CSV File Upload
  async uploadCSV(sessionId: string, file: File): Promise<CSVUploadResponse> {
    console.log(`[API] CSV Upload - Endpoint: /csv/upload, SessionId: ${sessionId}, Filename: ${file.name}`)
    
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('file', file)
    
    const response = await fetch(`${API_BASE_URL}/csv/upload`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set boundary for multipart
    })
    
    const result = await handleResponse(response)
    console.log(`[API] CSV Upload Result:`, result)
    return result
  },

  // CSV URL Upload
  async uploadCSVFromURL(sessionId: string, url: string): Promise<CSVUploadResponse> {
    console.log(`[API] CSV URL Upload - Endpoint: /csv/url, SessionId: ${sessionId}, URL: ${url}`)
    
    const response = await fetch(`${API_BASE_URL}/csv/url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        url: url
      })
    })
    
    const result = await handleResponse(response)
    console.log(`[API] CSV URL Upload Result:`, result)
    return result
  },

  // Image Upload
  async uploadImage(sessionId: string, imageFile: File, question?: string): Promise<ImageChatResponse> {
    console.log(`[API] Image Upload - Endpoint: /image-chat, SessionId: ${sessionId}, Filename: ${imageFile.name}, Question: ${question || 'none'}`)
    
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('image_file', imageFile)
    if (question) {
      formData.append('question', question)
    }
    
    const response = await fetch(`${API_BASE_URL}/image-chat`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set boundary for multipart
    })
    
    const result = await handleResponse(response)
    console.log(`[API] Image Upload Result:`, result)
    return result
  },

  // Chat endpoint
  async sendChatMessage(chatId: string, messageId: string): Promise<ApiResponse> {
    console.log(`[API] Chat Message - Endpoint: /chat, ChatId: ${chatId}, MessageId: ${messageId}`)
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId,
        message_id: messageId
      })
    })
    
    const result = await handleResponse(response)
    console.log(`[API] Chat Message Result:`, result)
    return result
  },

  // Debug endpoints
  async getSessionMeta(sessionId: string): Promise<{ meta: any }> {
    console.log(`[API] Debug Session Meta - Endpoint: /debug/session/${sessionId}`)
    
    const response = await fetch(`${API_BASE_URL}/debug/session/${sessionId}`)
    const result = await handleResponse(response)
    console.log(`[API] Debug Session Meta Result:`, result)
    return result
  },

  async healthCheck(): Promise<{ ok: boolean }> {
    const response = await fetch(`${API_BASE_URL}/health`)
    return handleResponse(response)
  }
}

export { ApiError }
