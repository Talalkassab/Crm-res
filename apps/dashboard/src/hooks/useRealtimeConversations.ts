import { useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { useAppStore } from '@/stores/app-store'
import type { Conversation, Message } from '@/types'

export function useRealtimeConversations(restaurantId: string | null) {
  const {
    addConversation,
    updateConversation,
    setConversations,
    setConversationsLoading,
  } = useAppStore()
  
  const supabase = createClient()

  const fetchConversations = useCallback(async () => {
    if (!restaurantId) return

    setConversationsLoading(true)
    try {
      // Mock data for now - will be replaced with real API call
      const mockConversations: Conversation[] = [
        {
          id: '1',
          customerId: 'cust1',
          restaurantId,
          status: 'active',
          type: 'feedback',
          aiConfidence: 0.85,
          messages: [
            {
              id: 'm1',
              conversationId: '1',
              sender: 'customer',
              content: 'الطعام كان ممتازًا اليوم!',
              contentAr: 'الطعام كان ممتازًا اليوم!',
              timestamp: new Date().toISOString(),
              metadata: {
                sentiment: 'positive',
              },
            },
            {
              id: 'm2',
              conversationId: '1',
              sender: 'ai',
              content: 'شكراً لك على ملاحظاتك الإيجابية! نحن سعداء بأن الطعام نال إعجابك.',
              timestamp: new Date().toISOString(),
              metadata: {
                confidence: 0.85,
                sentiment: 'positive',
              },
            },
          ],
          startedAt: new Date().toISOString(),
          customer: {
            id: 'cust1',
            phoneNumber: '+966501234567',
            name: 'أحمد محمد',
            preferredLanguage: 'ar',
            totalOrders: 15,
            totalFeedback: 8,
            lastContactDate: new Date().toISOString(),
            tags: ['vip', 'regular'],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        },
        {
          id: '2',
          customerId: 'cust2',
          restaurantId,
          status: 'escalated',
          type: 'support',
          aiConfidence: 0.3,
          messages: [
            {
              id: 'm3',
              conversationId: '2',
              sender: 'customer',
              content: 'طلبي لم يصل بعد وقد مر أكثر من ساعة!',
              timestamp: new Date().toISOString(),
              metadata: {
                sentiment: 'negative',
              },
            },
            {
              id: 'm4',
              conversationId: '2',
              sender: 'ai',
              content: 'أعتذر عن التأخير. سأقوم بتحويلك إلى أحد موظفينا للمساعدة الفورية.',
              timestamp: new Date().toISOString(),
              metadata: {
                confidence: 0.3,
                sentiment: 'negative',
              },
            },
          ],
          startedAt: new Date(Date.now() - 3600000).toISOString(),
          escalatedAt: new Date(Date.now() - 1800000).toISOString(),
          customer: {
            id: 'cust2',
            phoneNumber: '+966507654321',
            preferredLanguage: 'ar',
            totalOrders: 5,
            totalFeedback: 2,
            lastContactDate: new Date().toISOString(),
            tags: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        },
      ]

      setConversations(mockConversations)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setConversationsLoading(false)
    }
  }, [restaurantId, setConversations, setConversationsLoading])

  useEffect(() => {
    if (!restaurantId) return

    // Initial fetch
    fetchConversations()

    // Set up realtime subscription
    const channel = supabase
      .channel(`restaurant_${restaurantId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'conversations',
          filter: `restaurant_id=eq.${restaurantId}`,
        },
        (payload) => {
          console.log('New conversation:', payload)
          // addConversation(payload.new as Conversation)
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'conversations',
          filter: `restaurant_id=eq.${restaurantId}`,
        },
        (payload) => {
          console.log('Updated conversation:', payload)
          // updateConversation(payload.new.id, payload.new as Partial<Conversation>)
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
        },
        (payload) => {
          console.log('New message:', payload)
          // Handle new message
        }
      )
      .subscribe((status) => {
        console.log('Realtime subscription status:', status)
      })

    // Cleanup
    return () => {
      supabase.removeChannel(channel)
    }
  }, [restaurantId, supabase, addConversation, updateConversation, fetchConversations])

  return {
    refetch: fetchConversations,
  }
}