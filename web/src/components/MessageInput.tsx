import React, { useState, useRef } from 'react'
import { collection, addDoc, serverTimestamp, doc, updateDoc, setDoc } from 'firebase/firestore'
import { db } from '../lib/firebase'
import { useAuth } from '../hooks/useAuth'
import { useChatStore } from '../store/chat'
import { api, ApiError } from '../lib/api'
import toast from 'react-hot-toast'

interface MessageInputProps {
  chatId: string | null
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  onMessageSent?: () => void
  onCreateChat?: (chatId: string) => void
}

export const MessageInput: React.FC<MessageInputProps> = ({ chatId, isLoading, setIsLoading, onMessageSent, onCreateChat }) => {
  const { user } = useAuth()
  const { sessionId, setCsvMeta, setIsUploading, csvMeta, isUploading, setSessionId } = useChatStore()
  
  const [textInput, setTextInput] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [pendingImagePreview, setPendingImagePreview] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  
  const csvFileInputRef = useRef<HTMLInputElement>(null)
  const imageFileInputRef = useRef<HTMLInputElement>(null)

  const handleCSVFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.name.toLowerCase().endsWith('.csv')) {
        toast.error('Only CSV files are allowed')
        return
      }
      
      // Validate file size (20MB)
      const maxSizeBytes = 20 * 1024 * 1024
      if (file.size > maxSizeBytes) {
        toast.error('File too large. Maximum size: 20MB')
        return
      }

      setSelectedFile(file)
      setUploadError(null)
    }
  }

  const handleImageFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
      if (!allowedTypes.includes(file.type)) {
        toast.error('Only PNG and JPG images are allowed')
        return
      }
      
      // Validate file size (10MB)
      const maxSizeBytes = 10 * 1024 * 1024
      if (file.size > maxSizeBytes) {
        toast.error('File too large. Maximum size: 10MB')
        return
      }

      // Create preview
      const preview = URL.createObjectURL(file)
      setPendingImagePreview(preview)
      setSelectedFile(file)
      setUploadError(null)
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    setUploadError(null)
    if (pendingImagePreview) {
      URL.revokeObjectURL(pendingImagePreview)
      setPendingImagePreview(null)
    }
    if (csvFileInputRef.current) {
      csvFileInputRef.current.value = ''
    }
    if (imageFileInputRef.current) {
      imageFileInputRef.current.value = ''
    }
  }

  const uploadCSVFile = async (file: File): Promise<void> => {
    if (!sessionId) {
      throw new Error('No session ID available')
    }

    console.log(`[MessageInput] Uploading CSV file - sessionId: ${sessionId}, filename: ${file.name}`)

    setIsUploading(true)
    setUploadError(null)

    try {
      const response = await api.uploadCSV(sessionId, file)
      
      if (response.ok) {
        // Update store with CSV metadata
        setCsvMeta({
          columns: response.columns || [],
          types: response.types || {},
          rows: response.stats?.rows || 0
        })
        
        // Show success toast
        toast.success('CSV uploaded successfully!')
        
        // Add system message
        await addSystemMessage('CSV uploaded successfully. You can try: "Summarize the dataset", "Show basic stats", or "Which column has the most missing values?"')
        
        // Show CSV attached badge (handled by parent component)
        console.log('CSV attached badge should be shown')
      } else {
        throw new Error(response.error || 'Upload failed')
      }
    } catch (error) {
      const errorMessage = error instanceof ApiError ? error.message : 'Failed to upload CSV'
      setUploadError(errorMessage)
      toast.error(errorMessage)
      throw error
    } finally {
      setIsUploading(false)
    }
  }

  const uploadCSVFromURL = async (url: string): Promise<void> => {
    if (!sessionId) {
      throw new Error('No session ID available')
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      const response = await api.uploadCSVFromURL(sessionId, url)
      
      if (response.ok) {
        // Update store with CSV metadata
        setCsvMeta({
          columns: response.columns || [],
          types: response.types || {},
          rows: response.stats?.rows || 0
        })
        
        // Show success toast
        toast.success('CSV uploaded successfully!')
        
        // Add system message
        await addSystemMessage('CSV uploaded successfully. You can try: "Summarize the dataset", "Show basic stats", or "Which column has the most missing values?"')
        
        console.log('CSV attached badge should be shown')
      } else {
        throw new Error(response.error || 'Upload failed')
      }
    } catch (error) {
      const errorMessage = error instanceof ApiError ? error.message : 'Failed to upload CSV'
      setUploadError(errorMessage)
      toast.error(errorMessage)
      throw error
    } finally {
      setIsUploading(false)
    }
  }

  const uploadImage = async (file: File, question?: string): Promise<void> => {
    if (!sessionId) {
      throw new Error('No session ID available')
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      const response = await api.uploadImage(sessionId, file, question)
      
      if (response.ok) {
        // Add user image message
        await addUserImageMessage(file, pendingImagePreview)
        
        // Add assistant response
        if (response.text) {
          await addAssistantMessage(response.text)
        }
        
        toast.success('Image processed successfully!')
      } else {
        throw new Error(response.error || 'Image processing failed')
      }
    } catch (error) {
      const errorMessage = error instanceof ApiError ? error.message : 'Failed to process image'
      setUploadError(errorMessage)
      toast.error(errorMessage)
      throw error
    } finally {
      setIsUploading(false)
      // Clean up preview
      if (pendingImagePreview) {
        URL.revokeObjectURL(pendingImagePreview)
        setPendingImagePreview(null)
      }
    }
  }

  const addSystemMessage = async (content: string) => {
    if (!chatId) return

    await addDoc(collection(db, 'chats', chatId, 'messages'), {
      role: 'system',
      timestamp: serverTimestamp(),
      parts: [{ type: 'text', content }]
    })
  }

  const addUserImageMessage = async (file: File, preview: string | null) => {
    if (!chatId) return

    await addDoc(collection(db, 'chats', chatId, 'messages'), {
      role: 'user',
      timestamp: serverTimestamp(),
      parts: [
        { type: 'image', content: preview || '', filename: file.name }
      ]
    })
  }

  const addAssistantMessage = async (content: string) => {
    if (!chatId) return

    await addDoc(collection(db, 'chats', chatId, 'messages'), {
      role: 'assistant',
      timestamp: serverTimestamp(),
      parts: [{ type: 'text', content }]
    })
  }

  const createNewChat = async (): Promise<string> => {
    if (!user) throw new Error('User not authenticated')
    
    // Create new chat document
    const chatRef = doc(collection(db, 'chats'))
    const chatId = chatRef.id
    
    // Set initial chat data
    await setDoc(chatRef, {
      userId: user.uid,
      title: 'New Chat',
      createdAt: serverTimestamp(),
      lastMessage: null,
      lastMessageTime: null
    })
    
    console.log(`[MessageInput] Created new chat: ${chatId}`)
    return chatId
  }

  const handleSend = async (e?: React.MouseEvent | React.FormEvent) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    
    if (isLoading || isUploading || !user) {
      return
    }

    if (!textInput.trim() && !selectedFile) {
      toast.error('Please enter a message or select a file')
      return
    }

    setIsLoading(true)

    try {
      // Create new chat if needed
      let currentChatId = chatId
      if (!currentChatId) {
        console.log('[MessageInput] Creating new chat for first message')
        currentChatId = await createNewChat()
        
        // Update session ID to match new chat ID
        setSessionId(currentChatId)
        
        // Notify parent component about new chat
        onCreateChat?.(currentChatId)
      }
      // Handle file uploads first (these are separate from chat messages)
      if (selectedFile) {
        if (selectedFile.name.toLowerCase().endsWith('.csv')) {
          // Upload CSV file
          await uploadCSVFile(selectedFile)
        } else if (selectedFile.type.startsWith('image/')) {
          // Upload image
          await uploadImage(selectedFile, textInput.trim() || undefined)
        }
        
        // Clear file selection
        removeFile()
        
        // If it was just a file upload, we're done
        if (!textInput.trim()) {
          setIsLoading(false)
          onMessageSent?.()
          return
        }
      }

      // Handle CSV URL detection (only if no file selected)
      let newTextInput = textInput.trim()
      if (!selectedFile) {
        const urlRegex = /(https?:\/\/[^\s]+(\.csv))(?=\s|$)/g
        const csvUrlMatch = newTextInput.match(urlRegex)

        if (csvUrlMatch) {
          const csvUrl = csvUrlMatch[0]
          console.log('Detected CSV URL:', csvUrl)
          
          // Upload CSV from URL
          await uploadCSVFromURL(csvUrl)
          
          // Remove URL from text prompt
          newTextInput = newTextInput.replace(csvUrl, '').trim()
        }
      }

      // Send plain text message (no attachment flags)
      if (newTextInput) {
        // Create user message document with plain text only
        const userMessageRef = await addDoc(collection(db, 'chats', currentChatId, 'messages'), {
          role: 'user',
          timestamp: serverTimestamp(),
          parts: [{
            type: 'text',
            content: newTextInput
          }]
        })

        // Update chat with last message info
        const chatRef = doc(db, 'chats', currentChatId)
        await updateDoc(chatRef, {
          lastMessage: newTextInput,
          lastMessageTime: serverTimestamp()
        })

        // Clear input
        setTextInput('')

        // Call backend API (relies on server-side session context)
        await api.sendChatMessage(currentChatId, userMessageRef.id)

        toast.success('Message sent!')
        onMessageSent?.()
      } else {
        // No text content after file upload, just clear loading
        setIsLoading(false)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      e.stopPropagation()
      handleSend(e)
    }
  }

  if (!chatId) {
    return (
      <div className="bg-surface border-t border-glow-accent px-6 py-4">
        <div className="text-center text-muted">
          Select a chat to start messaging
        </div>
      </div>
    )
  }

  return (
    <div className="bg-surface border-t border-glow-accent px-6 py-4 flex-shrink-0">
      {/* CSV Attached Badge */}
      {csvMeta && (
        <div className="mb-3 p-2 bg-green-500/20 border border-green-500/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="text-green-400">📊</div>
            <div className="text-green-400 text-sm font-medium">
              CSV attached ({csvMeta.rows} rows, {csvMeta.columns.length} columns)
            </div>
          </div>
        </div>
      )}

      {/* File Preview */}
      {selectedFile && (
        <div className="mb-3 p-3 bg-surface border border-glow rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="text-accent">
                {selectedFile.type.startsWith('image') ? '🖼️' : '📄'}
              </div>
              <div>
                <div className="text-primaryText text-sm font-medium">
                  {selectedFile.name}
                </div>
                <div className="text-muted text-xs">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-red-400 hover:text-red-300 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Image Preview */}
      {pendingImagePreview && (
        <div className="mb-3 p-3 bg-surface border border-glow rounded-lg">
          <img 
            src={pendingImagePreview} 
            alt="Preview" 
            className="max-w-xs max-h-32 object-contain rounded"
          />
        </div>
      )}

      {/* Upload Error */}
      {uploadError && (
        <div className="mb-3 p-2 bg-red-500/20 border border-red-500/30 rounded-lg">
          <div className="text-red-400 text-sm">{uploadError}</div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex space-x-3">
        {/* CSV File Input */}
        <button
          onClick={() => csvFileInputRef.current?.click()}
          disabled={isLoading || isUploading}
          className="flex-shrink-0 bg-blue-500/20 text-blue-400 px-3 py-2 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          title="Upload CSV file"
        >
          📊
        </button>

        <input
          ref={csvFileInputRef}
          type="file"
          accept=".csv"
          onChange={handleCSVFileSelect}
          className="hidden"
        />

        {/* Image File Input */}
        <button
          onClick={() => imageFileInputRef.current?.click()}
          disabled={isLoading || isUploading}
          className="flex-shrink-0 bg-purple-500/20 text-purple-400 px-3 py-2 rounded-lg hover:bg-purple-500/30 transition-colors disabled:opacity-50"
          title="Upload image"
        >
          🖼️
        </button>

        <input
          ref={imageFileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg"
          onChange={handleImageFileSelect}
          className="hidden"
        />

        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message or paste CSV URL..."
            disabled={isLoading || isUploading}
            className="w-full bg-surface border border-glow rounded-lg px-3 py-2 text-primaryText placeholder-muted focus:outline-none focus:border-glow-accent resize-none disabled:opacity-50"
            rows={1}
            style={{ minHeight: '40px', maxHeight: '120px' }}
          />
        </div>

        {/* Send Button */}
        <button
          type="button"
          onClick={(e) => handleSend(e)}
          disabled={isLoading || isUploading || (!textInput.trim() && !selectedFile)}
          className="flex-shrink-0 bg-accent text-bg px-4 py-2 rounded-lg font-medium hover:bg-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading || isUploading ? (
            <div className="flex items-center space-x-1">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-bg"></div>
              <span>...</span>
            </div>
          ) : (
            '➤'
          )}
        </button>
      </div>
    </div>
  )
}