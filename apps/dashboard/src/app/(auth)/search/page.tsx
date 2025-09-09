'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/stores/app-store'
import { SearchInterface } from '@/components/conversations/search-interface'
import { MessageHistory } from '@/components/conversations/message-history'
import type { Conversation } from '@/types'

interface SearchFilters {
  query: string
  phoneNumber: string
  dateRange: {
    from: string
    to: string
  }
  branchId: string
  conversationType: 'all' | 'feedback' | 'order' | 'support' | 'general'
}

interface SearchState {
  conversations: Conversation[]
  isLoading: boolean
  currentPage: number
  totalPages: number
  totalResults: number
}

export default function SearchPage() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  
  const [searchState, setSearchState] = useState<SearchState>({
    conversations: [],
    isLoading: false,
    currentPage: 1,
    totalPages: 0,
    totalResults: 0,
  })
  
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>({
    query: '',
    phoneNumber: '',
    dateRange: { from: '', to: '' },
    branchId: '',
    conversationType: 'all',
  })
  
  const [searchPerformed, setSearchPerformed] = useState(false)

  // Mock search function - will be replaced with real API call
  const performSearch = async (filters: SearchFilters, page: number = 1) => {
    setSearchState(prev => ({ ...prev, isLoading: true }))
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Mock search results
    const mockResults: Conversation[] = [
      {
        id: 'search1',
        customerId: 'cust1',
        restaurantId: 'rest1',
        status: 'resolved',
        type: 'feedback',
        aiConfidence: 0.9,
        messages: [
          {
            id: 'msg1',
            conversationId: 'search1',
            sender: 'customer',
            content: filters.query ? `هذا نص يحتوي على "${filters.query}" في المحتوى` : 'الطعام كان رائعاً جداً!',
            contentAr: filters.query ? `هذا نص يحتوي على "${filters.query}" في المحتوى` : 'الطعام كان رائعاً جداً!',
            timestamp: '2024-01-15T10:30:00Z',
            metadata: { sentiment: 'positive' },
          },
          {
            id: 'msg2',
            conversationId: 'search1',
            sender: 'ai',
            content: 'شكراً لك على تقييمك الإيجابي! نحن سعداء بإعجابك بالطعام.',
            timestamp: '2024-01-15T10:32:00Z',
            metadata: { confidence: 0.9, sentiment: 'positive' },
          },
        ],
        startedAt: '2024-01-15T10:30:00Z',
        resolvedAt: '2024-01-15T10:35:00Z',
        customer: {
          id: 'cust1',
          phoneNumber: '+966501234567',
          name: 'أحمد محمد',
          preferredLanguage: 'ar',
          totalOrders: 5,
          totalFeedback: 2,
          lastContactDate: '2024-01-15T10:30:00Z',
          tags: ['regular'],
          createdAt: '2023-12-01T00:00:00Z',
          updatedAt: '2024-01-15T10:35:00Z',
        },
      },
      {
        id: 'search2',
        customerId: 'cust2',
        restaurantId: 'rest1',
        status: 'resolved',
        type: 'support',
        aiConfidence: 0.75,
        messages: [
          {
            id: 'msg3',
            conversationId: 'search2',
            sender: 'customer',
            content: filters.query ? `سؤال حول الطلب يتضمن "${filters.query}"` : 'أين طلبي؟ تأخر كثيراً',
            timestamp: '2024-01-14T16:20:00Z',
            metadata: { sentiment: 'negative' },
          },
          {
            id: 'msg4',
            conversationId: 'search2',
            sender: 'agent',
            content: 'أعتذر عن التأخير، سأتحقق من حالة طلبك فوراً.',
            timestamp: '2024-01-14T16:25:00Z',
            metadata: { sentiment: 'neutral' },
          },
          {
            id: 'msg5',
            conversationId: 'search2',
            sender: 'agent',
            content: 'تم إرسال طلبك وسيصل خلال 10 دقائق.',
            timestamp: '2024-01-14T16:30:00Z',
            metadata: { sentiment: 'positive' },
          },
        ],
        startedAt: '2024-01-14T16:20:00Z',
        resolvedAt: '2024-01-14T16:45:00Z',
        customer: {
          id: 'cust2',
          phoneNumber: '+966507654321',
          name: 'سارة أحمد',
          preferredLanguage: 'ar',
          totalOrders: 12,
          totalFeedback: 4,
          lastContactDate: '2024-01-14T16:20:00Z',
          tags: ['vip'],
          createdAt: '2023-11-15T00:00:00Z',
          updatedAt: '2024-01-14T16:45:00Z',
        },
      },
    ]

    // Filter results based on search criteria
    let filteredResults = mockResults

    if (filters.query) {
      filteredResults = filteredResults.filter(conv =>
        conv.messages.some(msg => 
          msg.content.toLowerCase().includes(filters.query.toLowerCase()) ||
          (msg.contentAr && msg.contentAr.includes(filters.query))
        ) ||
        conv.customer?.name?.includes(filters.query) ||
        conv.customer?.phoneNumber?.includes(filters.query)
      )
    }

    if (filters.phoneNumber) {
      filteredResults = filteredResults.filter(conv =>
        conv.customer?.phoneNumber?.includes(filters.phoneNumber)
      )
    }

    if (filters.conversationType !== 'all') {
      filteredResults = filteredResults.filter(conv => conv.type === filters.conversationType)
    }

    // Simulate pagination
    const resultsPerPage = 10
    const totalResults = filteredResults.length
    const totalPages = Math.ceil(totalResults / resultsPerPage)
    const startIndex = (page - 1) * resultsPerPage
    const paginatedResults = filteredResults.slice(startIndex, startIndex + resultsPerPage)

    setSearchState({
      conversations: paginatedResults,
      isLoading: false,
      currentPage: page,
      totalPages,
      totalResults,
    })
  }

  const handleSearch = async (filters: SearchFilters) => {
    setCurrentFilters(filters)
    setSearchPerformed(true)
    await performSearch(filters, 1)
  }

  const handlePageChange = async (page: number) => {
    await performSearch(currentFilters, page)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isRTL ? 'البحث في المحادثات' : 'Search Conversations'}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isRTL 
            ? 'ابحث في تاريخ المحادثات والرسائل'
            : 'Search through conversation history and messages'
          }
        </p>
      </div>

      {/* Search Interface */}
      <SearchInterface onSearch={handleSearch} isLoading={searchState.isLoading} />

      {/* Search Results */}
      {searchPerformed && (
        <div className="space-y-4">
          {searchState.totalResults > 0 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {isRTL 
                  ? `${searchState.totalResults} نتيجة`
                  : `${searchState.totalResults} results`
                }
              </div>
            </div>
          )}

          <MessageHistory
            conversations={searchState.conversations}
            searchQuery={currentFilters.query}
            isLoading={searchState.isLoading}
            currentPage={searchState.currentPage}
            totalPages={searchState.totalPages}
            onPageChange={handlePageChange}
          />
        </div>
      )}

      {/* No search performed yet */}
      {!searchPerformed && (
        <div className="text-center py-12 text-muted-foreground">
          <p>{isRTL ? 'ابدأ البحث للعثور على المحادثات' : 'Start searching to find conversations'}</p>
        </div>
      )}
    </div>
  )
}