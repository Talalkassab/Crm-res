import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DashboardPage from '@/app/(auth)/dashboard/page'

// Mock the app store
vi.mock('@/stores/app-store', () => ({
  useAppStore: () => ({
    ui: { language: 'en' },
    metrics: { dashboard: null, lastUpdated: null }
  })
}))

describe('Dashboard Page', () => {
  it('renders dashboard title', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('displays metrics cards', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Conversations Today')).toBeInTheDocument()
    expect(screen.getByText('Average Rating')).toBeInTheDocument()
  })
})