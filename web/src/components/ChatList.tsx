import React, { useState, useEffect } from 'react'
import { collection, query, where, onSnapshot } from 'firebase/firestore'
import { db } from '../lib/firebase'
import { useAuth } from '../hooks/useAuth'

interface Chat {
  id: string
  title: string
  createdAt: any
  lastMessage?: string
  lastMessageTime?: any
}

interface ChatListProps {
  selectedChatId: string | null
  onSelectChat: (chatId: string) => void
  onNewChat: () => void
}

export const ChatList: React.FC<ChatListProps> = ({ selectedChatId, onSelectChat, onNewChat }) => {
  const { user } = useAuth()
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setChats([])
      setLoading(false)
      return
    }

    // Listen to user's chats
    const q = query(
      collection(db, 'chats'),
      where('userId', '==', user.uid)
    )

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const chatsData: Chat[] = []
      
      snapshot.forEach((doc) => {
        const data = doc.data()
        chatsData.push({
          id: doc.id,
          title: data.title || 'New Chat',
          createdAt: data.createdAt,
          lastMessage: data.lastMessage,
          lastMessageTime: data.lastMessageTime
        })
      })

      // Sort by last message time or creation time
      chatsData.sort((a, b) => {
        const timeA = a.lastMessageTime || a.createdAt
        const timeB = b.lastMessageTime || b.createdAt
        return timeB?.toMillis() - timeA?.toMillis()
      })

      setChats(chatsData)
      setLoading(false)
    })

    return () => unsubscribe()
  }, [user])


  if (loading) {
    return (
      <div className="w-80 bg-surface border-r border-borderGlow flex flex-col h-screen">
        <div className="p-4 flex-shrink-0">
          <div className="animate-pulse">
            <div className="h-10 bg-gray-700 rounded mb-4"></div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="p-4 space-y-2">
            <div className="animate-pulse">
              <div className="h-16 bg-gray-700 rounded"></div>
              <div className="h-16 bg-gray-700 rounded"></div>
              <div className="h-16 bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-80 bg-surface border-r border-borderGlow flex flex-col h-screen">
      {/* User Info & New Chat Button - Fixed */}
      <div className="p-4 border-b border-glow flex-shrink-0">
        <button
          onClick={onNewChat}
          className="w-full bg-accent text-bg px-4 py-2 rounded-lg font-medium hover:bg-accent/80 transition-colors"
        >
          + New Chat
        </button>
      </div>

      {/* Chat List - Scrollable */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="p-4 space-y-2">
          {chats.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-muted text-sm">No chats yet</div>
              <div className="text-muted text-xs mt-1">Create your first chat above</div>
            </div>
          ) : (
            chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedChatId === chat.id
                    ? 'bg-accent/20 border border-glow-accent'
                    : 'hover:bg-surface/50 border border-transparent'
                }`}
              >
                <div className="font-medium text-primaryText truncate">
                  {chat.title}
                </div>
                {chat.lastMessage && (
                  <div className="text-sm text-muted truncate mt-1">
                    {chat.lastMessage}
                  </div>
                )}
                {chat.lastMessageTime && (
                  <div className="text-xs text-muted mt-1">
                    {chat.lastMessageTime.toDate().toLocaleDateString()}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
