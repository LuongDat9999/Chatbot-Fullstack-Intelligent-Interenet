import React from 'react'

export const TypingIndicator: React.FC = () => {
  return (
    // 'w-full' và 'justify-start' để căn lề trái
    <div className="w-full flex justify-start mb-4">
      <div className="flex items-center space-x-1 p-3 rounded-lg bg-surface border border-glow max-w-xs">
        <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-2 h-2 bg-accent rounded-full animate-bounce"></div>
      </div>
    </div>
  )
}
