import React, { useState, useEffect, useRef } from 'react'
import { collection, query, where, onSnapshot, addDoc, serverTimestamp, deleteDoc, doc } from 'firebase/firestore'
import { db } from '../lib/firebase'
import { User } from 'firebase/auth'

interface Chat {
  id: string
  title: string
  createdAt: any
  lastMessage?: string
  lastMessageTime?: any
}

interface ChatListProps {
  user: User | null
  selectedChatId: string | null
  onSelectChat: (chatId: string) => void
}

export const ChatList: React.FC<ChatListProps> = ({ user, selectedChatId, onSelectChat }) => {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const chatListRef = useRef<HTMLDivElement>(null)
  const selectedChatRef = useRef<HTMLButtonElement | null>(null)

  // Listen to user's chats
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

    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        console.log('Chats snapshot received. Count:', snapshot.size)
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
      },
      (error) => {
        console.error('Firestore listener error:', error)
      }
    )

    return () => unsubscribe()
  }, [user])

  // Focus and scroll to top when new chat is selected
  useEffect(() => {
    if (selectedChatId && chatListRef.current) {
      // Scroll to top with a slight delay to ensure DOM is updated
      setTimeout(() => {
        chatListRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
        // Focus the selected chat button for accessibility
        selectedChatRef.current?.focus()
      }, 50)
    }
  }, [selectedChatId])

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

  const handleNewChat = async () => {
    if (!user) return
    console.log('Creating new chat for user:', user.uid)
    if (isCreating) return
    setIsCreating(true)
    try {
      const docRef = await addDoc(collection(db, 'chats'), {
        userId: user.uid,
        title: 'New Chat',
        createdAt: serverTimestamp()
      })
      // Optionally select the new chat
      onSelectChat(docRef.id)
    } catch (error) {
      console.error('Error creating chat:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="w-80 bg-surface border-r border-borderGlow flex flex-col h-screen">
      {/* User Info & New Chat Button - Fixed */}
      <div className="p-4 border-b border-glow flex-shrink-0">
        <button
          onClick={handleNewChat}
          disabled={isCreating}
          className="w-full bg-accent text-bg px-4 py-2 rounded-lg font-medium hover:bg-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Create new chat"
        >
          {isCreating ? 'Creating...' : '+ New Chat'}
        </button>
      </div>

      {/* Chat List - Scrollable */}
      <div ref={chatListRef} className="flex-1 overflow-y-auto min-h-0">
        <div className="p-4 space-y-2">
          {chats.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-muted text-sm">No chats yet</div>
              <div className="text-muted text-xs mt-1">Create your first chat above</div>
            </div>
          ) : (
            chats.map((chat) => (
              <div key={chat.id} className="relative">
                <button
                  ref={selectedChatId === chat.id ? selectedChatRef : null}
                  onClick={() => onSelectChat(chat.id)}
                  aria-current={selectedChatId === chat.id ? 'page' : 'false'}
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

                {/* Three dots menu trigger */}
                <button
                  className="absolute top-2 right-2 text-muted hover:text-primaryText p-1 rounded"
                  title="More options"
                  onClick={(e) => {
                    e.stopPropagation()
                    setMenuOpenId((prev) => (prev === chat.id ? null : chat.id))
                  }}
                >
                  ⋯
                </button>

                {/* Dropdown menu */}
                {menuOpenId === chat.id && (
                  <div
                    className="absolute top-8 right-2 bg-surface border border-borderGlow rounded shadow-lg z-10"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      className="px-3 py-2 text-red-400 hover:bg-surface/60 w-full text-left disabled:opacity-50"
                      disabled={deletingId === chat.id}
                      onClick={async () => {
                        // Confirm deletion
                        const confirmed = window.confirm('Xác nhận xóa cuộc trò chuyện này?')
                        if (!confirmed) return
                        if (!user) return
                        try {
                          setDeletingId(chat.id)
                          console.log('Deleting chat:', chat.id)
                          await deleteDoc(doc(db, 'chats', chat.id))
                          setMenuOpenId(null)
                          if (selectedChatId === chat.id) {
                            onSelectChat('')
                          }
                        } catch (error) {
                          console.error('Error deleting chat:', error)
                        } finally {
                          setDeletingId(null)
                        }
                      }}
                    >
                      {deletingId === chat.id ? 'Đang xóa...' : 'Xóa' }
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
