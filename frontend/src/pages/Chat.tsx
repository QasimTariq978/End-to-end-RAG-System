import { useCallback, useEffect, useRef, useState } from 'react'
import { Menu, X } from 'lucide-react'

import { MessageInput } from '@/components/MessageInput'
import { MessageList, type ChatMessage } from '@/components/MessageList'
import { ThreadSidebar } from '@/components/ThreadSidebar'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'
import {
  createThread,
  deleteThread,
  listMessages,
  listThreads,
  streamMessage,
  type Thread,
} from '@/lib/api'
import { cn } from '@/lib/utils'

const PENDING_ID = 'pending-assistant'

function errorText(err: unknown) {
  return err instanceof Error ? err.message : String(err)
}

export default function Chat() {
  const { session, signOut } = useAuth()
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [searching, setSearching] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const refreshThreads = useCallback(async () => {
    try {
      setThreads(await listThreads())
    } catch (err) {
      setPageError(errorText(err))
    }
  }, [])

  useEffect(() => {
    refreshThreads()
    return () => abortRef.current?.abort()
  }, [refreshThreads])

  async function selectThread(id: string) {
    abortRef.current?.abort()
    setActiveId(id)
    setSidebarOpen(false)
    setMessages([])
    try {
      setMessages(await listMessages(id))
    } catch (err) {
      setPageError(errorText(err))
    }
  }

  function newChat() {
    abortRef.current?.abort()
    setActiveId(null)
    setMessages([])
    setSidebarOpen(false)
  }

  async function removeThread(id: string) {
    try {
      await deleteThread(id)
      if (id === activeId) newChat()
      setThreads((prev) => prev.filter((t) => t.id !== id))
    } catch (err) {
      setPageError(errorText(err))
    }
  }

  function updatePending(update: (m: ChatMessage) => ChatMessage) {
    setMessages((prev) => prev.map((m) => (m.id === PENDING_ID ? update(m) : m)))
  }

  async function send(content: string) {
    setPageError(null)
    setStreaming(true)
    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: 'user', content },
      { id: PENDING_ID, role: 'assistant', content: '' },
    ])

    try {
      let threadId = activeId
      if (!threadId) {
        threadId = (await createThread()).id
        setActiveId(threadId)
      }

      const controller = new AbortController()
      abortRef.current = controller
      await streamMessage(
        threadId,
        content,
        {
          onDelta: (text) => {
            setSearching(false)
            updatePending((m) => ({ ...m, content: m.content + text }))
          },
          onTool: (event) => setSearching(event.status === 'searching'),
          onDone: (messageId) => updatePending((m) => ({ ...m, id: messageId })),
          onError: (message) => updatePending((m) => ({ ...m, error: message })),
        },
        controller.signal,
      )
    } catch (err) {
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        updatePending((m) => ({ ...m, error: errorText(err) }))
      }
    } finally {
      // Give the placeholder a stable id if the stream ended without a "done" event.
      updatePending((m) => ({ ...m, id: `assistant-${Date.now()}` }))
      setSearching(false)
      setStreaming(false)
      refreshThreads()
    }
  }

  return (
    <div className="flex h-svh overflow-hidden">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 w-64 border-r transition-transform md:static md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <ThreadSidebar
          threads={threads}
          activeId={activeId}
          email={session?.user.email}
          onNew={newChat}
          onSelect={selectThread}
          onDelete={removeThread}
          onSignOut={signOut}
        />
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b px-3 py-2 md:hidden">
          <Button
            variant="ghost"
            size="icon"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            onClick={() => setSidebarOpen((open) => !open)}
          >
            {sidebarOpen ? <X /> : <Menu />}
          </Button>
          <span className="truncate text-sm font-medium">
            {threads.find((t) => t.id === activeId)?.title ?? 'New chat'}
          </span>
        </header>
        {pageError && (
          <p role="alert" className="border-b bg-destructive/10 px-4 py-2 text-sm text-destructive">
            {pageError}
          </p>
        )}
        <div className="min-h-0 flex-1 overflow-y-auto">
          <MessageList messages={messages} searching={searching} />
        </div>
        <div className="border-t">
          <MessageInput disabled={streaming} onSend={send} />
        </div>
      </main>
    </div>
  )
}
