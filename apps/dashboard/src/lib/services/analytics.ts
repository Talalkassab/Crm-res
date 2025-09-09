import { apiClient, withRetry } from '../api-client'
import type { DashboardMetrics, Feedback } from '@/types'

export interface AnalyticsService {
  getDashboardMetrics(restaurantId: string, dateRange?: { from: string; to: string }): Promise<DashboardMetrics>
  getFeedbackAnalytics(restaurantId: string, filters?: any): Promise<any>
  getAIMetrics(restaurantId: string, dateRange?: { from: string; to: string }): Promise<any>
  exportData(type: string, format: string, filters?: any): Promise<{ downloadUrl: string }>
}

class AnalyticsAPI implements AnalyticsService {
  async getDashboardMetrics(restaurantId: string, dateRange?: { from: string; to: string }): Promise<DashboardMetrics> {
    const queryParams = new URLSearchParams()
    queryParams.append('restaurant_id', restaurantId)
    
    if (dateRange?.from) queryParams.append('date_from', dateRange.from)
    if (dateRange?.to) queryParams.append('date_to', dateRange.to)

    return withRetry(() => 
      apiClient.get<DashboardMetrics>(`/analytics/dashboard?${queryParams.toString()}`)
    )
  }

  async getFeedbackAnalytics(restaurantId: string, filters?: any): Promise<any> {
    const queryParams = new URLSearchParams()
    queryParams.append('restaurant_id', restaurantId)
    
    // Add filter parameters
    Object.entries(filters || {}).forEach(([key, value]) => {
      if (value) queryParams.append(key, String(value))
    })

    return withRetry(() => 
      apiClient.get(`/analytics/feedback?${queryParams.toString()}`)
    )
  }

  async getAIMetrics(restaurantId: string, dateRange?: { from: string; to: string }): Promise<any> {
    const queryParams = new URLSearchParams()
    queryParams.append('restaurant_id', restaurantId)
    
    if (dateRange?.from) queryParams.append('date_from', dateRange.from)
    if (dateRange?.to) queryParams.append('date_to', dateRange.to)

    return withRetry(() => 
      apiClient.get(`/analytics/ai-metrics?${queryParams.toString()}`)
    )
  }

  async exportData(type: string, format: string, filters?: any): Promise<{ downloadUrl: string }> {
    return withRetry(() => 
      apiClient.post<{ downloadUrl: string }>('/export', {
        type,
        format,
        filters,
        timestamp: new Date().toISOString(),
      })
    )
  }
}

export const analyticsService = new AnalyticsAPI()