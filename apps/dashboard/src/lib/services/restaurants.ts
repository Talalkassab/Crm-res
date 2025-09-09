import { apiClient, withRetry } from '../api-client'
import type { Restaurant, Branch } from '@/types'

export interface RestaurantService {
  getRestaurant(id: string): Promise<Restaurant>
  updateRestaurant(id: string, data: Partial<Restaurant>): Promise<Restaurant>
  getBranches(restaurantId: string): Promise<Branch[]>
  updateRestaurantSettings(restaurantId: string, settings: any): Promise<any>
}

class RestaurantsAPI implements RestaurantService {
  async getRestaurant(id: string): Promise<Restaurant> {
    return withRetry(() => 
      apiClient.get<Restaurant>(`/restaurants/${id}`)
    )
  }

  async updateRestaurant(id: string, data: Partial<Restaurant>): Promise<Restaurant> {
    return withRetry(() => 
      apiClient.put<Restaurant>(`/restaurants/${id}`, data)
    )
  }

  async getBranches(restaurantId: string): Promise<Branch[]> {
    return withRetry(() => 
      apiClient.get<Branch[]>(`/restaurants/${restaurantId}/branches`)
    )
  }

  async updateRestaurantSettings(restaurantId: string, settings: any): Promise<any> {
    return withRetry(() => 
      apiClient.put(`/restaurants/${restaurantId}/settings`, settings)
    )
  }
}

export const restaurantsService = new RestaurantsAPI()