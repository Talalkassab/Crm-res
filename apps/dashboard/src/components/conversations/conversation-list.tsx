'use client'

import { useAppStore } from '@/stores/app-store'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  MessageSquare,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  User,
} from 'lucide-react'
import type { Conversation } from '@/types'

interface ConversationListProps {
  conversations: Conversation[]
  onSelectConversation: (id: string) => void
}

export function ConversationList({ conversations, onSelectConversation }: ConversationListProps) {
  const { ui, conversations: conversationState } = useAppStore()
  const isRTL = ui.language === 'ar'

  const getStatusIcon = (status: Conversation['status']) => {
    switch (status) {
      case 'active':
        return <MessageSquare className="h-4 w-4 text-blue-600" />
      case 'escalated':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'abandoned':
        return <XCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: Conversation['status']) => {
    const statusMap = {
      active: { en: 'Active', ar: 'نشط' },
      escalated: { en: 'Escalated', ar: 'تم التصعيد' },
      resolved: { en: 'Resolved', ar: 'تم الحل' },
      abandoned: { en: 'Abandoned', ar: 'مهجور' },
    }
    return statusMap[status][ui.language]
  }

  const getTypeText = (type: Conversation['type']) => {
    const typeMap = {
      feedback: { en: 'Feedback', ar: 'ملاحظات' },
      order: { en: 'Order', ar: 'طلب' },
      support: { en: 'Support', ar: 'دعم' },
      general: { en: 'General', ar: 'عام' },
    }
    return typeMap[type][ui.language]
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) {
      return isRTL ? 'الآن' : 'Just now'
    } else if (minutes < 60) {
      return isRTL ? `منذ ${minutes} دقيقة` : `${minutes}m ago`
    } else if (hours < 24) {
      return isRTL ? `منذ ${hours} ساعة` : `${hours}h ago`
    } else {
      return isRTL ? `منذ ${days} يوم` : `${days}d ago`
    }
  }

  if (conversations.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {isRTL ? 'لا توجد محادثات' : 'No conversations'}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {conversations.map((conversation) => {
        const lastMessage = conversation.messages[conversation.messages.length - 1]
        const isActive = conversationState.activeId === conversation.id

        return (
          <Card
            key={conversation.id}
            className={cn(
              'p-4 cursor-pointer transition-all hover:bg-accent/50',
              isActive && 'border-primary bg-accent'
            )}
            onClick={() => onSelectConversation(conversation.id)}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {getStatusIcon(conversation.status)}
                  <span className="font-medium text-sm">
                    {conversation.customer?.name || conversation.customer?.phoneNumber || 'Unknown'}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {getTypeText(conversation.type)}
                  </Badge>
                </div>
                
                {lastMessage && (
                  <p className="text-sm text-muted-foreground truncate">
                    {lastMessage.content}
                  </p>
                )}

                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTime(conversation.startedAt)}
                  </div>
                  {conversation.aiConfidence && (
                    <div className="flex items-center gap-1">
                      <span>AI:</span>
                      <span className={cn(
                        conversation.aiConfidence > 0.8 ? 'text-green-600' :
                        conversation.aiConfidence > 0.5 ? 'text-yellow-600' :
                        'text-red-600'
                      )}>
                        {Math.round(conversation.aiConfidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                {getStatusText(conversation.status)}
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}