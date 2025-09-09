'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  ChevronLeft,
  ChevronRight,
  User,
  Bot,
  Headphones,
  MessageSquare,
  Calendar,
  Phone,
} from 'lucide-react'
import type { Conversation, Message } from '@/types'

interface MessageHistoryProps {
  conversations: Conversation[]
  searchQuery?: string
  isLoading?: boolean
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function MessageHistory({
  conversations,
  searchQuery,
  isLoading,
  currentPage,
  totalPages,
  onPageChange,
}: MessageHistoryProps) {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  const [expandedConversations, setExpandedConversations] = useState<Set<string>>(new Set())

  const toggleExpanded = (conversationId: string) => {
    const newExpanded = new Set(expandedConversations)
    if (newExpanded.has(conversationId)) {
      newExpanded.delete(conversationId)
    } else {
      newExpanded.add(conversationId)
    }
    setExpandedConversations(newExpanded)
  }

  const highlightSearchTerm = (text: string, query?: string) => {
    if (!query || query.length < 2) return text

    const regex = new RegExp(`(${query})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  const getSenderIcon = (sender: Message['sender']) => {
    switch (sender) {
      case 'customer':
        return <User className="h-4 w-4 text-blue-600" />
      case 'ai':
        return <Bot className="h-4 w-4 text-purple-600" />
      case 'agent':
        return <Headphones className="h-4 w-4 text-green-600" />
    }
  }

  const getSenderName = (sender: Message['sender']) => {
    const senderMap = {
      customer: { en: 'Customer', ar: 'العميل' },
      ai: { en: 'AI', ar: 'الذكي' },
      agent: { en: 'Agent', ar: 'الموظف' },
    }
    return senderMap[sender][ui.language]
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString(isRTL ? 'ar-SA' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2" />
          <p className="text-muted-foreground">
            {isRTL ? 'جاري البحث...' : 'Searching...'}
          </p>
        </div>
      </div>
    )
  }

  if (conversations.length === 0) {
    return (
      <Card className="p-8 text-center">
        <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="font-semibold text-lg mb-2">
          {isRTL ? 'لا توجد محادثات' : 'No conversations found'}
        </h3>
        <p className="text-muted-foreground">
          {searchQuery 
            ? (isRTL ? 'لم يتم العثور على نتائج لبحثك' : 'No results found for your search')
            : (isRTL ? 'لا توجد محادثات متاحة' : 'No conversations available')
          }
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search results summary */}
      {searchQuery && (
        <div className="text-sm text-muted-foreground">
          {isRTL 
            ? `تم العثور على ${conversations.length} نتيجة للبحث عن "${searchQuery}"`
            : `Found ${conversations.length} results for "${searchQuery}"`
          }
        </div>
      )}

      {/* Message history list */}
      <div className="space-y-4">
        {conversations.map((conversation) => {
          const isExpanded = expandedConversations.has(conversation.id)
          const visibleMessages = isExpanded ? conversation.messages : conversation.messages.slice(-2)
          
          return (
            <Card key={conversation.id} className="p-4">
              {/* Conversation header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">
                      {conversation.customer?.name || conversation.customer?.phoneNumber || 'Unknown'}
                    </span>
                    <Badge variant={conversation.status === 'active' ? 'default' : 'secondary'}>
                      {conversation.status}
                    </Badge>
                    <Badge variant="outline">{conversation.type}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(conversation.startedAt)}
                    </span>
                    <span>
                      {conversation.messages.length} {isRTL ? 'رسالة' : 'messages'}
                    </span>
                    {conversation.branch && (
                      <span>{conversation.branch.name}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="space-y-2">
                {!isExpanded && conversation.messages.length > 2 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(conversation.id)}
                    className="text-muted-foreground"
                  >
                    {isRTL 
                      ? `عرض ${conversation.messages.length - 2} رسالة أخرى`
                      : `Show ${conversation.messages.length - 2} more messages`
                    }
                  </Button>
                )}

                {visibleMessages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex gap-3 p-2 rounded-lg',
                      message.sender === 'customer' ? 'bg-blue-50' : 'bg-gray-50'
                    )}
                  >
                    <div className="flex-shrink-0 mt-1">
                      {getSenderIcon(message.sender)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium">
                          {getSenderName(message.sender)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(message.timestamp)}
                        </span>
                        {message.metadata?.confidence && (
                          <Badge variant="outline" className="text-xs">
                            {Math.round(message.metadata.confidence * 100)}%
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm">
                        {highlightSearchTerm(
                          isRTL && message.contentAr ? message.contentAr : message.content,
                          searchQuery
                        )}
                      </p>
                    </div>
                  </div>
                ))}

                {isExpanded && conversation.messages.length > 2 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(conversation.id)}
                    className="text-muted-foreground"
                  >
                    {isRTL ? 'إخفاء الرسائل' : 'Hide messages'}
                  </Button>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
            {isRTL ? 'السابق' : 'Previous'}
          </Button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNumber
              if (totalPages <= 5) {
                pageNumber = i + 1
              } else if (currentPage <= 3) {
                pageNumber = i + 1
              } else if (currentPage >= totalPages - 2) {
                pageNumber = totalPages - 4 + i
              } else {
                pageNumber = currentPage - 2 + i
              }

              return (
                <Button
                  key={pageNumber}
                  variant={currentPage === pageNumber ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onPageChange(pageNumber)}
                  className="w-8 h-8 p-0"
                >
                  {pageNumber}
                </Button>
              )
            })}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
          >
            {isRTL ? 'التالي' : 'Next'}
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Results info */}
      <div className="text-center text-sm text-muted-foreground">
        {isRTL 
          ? `الصفحة ${currentPage} من ${totalPages}`
          : `Page ${currentPage} of ${totalPages}`
        }
      </div>
    </div>
  )
}