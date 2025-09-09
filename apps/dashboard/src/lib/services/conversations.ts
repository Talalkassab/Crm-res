import { apiClient, withRetry } from '../api-client'
import type { Conversation, Message, ConversationFilters } from '@/types'

export interface ConversationService {
  getConversations(restaurantId: string, filters?: ConversationFilters): Promise<Conversation[]>
  getConversation(id: string): Promise<Conversation>
  sendMessage(conversationId: string, message: string): Promise<Message>
  updateConversationStatus(id: string, status: Conversation['status']): Promise<Conversation>
}

class ConversationsAPI implements ConversationService {
  async getConversations(restaurantId: string, filters?: ConversationFilters): Promise<Conversation[]> {
    const queryParams = new URLSearchParams()
    queryParams.append('restaurant_id', restaurantId)
    
    if (filters?.status) queryParams.append('status', filters.status)
    if (filters?.type) queryParams.append('type', filters.type)
    if (filters?.branchId) queryParams.append('branch_id', filters.branchId)
    if (filters?.dateRange?.from) queryParams.append('date_from', filters.dateRange.from)
    if (filters?.dateRange?.to) queryParams.append('date_to', filters.dateRange.to)
    if (filters?.searchQuery) queryParams.append('search', filters.searchQuery)

    return withRetry(() => 
      apiClient.get<Conversation[]>(`/conversations?${queryParams.toString()}`)
    )
  }

  async getConversation(id: string): Promise<Conversation> {
    return withRetry(() => 
      apiClient.get<Conversation>(`/conversations/${id}`)
    )
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    return withRetry(() => 
      apiClient.post<Message>(`/conversations/${conversationId}/messages`, {
        content,
        sender: 'agent',
        timestamp: new Date().toISOString(),
      })
    )
  }

  async updateConversationStatus(id: string, status: Conversation['status']): Promise<Conversation> {
    return withRetry(() => 
      apiClient.put<Conversation>(`/conversations/${id}`, { status })
    )
  }
}

export const conversationsService = new ConversationsAPI()