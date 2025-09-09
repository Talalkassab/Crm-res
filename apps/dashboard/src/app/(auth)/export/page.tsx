'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { ReportGenerator } from '@/components/export/report-generator'
import { ExportService } from '@/lib/export-service'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Download, FileText, Database, BarChart3, Zap } from 'lucide-react'

export default function ExportPage() {
  const { ui, conversations } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock data for quick export examples
  const handleQuickExport = (type: 'feedback' | 'conversations' | 'analytics') => {
    const options = {
      format: 'csv' as const,
      includeDetails: true,
      includeSentiment: true,
      includeAIMetrics: true,
      language: ui.language,
    }

    switch (type) {
      case 'feedback':
        // Mock feedback data
        const mockFeedback = [
          {
            id: 'fb1',
            conversationId: 'conv1',
            customerId: 'cust1',
            restaurantId: 'rest1',
            branchId: 'branch1',
            rating: 5 as const,
            comment: 'الطعام كان ممتازاً والخدمة رائعة!',
            sentiment: 'positive' as const,
            categories: ['food', 'service'],
            requiresFollowup: false,
            createdAt: '2024-01-15T10:30:00Z',
          },
          {
            id: 'fb2',
            conversationId: 'conv2',
            customerId: 'cust2',
            restaurantId: 'rest1',
            branchId: 'branch1',
            rating: 2 as const,
            comment: 'الطلب تأخر كثيراً والطعام وصل بارداً',
            sentiment: 'negative' as const,
            categories: ['delivery', 'food_quality'],
            requiresFollowup: true,
            createdAt: '2024-01-14T18:20:00Z',
          },
        ]
        ExportService.exportFeedbackData(mockFeedback, conversations.items, options)
        break

      case 'conversations':
        ExportService.exportConversationData(conversations.items, options)
        break

      case 'analytics':
        const mockAnalytics = {
          totalConversations: 1247,
          averageRating: 4.2,
          responseRate: 94.5,
          automationRate: 87.2,
        }
        ExportService.exportAnalyticsData(mockAnalytics, options)
        break
    }
  }

  const quickExportOptions = [
    {
      id: 'feedback',
      title: isRTL ? 'تصدير الملاحظات' : 'Export Feedback',
      description: isRTL ? 'تصدير ملاحظات العملاء الأخيرة' : 'Export recent customer feedback',
      icon: FileText,
      color: 'text-blue-600 bg-blue-50',
      count: 245
    },
    {
      id: 'conversations',
      title: isRTL ? 'تصدير المحادثات' : 'Export Conversations',
      description: isRTL ? 'تصدير سجل المحادثات' : 'Export conversation history',
      icon: Database,
      color: 'text-green-600 bg-green-50',
      count: conversations.items.length
    },
    {
      id: 'analytics',
      title: isRTL ? 'تصدير التحليلات' : 'Export Analytics',
      description: isRTL ? 'تصدير البيانات التحليلية' : 'Export analytics data',
      icon: BarChart3,
      color: 'text-purple-600 bg-purple-50',
      count: 12
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isRTL ? 'تصدير البيانات' : 'Data Export'}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isRTL 
            ? 'تصدير ملاحظات العملاء والتحليلات بصيغ مختلفة'
            : 'Export customer feedback and analytics in various formats'
          }
        </p>
      </div>

      {/* Quick Export Options */}
      <div className="grid gap-4 md:grid-cols-3">
        {quickExportOptions.map((option) => (
          <Card key={option.id} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg ${option.color}`}>
                  <option.icon className="h-5 w-5" />
                </div>
                <Badge variant="secondary">{option.count}</Badge>
              </div>
              
              <h3 className="font-semibold mb-2">{option.title}</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {option.description}
              </p>
              
              <Button 
                onClick={() => handleQuickExport(option.id as any)}
                size="sm" 
                variant="outline" 
                className="w-full"
              >
                <Download className="h-4 w-4 mr-2" />
                {isRTL ? 'تصدير سريع' : 'Quick Export'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Advanced Export Generator */}
      <ReportGenerator />

      {/* Export Guidelines */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {isRTL ? 'إرشادات التصدير' : 'Export Guidelines'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-semibold mb-2">
                {isRTL ? 'تشفير النصوص العربية' : 'Arabic Text Encoding'}
              </h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• {isRTL ? 'جميع الملفات يتم تصديرها بترميز UTF-8' : 'All files exported with UTF-8 encoding'}</li>
                <li>• {isRTL ? 'النصوص العربية تظهر بشكل صحيح في Excel' : 'Arabic text displays correctly in Excel'}</li>
                <li>• {isRTL ? 'دعم كامل للنصوص ثنائية الاتجاه' : 'Full bidirectional text support'}</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">
                {isRTL ? 'أنواع البيانات المتاحة' : 'Available Data Types'}
              </h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• {isRTL ? 'ملاحظات العملاء وتقييماتهم' : 'Customer feedback and ratings'}</li>
                <li>• {isRTL ? 'سجل المحادثات الكامل' : 'Complete conversation history'}</li>
                <li>• {isRTL ? 'تحليل المشاعر والاتجاهات' : 'Sentiment analysis and trends'}</li>
                <li>• {isRTL ? 'مقاييس الأداء والذكاء الاصطناعي' : 'Performance and AI metrics'}</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}