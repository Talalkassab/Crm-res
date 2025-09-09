'use client'

import { useAppStore } from '@/stores/app-store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  TrendingUp,
  TrendingDown,
  MessageSquare,
  Star,
  Clock,
  Zap,
  Users,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon: React.ElementType
  color: string
}

function MetricCard({ title, value, change, changeLabel, icon: Icon, color }: MetricCardProps) {
  const hasPositiveChange = change !== undefined && change > 0
  const hasNegativeChange = change !== undefined && change < 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={cn('h-4 w-4', color)} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <div className="flex items-center text-xs text-muted-foreground mt-1">
            {hasPositiveChange && <TrendingUp className="h-3 w-3 mr-1 text-green-500" />}
            {hasNegativeChange && <TrendingDown className="h-3 w-3 mr-1 text-red-500" />}
            <span className={cn(
              hasPositiveChange && 'text-green-500',
              hasNegativeChange && 'text-red-500'
            )}>
              {hasPositiveChange ? '+' : ''}{change}%
            </span>
            {changeLabel && <span className="ml-1">{changeLabel}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function MetricsGrid() {
  const { ui, metrics } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock data for now
  const metricsData = {
    totalConversations: 1247,
    conversationsChange: 12.3,
    averageRating: 4.2,
    ratingChange: 0.3,
    responseRate: 94.5,
    responseChange: 2.1,
    automationRate: 87.2,
    automationChange: 5.7,
    averageResponseTime: '2.4m',
    responseTimeChange: -15.2,
    resolutionRate: 91.8,
    resolutionChange: 3.4,
    escalationRate: 5.2,
    escalationChange: -8.1,
    customerSatisfaction: 4.6,
    satisfactionChange: 0.2,
  }

  const metrics_cards = [
    {
      title: isRTL ? 'إجمالي المحادثات' : 'Total Conversations',
      value: metricsData.totalConversations.toLocaleString(),
      change: metricsData.conversationsChange,
      changeLabel: isRTL ? 'من الأسبوع الماضي' : 'from last week',
      icon: MessageSquare,
      color: 'text-blue-600',
    },
    {
      title: isRTL ? 'متوسط التقييم' : 'Average Rating',
      value: `${metricsData.averageRating}/5`,
      change: metricsData.ratingChange,
      changeLabel: isRTL ? 'من الشهر الماضي' : 'from last month',
      icon: Star,
      color: 'text-yellow-600',
    },
    {
      title: isRTL ? 'معدل الاستجابة' : 'Response Rate',
      value: `${metricsData.responseRate}%`,
      change: metricsData.responseChange,
      changeLabel: isRTL ? 'من الأسبوع الماضي' : 'from last week',
      icon: Clock,
      color: 'text-green-600',
    },
    {
      title: isRTL ? 'معدل الأتمتة' : 'Automation Rate',
      value: `${metricsData.automationRate}%`,
      change: metricsData.automationChange,
      changeLabel: isRTL ? 'من الشهر الماضي' : 'from last month',
      icon: Zap,
      color: 'text-purple-600',
    },
    {
      title: isRTL ? 'متوسط وقت الاستجابة' : 'Avg Response Time',
      value: metricsData.averageResponseTime,
      change: metricsData.responseTimeChange,
      changeLabel: isRTL ? 'من الأسبوع الماضي' : 'from last week',
      icon: Clock,
      color: 'text-orange-600',
    },
    {
      title: isRTL ? 'معدل الحل' : 'Resolution Rate',
      value: `${metricsData.resolutionRate}%`,
      change: metricsData.resolutionChange,
      changeLabel: isRTL ? 'من الشهر الماضي' : 'from last month',
      icon: CheckCircle2,
      color: 'text-green-600',
    },
    {
      title: isRTL ? 'معدل التصعيد' : 'Escalation Rate',
      value: `${metricsData.escalationRate}%`,
      change: metricsData.escalationChange,
      changeLabel: isRTL ? 'من الأسبوع الماضي' : 'from last week',
      icon: AlertTriangle,
      color: 'text-red-600',
    },
    {
      title: isRTL ? 'رضا العملاء' : 'Customer Satisfaction',
      value: `${metricsData.customerSatisfaction}/5`,
      change: metricsData.satisfactionChange,
      changeLabel: isRTL ? 'من الشهر الماضي' : 'from last month',
      icon: Users,
      color: 'text-indigo-600',
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {metrics_cards.map((metric, index) => (
        <MetricCard
          key={index}
          title={metric.title}
          value={metric.value}
          change={metric.change}
          changeLabel={metric.changeLabel}
          icon={metric.icon}
          color={metric.color}
        />
      ))}
    </div>
  )
}