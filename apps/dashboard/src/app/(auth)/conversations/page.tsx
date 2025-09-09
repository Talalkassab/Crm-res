'use client'

import { useEffect, useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { useRealtimeConversations } from '@/hooks/useRealtimeConversations'
import { ConversationList } from '@/components/conversations/conversation-list'
import { ConversationView } from '@/components/conversations/conversation-view'
import { InterventionPanel } from '@/components/conversations/intervention-panel'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Filter, RefreshCw } from 'lucide-react'
import type { Conversation } from '@/types'

export default function ConversationsPage() {
  const { ui, conversations, setActiveConversation, setConversationFilters } = useAppStore()
  const isRTL = ui.language === 'ar'
  const [selectedFilter, setSelectedFilter] = useState<Conversation['status'] | 'all'>('all')
  
  // Mock restaurant ID for now
  const restaurantId = 'rest1'
  const { refetch } = useRealtimeConversations(restaurantId)

  const activeConversation = conversations.items.find(c => c.id === conversations.activeId)

  const handleSelectConversation = (id: string) => {
    setActiveConversation(id)
  }

  const handleSendMessage = async (message: string): Promise<void> => {
    // Mock send message - will be replaced with real API call
    console.log('Sending message:', message)
    return new Promise((resolve) => setTimeout(() => resolve(), 1000))
  }

  const handleFilterChange = (filter: Conversation['status'] | 'all') => {
    setSelectedFilter(filter)
    if (filter === 'all') {
      setConversationFilters({})
    } else {
      setConversationFilters({ status: filter })
    }
  }

  const filteredConversations = selectedFilter === 'all' 
    ? conversations.items
    : conversations.items.filter(c => c.status === selectedFilter)

  const statusCounts = {
    all: conversations.items.length,
    active: conversations.items.filter(c => c.status === 'active').length,
    escalated: conversations.items.filter(c => c.status === 'escalated').length,
    resolved: conversations.items.filter(c => c.status === 'resolved').length,
    abandoned: conversations.items.filter(c => c.status === 'abandoned').length,
  }

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {isRTL ? 'المحادثات' : 'Conversations'}
          </h1>
          <p className="text-muted-foreground mt-1">
            {isRTL ? 'مراقبة وإدارة محادثات العملاء' : 'Monitor and manage customer conversations'}
          </p>
        </div>
        
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          {isRTL ? 'تحديث' : 'Refresh'}
        </Button>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2 overflow-x-auto">
        {(['all', 'active', 'escalated', 'resolved', 'abandoned'] as const).map((status) => (
          <Button
            key={status}
            variant={selectedFilter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFilterChange(status)}
            className="whitespace-nowrap"
          >
            {status === 'all' ? (isRTL ? 'الكل' : 'All') : status}
            <Badge variant="secondary" className="ml-2">
              {statusCounts[status]}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Conversation list */}
        <div className="lg:col-span-1">
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">
                {isRTL ? 'قائمة المحادثات' : 'Conversation List'}
              </h2>
              <Filter className="h-4 w-4 text-muted-foreground" />
            </div>
            
            {conversations.isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                {isRTL ? 'جاري التحميل...' : 'Loading...'}
              </div>
            ) : (
              <ConversationList
                conversations={filteredConversations}
                onSelectConversation={handleSelectConversation}
              />
            )}
          </Card>
        </div>

        {/* Conversation view and intervention */}
        <div className="lg:col-span-2 space-y-4">
          <div className="h-[500px]">
            <ConversationView conversation={activeConversation || null} />
          </div>
          
          <InterventionPanel
            conversation={activeConversation || null}
            onSendMessage={handleSendMessage}
          />
        </div>
      </div>
    </div>
  )
}