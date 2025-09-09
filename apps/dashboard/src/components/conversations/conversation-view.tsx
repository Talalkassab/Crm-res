'use client'

import { useEffect, useRef } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { User, Bot, Headphones } from 'lucide-react'
import type { Conversation, Message } from '@/types'

interface ConversationViewProps {
  conversation: Conversation | null
}

export function ConversationView({ conversation }: ConversationViewProps) {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation?.messages])

  if (!conversation) {
    return (
      <Card className="h-full flex items-center justify-center text-muted-foreground">
        {isRTL ? 'اختر محادثة لعرضها' : 'Select a conversation to view'}
      </Card>
    )
  }

  const getSenderIcon = (sender: Message['sender']) => {
    switch (sender) {
      case 'customer':
        return <User className="h-4 w-4" />
      case 'ai':
        return <Bot className="h-4 w-4" />
      case 'agent':
        return <Headphones className="h-4 w-4" />
    }
  }

  const getSenderName = (sender: Message['sender']) => {
    const senderMap = {
      customer: { en: 'Customer', ar: 'العميل' },
      ai: { en: 'AI Assistant', ar: 'المساعد الذكي' },
      agent: { en: 'Agent', ar: 'الموظف' },
    }
    return senderMap[sender][ui.language]
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString(isRTL ? 'ar-SA' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getSentimentColor = (sentiment?: Message['metadata']['sentiment']) => {
    if (!sentiment) return ''
    switch (sentiment) {
      case 'positive':
        return 'text-green-600'
      case 'negative':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <Card className="h-full flex flex-col">
      {/* Conversation header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">
              {conversation.customer?.name || conversation.customer?.phoneNumber || 'Unknown Customer'}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={conversation.status === 'active' ? 'default' : 'outline'}>
                {conversation.status}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {isRTL ? 'نوع:' : 'Type:'} {conversation.type}
              </span>
              {conversation.aiConfidence && (
                <span className="text-sm text-muted-foreground">
                  AI: {Math.round(conversation.aiConfidence * 100)}%
                </span>
              )}
            </div>
          </div>
          {conversation.branch && (
            <div className="text-sm text-muted-foreground">
              {conversation.branch.name}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation.messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3',
              message.sender === 'customer' ? 'justify-start' : 'justify-end'
            )}
          >
            {message.sender === 'customer' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                {getSenderIcon(message.sender)}
              </div>
            )}
            
            <div className={cn(
              'max-w-[70%] space-y-1',
              message.sender !== 'customer' && 'text-right'
            )}>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{getSenderName(message.sender)}</span>
                <span>{formatTimestamp(message.timestamp)}</span>
                {message.metadata?.sentiment && (
                  <span className={getSentimentColor(message.metadata.sentiment)}>
                    {message.metadata.sentiment}
                  </span>
                )}
              </div>
              
              <div className={cn(
                'rounded-lg px-3 py-2 inline-block',
                message.sender === 'customer'
                  ? 'bg-muted'
                  : message.sender === 'ai'
                  ? 'bg-blue-100 dark:bg-blue-900/20'
                  : 'bg-primary text-primary-foreground'
              )}>
                <p className="text-sm whitespace-pre-wrap">
                  {isRTL && message.contentAr ? message.contentAr : message.content}
                </p>
              </div>

              {message.metadata?.confidence && (
                <div className="text-xs text-muted-foreground">
                  {isRTL ? 'الثقة:' : 'Confidence:'} {Math.round(message.metadata.confidence * 100)}%
                </div>
              )}
            </div>

            {message.sender !== 'customer' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                {getSenderIcon(message.sender)}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </Card>
  )
}