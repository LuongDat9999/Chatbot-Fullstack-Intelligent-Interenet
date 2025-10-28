import { useState } from 'react'
import { signOut } from 'firebase/auth'
import { auth } from './lib/firebase'
import { Login } from './components/Login'
import { ChatList } from './components/ChatList'
import { ChatWindow } from './components/ChatWindow'
import { MessageInput } from './components/MessageInput'
import { DebugPanel } from './components/DebugPanel'
import { useAuth } from './hooks/useAuth'
import { showErrorToast } from './utils/errorHandling'
import { useChatStore } from './store/chat'
import './App.css'

function App() {
  // Authentication
  const { user, loading } = useAuth()
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  
  // Chat store
  const { setSessionId, resetSession } = useChatStore()

  const handleLogout = async () => {
    try {
      await signOut(auth)
    } catch (error) {
      console.error('Logout error:', error)
      showErrorToast(error, 'Failed to logout')
    }
  }

  const handleSelectChat = (chatId: string) => {
    // Reset loading state immediately when switching chats
    setIsLoading(false)
    setSelectedChatId(chatId)
    
    // Set sessionId to match chatId (single source of truth)
    setSessionId(chatId)
  }
  
  const handleCreateChat = (chatId: string) => {
    // Handle new chat creation from MessageInput
    setSelectedChatId(chatId)
    setSessionId(chatId)
  }

  // Loading state
  if (loading) {
    return (
      <div className="h-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-primaryText">Loading...</p>
        </div>
      </div>
    )
  }

  // Not authenticated - show login
  if (!user) {
    return <Login />
  }

  return (
    <div className="h-screen bg-bg flex overflow-hidden">
      {/* Left Sidebar - Chat List */}
      <ChatList 
        user={user}
        selectedChatId={selectedChatId}
        onSelectChat={handleSelectChat}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header - Fixed */}
        <div className="bg-surface border-b border-glow-accent px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-primaryText text-glow">
                AI Fullstack Assignment
              </h1>
              <p className="text-muted text-sm mt-1">Chat with AI and analyze data</p>
            </div>
            
            {/* User Info, Debug & Logout */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user.photoURL ? (
                  <img
                    src={user.photoURL}
                    alt="Profile"
                    className="w-8 h-8 rounded-full"
                  />
                ) : (
                  <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center text-bg text-sm font-medium">
                    {user.email?.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <div className="text-sm font-medium text-primaryText">
                    {user.displayName || user.email?.split('@')[0]}
                  </div>
                  <div className="text-xs text-muted">
                    {user.email}
                  </div>
                </div>
              </div>
              
              {/* Debug Panel (dev only) */}
              <DebugPanel />
              
              <button
                onClick={handleLogout}
                className="text-muted hover:text-red-400 transition-colors p-1"
                title="Sign Out"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {/* Chat Window - Scrollable */}
        <ChatWindow chatId={selectedChatId} isLoading={isLoading} />

        {/* Message Input - Fixed */}
        <MessageInput 
          chatId={selectedChatId} 
          isLoading={isLoading} 
          setIsLoading={setIsLoading}
          onCreateChat={handleCreateChat}
        />
      </div>
    </div>
  )
}

export default App