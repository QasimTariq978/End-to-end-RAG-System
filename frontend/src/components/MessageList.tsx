import { useEffect, useRef } from 'react'

import { cn } from '@/lib/utils'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  error?: string
}

interface MessageListProps {
  messages: ChatMessage[]
  searching: boolean
}

export function MessageList({ messages, searching }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, searching])

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-muted-foreground">
        Ask a question about your documents to get started.
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn('flex flex-col', message.role === 'user' ? 'items-end' : 'items-start')}
        >
          {(message.content || message.role === 'user') && (
            <div
              className={cn(
                'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap',
                message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted',
              )}
            >
              {message.content}
            </div>
          )}
          {message.error && (
            <p role="alert" className="mt-1 text-sm text-destructive">
              {message.error}
            </p>
          )}
        </div>
      ))}
      {searching && <p className="text-sm text-muted-foreground italic">Searching documents…</p>}
      <div ref={bottomRef} />
    </div>
  )
}
