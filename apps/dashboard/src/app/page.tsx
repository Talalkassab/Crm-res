import { Suspense } from 'react'
import { DashboardHeader } from '@/components/dashboard-header'
import { StatsCards } from '@/components/stats-cards'
import { ConversationList } from '@/components/conversation-list'
import { RecentActivity } from '@/components/recent-activity'
import { PrayerTimeWidget } from '@/components/prayer-time-widget'

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <DashboardHeader />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">نظرة عامة</h2>
          <StatsCards />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Conversations */}
          <div className="lg:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">المحادثات النشطة</h3>
            <Suspense fallback={<div className="animate-pulse bg-gray-200 h-64 rounded-lg" />}>
              <ConversationList />
            </Suspense>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Prayer Times */}
            <PrayerTimeWidget />
            
            {/* Recent Activity */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">النشاط الأخير</h3>
              <Suspense fallback={<div className="animate-pulse bg-gray-200 h-48 rounded-lg" />}>
                <RecentActivity />
              </Suspense>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}