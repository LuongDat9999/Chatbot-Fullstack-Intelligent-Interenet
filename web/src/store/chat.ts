import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ChatState {
  sessionId: string | null
  csvMeta: {
    columns: string[]
    types: Record<string, string>
    rows: number
  } | null
  isUploading: boolean
  uploadError: string | null
  
  // Actions
  setSessionId: (sessionId: string | null) => void
  setCsvMeta: (meta: { columns: string[]; types: Record<string, string>; rows: number } | null) => void
  setIsUploading: (isUploading: boolean) => void
  setUploadError: (error: string | null) => void
  resetSession: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      sessionId: null,
      csvMeta: null,
      isUploading: false,
      uploadError: null,
      
      setSessionId: (sessionId) => set({ sessionId }),
      setCsvMeta: (csvMeta) => set({ csvMeta }),
      setIsUploading: (isUploading) => set({ isUploading }),
      setUploadError: (uploadError) => set({ uploadError }),
      resetSession: () => set({ 
        sessionId: null, 
        csvMeta: null, 
        isUploading: false, 
        uploadError: null 
      }),
    }),
    {
      name: 'chat-store',
      partialize: (state) => ({ sessionId: state.sessionId, csvMeta: state.csvMeta }),
    }
  )
)
