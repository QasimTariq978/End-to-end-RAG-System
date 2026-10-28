import { supabase } from '@/lib/supabase'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface Thread {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  thread_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ToolEvent {
  name: string
  status: 'searching' | 'done'
}

export interface StreamHandlers {
  onDelta: (text: string) => void
  onTool: (event: ToolEvent) => void
  onDone: (messageId: string) => void
  onError: (message: string) => void
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // Body wasn't JSON; fall through to the status text.
  }
  return `${res.status} ${res.statusText}`
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...(await authHeaders()), ...init.headers },
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res
}

export async function listThreads(): Promise<Thread[]> {
  return (await apiFetch('/api/threads')).json()
}

export async function createThread(): Promise<Thread> {
  return (await apiFetch('/api/threads', { method: 'POST' })).json()
}

export async function deleteThread(id: string): Promise<void> {
  await apiFetch(`/api/threads/${id}`, { method: 'DELETE' })
}

export async function listMessages(threadId: string): Promise<Message[]> {
  return (await apiFetch(`/api/threads/${threadId}/messages`)).json()
}

function dispatchEvent(raw: string, handlers: StreamHandlers) {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }
  if (dataLines.length === 0) return

  const data = JSON.parse(dataLines.join('\n'))
  switch (event) {
    case 'delta':
      handlers.onDelta(data.text)
      break
    case 'tool':
      handlers.onTool(data)
      break
    case 'done':
      handlers.onDone(data.message_id)
      break
    case 'error':
      handlers.onError(data.message)
      break
  }
}

/**
 * POST a message and read the SSE reply. EventSource can't send a POST body or an
 * Authorization header, so we parse the stream ourselves.
 */
export async function streamMessage(
  threadId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response
  try {
    res = await apiFetch(`/api/threads/${threadId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
      signal,
    })
  } catch (err) {
    handlers.onError(err instanceof Error ? err.message : String(err))
    return
  }
  if (!res.body) {
    handlers.onError('Response has no body')
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    // A chunk can end partway through an event, so only dispatch complete "\n\n"-terminated ones.
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      dispatchEvent(buffer.slice(0, boundary), handlers)
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf('\n\n')
    }
  }
  if (buffer.trim()) dispatchEvent(buffer, handlers)
}
