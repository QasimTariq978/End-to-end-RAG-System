import { LogOut, MessageSquarePlus, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import type { Thread } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ThreadSidebarProps {
  threads: Thread[]
  activeId: string | null
  email?: string
  onNew: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onSignOut: () => void
}

export function ThreadSidebar({
  threads,
  activeId,
  email,
  onNew,
  onSelect,
  onDelete,
  onSignOut,
}: ThreadSidebarProps) {
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="p-3">
        <Button className="w-full justify-start" variant="outline" onClick={onNew}>
          <MessageSquarePlus />
          New chat
        </Button>
      </div>
      <ScrollArea className="min-h-0 flex-1 px-2">
        <ul className="flex flex-col gap-0.5 pb-2">
          {threads.map((thread) => (
            <li key={thread.id} className="group relative">
              <button
                type="button"
                onClick={() => onSelect(thread.id)}
                className={cn(
                  'w-full truncate rounded-md py-2 pr-9 pl-3 text-left text-sm hover:bg-sidebar-accent',
                  thread.id === activeId && 'bg-sidebar-accent font-medium',
                )}
                title={thread.title}
              >
                {thread.title}
              </button>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label={`Delete ${thread.title}`}
                className="absolute top-1/2 right-1 -translate-y-1/2 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                onClick={() => onDelete(thread.id)}
              >
                <Trash2 />
              </Button>
            </li>
          ))}
          {threads.length === 0 && (
            <li className="px-3 py-2 text-sm text-muted-foreground">No chats yet</li>
          )}
        </ul>
      </ScrollArea>
      <Separator />
      <div className="flex items-center gap-2 p-3">
        <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{email}</span>
        <Button variant="ghost" size="sm" onClick={onSignOut}>
          <LogOut />
          Sign out
        </Button>
      </div>
    </div>
  )
}
