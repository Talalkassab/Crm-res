'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Send, AlertCircle } from 'lucide-react'
import type { Conversation } from '@/types'

interface InterventionPanelProps {
  conversation: Conversation | null
  onSendMessage: (message: string) => Promise<void>
}

export function InterventionPanel({ conversation, onSendMessage }: InterventionPanelProps) {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)

  const handleSend = async () => {
    if (!message.trim() || !conversation) return

    setSending(true)
    try {
      await onSendMessage(message)
      setMessage('')
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!conversation) {
    return null
  }

  const isInterventionNeeded = conversation.status === 'escalated' || 
    (conversation.aiConfidence && conversation.aiConfidence < 0.5)

  return (
    <Card className="p-4">
      {isInterventionNeeded && (
        <div className="flex items-center gap-2 mb-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-md">
          <AlertCircle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800 dark:text-yellow-200">
            {isRTL 
              ? 'هذه المحادثة تحتاج إلى تدخل بشري'
              : 'This conversation requires human intervention'}
          </span>
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium mb-1 block">
            {isRTL ? 'إرسال رسالة' : 'Send Message'}
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="w-full min-h-[80px] p-2 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder={isRTL ? 'اكتب رسالتك هنا...' : 'Type your message here...'}
            disabled={sending || conversation.status === 'resolved'}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            {conversation.status === 'resolved' && (
              isRTL ? 'المحادثة مغلقة' : 'Conversation is resolved'
            )}
          </div>
          
          <Button
            onClick={handleSend}
            disabled={!message.trim() || sending || conversation.status === 'resolved'}
            size="sm"
          >
            {sending ? (
              isRTL ? 'جاري الإرسال...' : 'Sending...'
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                {isRTL ? 'إرسال' : 'Send'}
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  )
}