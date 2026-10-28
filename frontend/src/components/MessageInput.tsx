import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { SendHorizontal } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface MessageInputProps {
  disabled: boolean
  onSend: (content: string) => void
}

export function MessageInput({ disabled, onSend }: MessageInputProps) {
  const [value, setValue] = useState('')

  function submit() {
    const content = value.trim()
    if (!content || disabled) return
    onSend(content)
    setValue('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    submit()
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto flex w-full max-w-3xl items-end gap-2 p-4">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Message… (Enter to send, Shift+Enter for a new line)"
        disabled={disabled}
        rows={1}
        className="max-h-48 min-h-10 resize-none"
        aria-label="Message"
      />
      <Button type="submit" size="icon-lg" disabled={disabled || !value.trim()} aria-label="Send">
        <SendHorizontal />
      </Button>
    </form>
  )
}
