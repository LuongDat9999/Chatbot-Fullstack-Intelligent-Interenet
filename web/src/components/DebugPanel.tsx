import React, { useState } from 'react'
import { useChatStore } from '../store/chat'
import { api } from '../lib/api'

export const DebugPanel: React.FC = () => {
  const { sessionId } = useChatStore()
  const [isOpen, setIsOpen] = useState(false)
  const [meta, setMeta] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSessionMeta = async () => {
    if (!sessionId) {
      setError('No session ID available')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const result = await api.getSessionMeta(sessionId)
      setMeta(result.meta)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch session metadata')
    } finally {
      setLoading(false)
    }
  }

  const togglePanel = () => {
    if (!isOpen && !meta) {
      fetchSessionMeta()
    }
    setIsOpen(!isOpen)
  }

  // Only show in development
  if (import.meta.env.PROD) {
    return null
  }

  return (
    <div className="relative">
      <button
        onClick={togglePanel}
        className="text-xs text-muted hover:text-accent transition-colors px-2 py-1 rounded border border-muted/30 hover:border-accent/50"
        title="Debug Session Metadata (Dev Only)"
      >
        Debug
      </button>
      
      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-96 bg-surface border border-glow rounded-lg shadow-lg z-50">
          <div className="p-3 border-b border-glow">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-primaryText">Session Debug Info</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-muted hover:text-primaryText"
              >
                ✕
              </button>
            </div>
            <div className="text-xs text-muted mt-1">
              Session ID: {sessionId || 'None'}
            </div>
          </div>
          
          <div className="p-3 max-h-64 overflow-y-auto">
            {loading && (
              <div className="text-sm text-muted">Loading...</div>
            )}
            
            {error && (
              <div className="text-sm text-red-400">Error: {error}</div>
            )}
            
            {meta && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-primaryText">Metadata:</div>
                <pre className="text-xs text-muted bg-bg/50 p-2 rounded border overflow-x-auto">
                  {JSON.stringify(meta, null, 2)}
                </pre>
              </div>
            )}
            
            {!loading && !error && !meta && (
              <div className="text-sm text-muted">No metadata available</div>
            )}
          </div>
          
          <div className="p-3 border-t border-glow">
            <button
              onClick={fetchSessionMeta}
              disabled={loading}
              className="text-xs bg-accent/20 text-accent px-2 py-1 rounded hover:bg-accent/30 transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
