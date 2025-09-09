'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { MetricsGrid } from '@/components/analytics/metrics-grid'
import { SatisfactionChart } from '@/components/analytics/satisfaction-chart'
import { SentimentAnalysis } from '@/components/analytics/sentiment-analysis'
import { ResponseMetrics } from '@/components/analytics/response-metrics'
import { AIMetrics } from '@/components/analytics/ai-metrics'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Calendar, Download, RefreshCw, BarChart3, TrendingUp, Bot } from 'lucide-react'

export default function AnalyticsPage() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  const [activeTab, setActiveTab] = useState<'overview' | 'satisfaction' | 'sentiment' | 'response' | 'ai'>('overview')
  const [dateRange, setDateRange] = useState('7d')

  const tabs = [
    { id: 'overview', label: isRTL ? 'نظرة عامة' : 'Overview', icon: BarChart3 },
    { id: 'satisfaction', label: isRTL ? 'الرضا' : 'Satisfaction', icon: TrendingUp },
    { id: 'sentiment', label: isRTL ? 'المشاعر' : 'Sentiment', icon: TrendingUp },
    { id: 'response', label: isRTL ? 'الاستجابة' : 'Response', icon: TrendingUp },
    { id: 'ai', label: isRTL ? 'الذكاء الاصطناعي' : 'AI Performance', icon: Bot },
  ]

  const dateRanges = [
    { value: '24h', label: isRTL ? '24 ساعة' : '24h' },
    { value: '7d', label: isRTL ? '7 أيام' : '7d' },
    { value: '30d', label: isRTL ? '30 يوم' : '30d' },
    { value: '90d', label: isRTL ? '90 يوم' : '90d' },
  ]

  const handleExport = () => {
    // Mock export functionality
    console.log('Exporting analytics data...')
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <MetricsGrid />
      case 'satisfaction':
        return <SatisfactionChart />
      case 'sentiment':
        return <SentimentAnalysis />
      case 'response':
        return <ResponseMetrics />
      case 'ai':
        return <AIMetrics />
      default:
        return <MetricsGrid />
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {isRTL ? 'التحليلات' : 'Analytics'}
          </h1>
          <p className="text-muted-foreground mt-1">
            {isRTL ? 'تحليلات الأداء ورضا العملاء' : 'Performance analytics and customer satisfaction'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Date Range Selector */}
          <div className="flex items-center gap-1">
            {dateRanges.map((range) => (
              <Button
                key={range.value}
                variant={dateRange === range.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDateRange(range.value)}
              >
                {range.label}
              </Button>
            ))}
          </div>

          {/* Action Buttons */}
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            {isRTL ? 'تحديث' : 'Refresh'}
          </Button>

          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            {isRTL ? 'تصدير' : 'Export'}
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b">
        <nav className="flex gap-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div>
        {renderContent()}
      </div>

      {/* Auto-refresh indicator */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium">
              {isRTL ? 'التحديث التلقائي مفعل' : 'Auto-refresh enabled'}
            </span>
          </div>
          <Badge variant="secondary">
            {isRTL ? 'كل 30 ثانية' : 'Every 30s'}
          </Badge>
        </div>
      </Card>
    </div>
  )
}