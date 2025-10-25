import React, { useEffect, useState, useRef } from 'react'
import { collection, query, orderBy, onSnapshot } from 'firebase/firestore'
import { db } from '../lib/firebase'
import { Message } from '../types'
import { MessageBubble } from './MessageBubble'
import { TypingIndicator } from './TypingIndicator'

interface ChatWindowProps {
  chatId: string | null
  isLoading: boolean
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ chatId, isLoading }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)
  const currentChatIdRef = useRef<string | null>(null)

  useEffect(() => {
    // CRITICAL: Cleanup previous listener FIRST to prevent leak
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    // CRITICAL: Update current chat ID reference
    currentChatIdRef.current = chatId

    if (!chatId) {
      setMessages([])
      return
    }

    console.log(`Setting up listener for chat: ${chatId}`)
    setMessages([]) // Xóa tin nhắn cũ

    // Listen to messages for this chat
    const q = query(
      collection(db, 'chats', chatId, 'messages'),
      orderBy('timestamp', 'asc')
    )

    const unsubscribe = onSnapshot(q, 
      (snapshot) => {
        // CRITICAL: Check if this is still the current chat to prevent state contamination
        if (currentChatIdRef.current !== chatId) {
          console.log('Skipping stale listener update for chat:', chatId)
          return
        }

        const messagesData: Message[] = []
        
        snapshot.forEach((doc) => {
          const data = doc.data()
          messagesData.push({
            id: parseInt(doc.id) || Date.now(),
            session_id: chatId,
            role: data.role,
            content: data.content || '', // Fallback for legacy messages
            ts: data.timestamp?.toDate?.()?.toISOString() || new Date().toISOString(),
            parts: data.parts || []
          })
        })

        // CRITICAL: Double-check chat ID before setting state
        if (currentChatIdRef.current === chatId) {
          setMessages(messagesData)
        }
      },
      (error) => {
        console.error(`[${chatId}] Error listening:`, error)
      }
    )

    // Store unsubscribe function for cleanup
    unsubscribeRef.current = unsubscribe

    return () => {
      console.log(`Cleaning up listener for chat: ${chatId}`)
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [chatId])

  // CRITICAL: Cleanup on unmount to prevent memory leak
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [])


  // Auto-scroll to bottom when new messages arrive or when loading state changes
  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }


  const renderMessage = (message: Message) => {
    return <MessageBubble key={message.id} message={message} />
  }

  if (!chatId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🤖</div>
          <h2 className="text-xl text-primaryText mb-2">Welcome to AI Assistant</h2>
          <p className="text-muted">Select a chat or create a new one to start</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages Container - Only this part scrolls */}
      <div 
        ref={listRef} 
        className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-3 min-h-0"
        style={{ maxHeight: 'calc(100vh - 200px)' }}
      >
        {/* Messages Container */}
        <div className="flex flex-col space-y-4">
          {messages.map(renderMessage)}

          {/* Spinner 'bot đang gõ' (state 'isLoading' từ props) */}
          {isLoading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  )
}
