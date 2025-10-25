// components/MessageBubble.tsx
import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message, MessagePart } from '../types'

interface MessageBubbleProps {
  message: Message
}

const renderMessagePart = (part: MessagePart, isUser: boolean) => {
  switch (part.type) {
    case 'text':
      return (
        <div className="text-primaryText">
          {isUser ? (
            <div className="whitespace-pre-wrap">{part.content}</div>
          ) : (
            <div className="max-w-full overflow-hidden break-words">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-invert prose-sm max-w-none break-words"
              components={{
                // Custom styling for markdown elements
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({ children, className }) => {
                  const isInline = !className
                  return isInline ? (
                    <code className="bg-bg/50 px-1 py-0.5 rounded text-accent text-sm">
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-bg/50 p-3 rounded text-accent text-sm overflow-x-auto">
                      {children}
                    </code>
                  )
                },
                pre: ({ children }) => (
                  <pre className="bg-bg/50 p-3 rounded overflow-x-auto mb-2 max-w-full whitespace-pre-wrap break-words">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-2 space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-primaryText">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="text-accent font-semibold">{children}</strong>
                ),
                em: ({ children }) => (
                  <em className="text-muted italic">{children}</em>
                ),
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold text-primaryText mb-2">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-lg font-bold text-primaryText mb-2">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-base font-bold text-primaryText mb-2">{children}</h3>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-accent pl-4 italic text-muted mb-2">
                    {children}
                  </blockquote>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto mb-2 max-w-full">
                    <table className="min-w-full border border-borderGlow rounded table-auto">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="border border-borderGlow px-3 py-2 bg-surface text-primaryText font-semibold text-left">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-borderGlow px-3 py-2 text-primaryText">
                    {children}
                  </td>
                ),
              }}
            >
              {part.content}
            </ReactMarkdown>
            </div>
          )}
        </div>
      )
    
    case 'image':
      return (
        <div className="mb-2">
          <div className="max-w-[280px] overflow-hidden rounded-xl border border-borderGlow/30 shadow">
            <img 
              src={part.content} 
              alt={part.filename || "uploaded image"} 
              className="block w-full h-auto" 
            />
          </div>
          {part.filename && (
            <div className="text-xs text-muted mt-1">
              📷 {part.filename}
            </div>
          )}
        </div>
      )
    
    case 'file':
      return (
        <div className="mb-2 p-3 bg-surface border border-glow rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="text-accent">📄</div>
            <div>
              <div className="text-primaryText text-sm font-medium">
                {part.filename || 'File'}
              </div>
              <a 
                href={part.content} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-accent text-xs hover:underline"
              >
                Download file
              </a>
            </div>
          </div>
        </div>
      )
    
    case 'file_url':
      return (
        <div className="mb-2 p-3 bg-surface border border-glow rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="text-accent">🔗</div>
            <div>
              <div className="text-primaryText text-sm font-medium">
                CSV from URL: {part.filename || 'CSV File'}
              </div>
              <a 
                href={part.url || part.content} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-accent text-xs hover:underline"
              >
                View source
              </a>
            </div>
          </div>
        </div>
      )
    
    default:
      return null
  }
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user'
  
  // Handle legacy image messages
  if (message.kind === 'image' && message.imageUrl) {
    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className="max-w-[280px] overflow-hidden rounded-xl border border-borderGlow/30 shadow">
          <img src={message.imageUrl} alt="uploaded" className="block w-full h-auto" />
        </div>
      </div>
    )
  }
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in mb-4`}>
      <div
        className={`max-w-[70%] p-4 rounded-lg border-glow hover:border-glow-accent transition-all ${
          isUser
            ? 'bg-accent/10 ml-12'
            : 'bg-surface mr-12'
        }`}
      >
        <div className="flex items-start space-x-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            isUser
              ? 'bg-accent text-bg'
              : 'bg-primaryText text-bg'
          }`}>
            {isUser ? '👤' : '🤖'}
          </div>
          <div className="flex-1">
            {/* Render message parts if available, otherwise fallback to legacy content */}
            {message.parts && message.parts.length > 0 ? (
              <div className="space-y-2">
                {message.parts.map((part, index) => (
                  <div key={index}>
                    {renderMessagePart(part, isUser)}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-primaryText">
                {isUser ? (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                ) : (
                  <div className="max-w-full overflow-hidden break-words">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="prose prose-invert prose-sm max-w-none break-words"
                    components={{
                      // Custom styling for markdown elements
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      code: ({ children, className }) => {
                        const isInline = !className
                        return isInline ? (
                          <code className="bg-bg/50 px-1 py-0.5 rounded text-accent text-sm">
                            {children}
                          </code>
                        ) : (
                          <code className="block bg-bg/50 p-3 rounded text-accent text-sm overflow-x-auto">
                            {children}
                          </code>
                        )
                      },
                      pre: ({ children }) => (
                        <pre className="bg-bg/50 p-3 rounded overflow-x-auto mb-2 max-w-full whitespace-pre-wrap break-words">
                          {children}
                        </pre>
                      ),
                      ul: ({ children }) => (
                        <ul className="list-disc list-inside mb-2 space-y-1">
                          {children}
                        </ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="list-decimal list-inside mb-2 space-y-1">
                          {children}
                        </ol>
                      ),
                      li: ({ children }) => (
                        <li className="text-primaryText">{children}</li>
                      ),
                      strong: ({ children }) => (
                        <strong className="text-accent font-semibold">{children}</strong>
                      ),
                      em: ({ children }) => (
                        <em className="text-muted italic">{children}</em>
                      ),
                      h1: ({ children }) => (
                        <h1 className="text-xl font-bold text-primaryText mb-2">{children}</h1>
                      ),
                      h2: ({ children }) => (
                        <h2 className="text-lg font-bold text-primaryText mb-2">{children}</h2>
                      ),
                      h3: ({ children }) => (
                        <h3 className="text-base font-bold text-primaryText mb-2">{children}</h3>
                      ),
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-accent pl-4 italic text-muted mb-2">
                          {children}
                        </blockquote>
                      ),
                      table: ({ children }) => (
                        <div className="overflow-x-auto mb-2 max-w-full">
                          <table className="min-w-full border border-borderGlow rounded table-auto">
                            {children}
                          </table>
                        </div>
                      ),
                      th: ({ children }) => (
                        <th className="border border-borderGlow px-3 py-2 bg-surface text-primaryText font-semibold text-left">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="border border-borderGlow px-3 py-2 text-primaryText">
                          {children}
                        </td>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                  </div>
                )}
              </div>
            )}
            <div className="text-xs text-muted mt-2">
              {new Date(message.ts).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
