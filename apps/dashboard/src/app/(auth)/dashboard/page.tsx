'use client'

import { useEffect } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import {
  Users,
  MessageSquare,
  TrendingUp,
  AlertCircle,
  Activity,
  Clock,
  BarChart,
  Zap,
} from 'lucide-react'

export default function DashboardPage() {
  const { ui, metrics } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock data for now - will be replaced with real API calls
  const mockMetrics = {
    conversationsToday: 142,
    conversationsTrend: 12,
    averageRating: 4.3,
    ratingTrend: 0.2,
    responseRate: 92,
    responseTrend: 3,
    automationRate: 78,
    automationTrend: 5,
    activeConversations: 8,
    escalatedConversations: 2,
    negativeFeedbackCount: 3,
    lastUpdated: new Date().toISOString(),
  }

  const metricCards = [
    {
      title: { en: 'Conversations Today', ar: 'المحادثات اليوم' },
      value: mockMetrics.conversationsToday,
      trend: mockMetrics.conversationsTrend,
      icon: MessageSquare,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: { en: 'Average Rating', ar: 'متوسط التقييم' },
      value: `${mockMetrics.averageRating}/5`,
      trend: mockMetrics.ratingTrend,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: { en: 'Response Rate', ar: 'معدل الاستجابة' },
      value: `${mockMetrics.responseRate}%`,
      trend: mockMetrics.responseTrend,
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: { en: 'Automation Rate', ar: 'معدل الأتمتة' },
      value: `${mockMetrics.automationRate}%`,
      trend: mockMetrics.automationTrend,
      icon: Zap,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ]

  const statusCards = [
    {
      title: { en: 'Active Conversations', ar: 'المحادثات النشطة' },
      value: mockMetrics.activeConversations,
      icon: Users,
      color: 'text-blue-600',
    },
    {
      title: { en: 'Escalated', ar: 'تم التصعيد' },
      value: mockMetrics.escalatedConversations,
      icon: AlertCircle,
      color: 'text-yellow-600',
    },
    {
      title: { en: 'Negative Feedback', ar: 'ردود فعل سلبية' },
      value: mockMetrics.negativeFeedbackCount,
      icon: AlertCircle,
      color: 'text-red-600',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isRTL ? 'لوحة التحكم' : 'Dashboard'}
        </h1>
        <p className="text-muted-foreground">
          {isRTL
            ? 'نظرة عامة على أداء نظام خدمة العملاء'
            : 'Overview of your customer service system performance'}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((card, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
              {card.trend !== 0 && (
                <span
                  className={cn(
                    'text-xs font-medium',
                    card.trend > 0 ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  {card.trend > 0 ? '+' : ''}{card.trend}%
                </span>
              )}
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-medium text-muted-foreground">
                {card.title[ui.language]}
              </h3>
              <p className="text-2xl font-bold mt-1">{card.value}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {statusCards.map((card, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {card.title[ui.language]}
                </p>
                <p className="text-3xl font-bold mt-2">{card.value}</p>
              </div>
              <card.icon className={`h-8 w-8 ${card.color}`} />
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">
          {isRTL ? 'النشاط الأخير' : 'Recent Activity'}
        </h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-full bg-blue-50">
              <MessageSquare className="h-4 w-4 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">
                {isRTL ? 'محادثة جديدة بدأت' : 'New conversation started'}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRTL ? 'قبل دقيقتين' : '2 minutes ago'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-full bg-yellow-50">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">
                {isRTL ? 'تم تصعيد المحادثة' : 'Conversation escalated'}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRTL ? 'قبل 5 دقائق' : '5 minutes ago'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-full bg-green-50">
              <Activity className="h-4 w-4 text-green-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">
                {isRTL ? 'تم استلام ملاحظات إيجابية' : 'Positive feedback received'}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRTL ? 'قبل 10 دقائق' : '10 minutes ago'}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}