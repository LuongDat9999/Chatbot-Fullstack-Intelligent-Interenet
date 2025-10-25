// utils/errorHandling.ts
import toast from 'react-hot-toast'

export interface ApiError {
  message: string
  status?: number
  code?: string
}

export const getErrorMessage = (error: any): string => {
  if (typeof error === 'string') return error
  if (error?.message) return error.message
  if (error?.error) return error.error
  return 'An unexpected error occurred'
}

export const getErrorHint = (error: any): string | null => {
  const message = getErrorMessage(error).toLowerCase()
  
  // API Key configuration errors
  if (message.includes('mock response') || message.includes('no api key')) {
    return "🔑 To use real AI responses, configure your OPENAI_API_KEY in the .env file. See env.example for setup instructions."
  }
  
  // CSV URL errors
  if (message.includes('csv') && message.includes('url')) {
    return "💡 Try adding '?raw=1' to GitHub URLs or ensure the URL points directly to a CSV file"
  }
  
  if (message.includes('decode') || message.includes('encoding')) {
    return "💡 The file might have encoding issues. Try saving as UTF-8 CSV"
  }
  
  if (message.includes('too large') || message.includes('size')) {
    return "💡 File is too large. Try uploading a smaller file or use URL instead"
  }
  
  if (message.includes('network') || message.includes('fetch')) {
    return "💡 Check your internet connection and try again"
  }
  
  if (message.includes('timeout')) {
    return "💡 Request timed out. The server might be busy, try again in a moment"
  }
  
  if (message.includes('unauthorized') || message.includes('401')) {
    return "💡 Authentication failed. Check your API key configuration"
  }
  
  if (message.includes('forbidden') || message.includes('403')) {
    return "💡 Access denied. You might not have permission for this resource"
  }
  
  if (message.includes('not found') || message.includes('404')) {
    return "💡 Resource not found. Check the URL or file path"
  }
  
  if (message.includes('server error') || message.includes('500')) {
    return "💡 Server error. Please try again later or contact support"
  }
  
  // File type errors
  if (message.includes('only csv files') || message.includes('only png and jpg')) {
    return "💡 Please check the file format and try uploading a supported file type"
  }
  
  return null
}

export const showErrorToast = (error: any, context?: string) => {
  const message = getErrorMessage(error)
  const hint = getErrorHint(error)
  
  const errorMessage = context ? `${context}: ${message}` : message
  
  toast.error(errorMessage, {
    duration: 5000,
    position: 'top-right',
    style: {
      background: '#0F1720',
      color: '#BAE9F4',
      border: '1px solid #264F68',
      borderRadius: '8px',
    },
  })
  
  if (hint) {
    setTimeout(() => {
      toast(hint, {
        duration: 8000,
        position: 'top-right',
        icon: '💡',
        style: {
          background: '#0F1720',
          color: '#81E1FF',
          border: '1px solid #81E1FF',
          borderRadius: '8px',
        },
      })
    }, 1000)
  }
}

export const showSuccessToast = (message: string) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
    style: {
      background: '#0F1720',
      color: '#BAE9F4',
      border: '1px solid #81E1FF',
      borderRadius: '8px',
    },
  })
}

export const showInfoToast = (message: string) => {
  toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: 'ℹ️',
    style: {
      background: '#0F1720',
      color: '#BAE9F4',
      border: '1px solid #264F68',
      borderRadius: '8px',
    },
  })
}
