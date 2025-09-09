import type { Conversation, Feedback } from '@/types'

interface ExportOptions {
  format: 'csv' | 'excel' | 'pdf'
  includeDetails: boolean
  includeSentiment: boolean
  includeAIMetrics: boolean
  language: 'ar' | 'en'
}

export class ExportService {
  // CSV Export with UTF-8 encoding for Arabic text
  static exportToCSV(data: any[], headers: { [key: string]: string }, filename: string, language: 'ar' | 'en' = 'en') {
    // Convert data to CSV format
    const csvContent = this.convertToCSV(data, headers, language)
    
    // Create blob with UTF-8 BOM for proper Arabic encoding
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { 
      type: 'text/csv;charset=utf-8' 
    })
    
    // Trigger download
    this.downloadBlob(blob, filename)
  }

  // Convert feedback data to CSV
  static exportFeedbackData(
    feedback: Feedback[], 
    conversations: Conversation[], 
    options: ExportOptions
  ) {
    const headers = options.language === 'ar' ? {
      id: 'المعرف',
      customerName: 'اسم العميل',
      customerPhone: 'رقم الهاتف',
      rating: 'التقييم',
      comment: 'التعليق',
      sentiment: 'المشاعر',
      categories: 'الفئات',
      branchName: 'الفرع',
      createdAt: 'تاريخ الإنشاء',
      requiresFollowup: 'يحتاج متابعة'
    } : {
      id: 'ID',
      customerName: 'Customer Name',
      customerPhone: 'Phone Number', 
      rating: 'Rating',
      comment: 'Comment',
      sentiment: 'Sentiment',
      categories: 'Categories',
      branchName: 'Branch',
      createdAt: 'Created At',
      requiresFollowup: 'Requires Followup'
    }

    const exportData = feedback.map(f => {
      const conversation = conversations.find(c => c.id === f.conversationId)
      return {
        id: f.id,
        customerName: conversation?.customer?.name || 'N/A',
        customerPhone: conversation?.customer?.phoneNumber || 'N/A',
        rating: f.rating,
        comment: f.comment || '',
        sentiment: options.includeSentiment ? f.sentiment : '',
        categories: f.categories.join(', '),
        branchName: conversation?.branch?.name || 'N/A',
        createdAt: new Date(f.createdAt).toLocaleDateString(options.language === 'ar' ? 'ar-SA' : 'en-US'),
        requiresFollowup: f.requiresFollowup ? (options.language === 'ar' ? 'نعم' : 'Yes') : (options.language === 'ar' ? 'لا' : 'No')
      }
    })

    const filename = `feedback_export_${new Date().toISOString().split('T')[0]}.csv`
    this.exportToCSV(exportData, headers, filename, options.language)
  }

  // Convert conversation data to CSV
  static exportConversationData(
    conversations: Conversation[],
    options: ExportOptions
  ) {
    const headers = options.language === 'ar' ? {
      id: 'معرف المحادثة',
      customerName: 'اسم العميل',
      customerPhone: 'رقم الهاتف',
      status: 'الحالة',
      type: 'النوع',
      messageCount: 'عدد الرسائل',
      aiConfidence: 'ثقة الذكاء الاصطناعي',
      startedAt: 'بدأت في',
      resolvedAt: 'انتهت في',
      branchName: 'الفرع',
      duration: 'المدة (دقائق)'
    } : {
      id: 'Conversation ID',
      customerName: 'Customer Name',
      customerPhone: 'Phone Number',
      status: 'Status',
      type: 'Type',
      messageCount: 'Message Count',
      aiConfidence: 'AI Confidence',
      startedAt: 'Started At',
      resolvedAt: 'Resolved At',
      branchName: 'Branch',
      duration: 'Duration (minutes)'
    }

    const exportData = conversations.map(c => {
      const startTime = new Date(c.startedAt)
      const endTime = c.resolvedAt ? new Date(c.resolvedAt) : new Date()
      const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60))

      return {
        id: c.id,
        customerName: c.customer?.name || 'Unknown',
        customerPhone: c.customer?.phoneNumber || 'Unknown',
        status: c.status,
        type: c.type,
        messageCount: c.messages.length,
        aiConfidence: options.includeAIMetrics ? `${Math.round(c.aiConfidence * 100)}%` : '',
        startedAt: startTime.toLocaleString(options.language === 'ar' ? 'ar-SA' : 'en-US'),
        resolvedAt: c.resolvedAt ? new Date(c.resolvedAt).toLocaleString(options.language === 'ar' ? 'ar-SA' : 'en-US') : '',
        branchName: c.branch?.name || 'N/A',
        duration: duration
      }
    })

    const filename = `conversations_export_${new Date().toISOString().split('T')[0]}.csv`
    this.exportToCSV(exportData, headers, filename, options.language)
  }

  // Convert detailed conversation data with messages
  static exportDetailedConversationData(
    conversations: Conversation[],
    options: ExportOptions
  ) {
    const headers = options.language === 'ar' ? {
      conversationId: 'معرف المحادثة',
      customerName: 'اسم العميل',
      messageId: 'معرف الرسالة',
      sender: 'المرسل',
      content: 'المحتوى',
      sentiment: 'المشاعر',
      aiConfidence: 'ثقة الذكاء الاصطناعي',
      timestamp: 'وقت الإرسال',
      branchName: 'الفرع'
    } : {
      conversationId: 'Conversation ID',
      customerName: 'Customer Name',
      messageId: 'Message ID',
      sender: 'Sender',
      content: 'Content',
      sentiment: 'Sentiment',
      aiConfidence: 'AI Confidence',
      timestamp: 'Timestamp',
      branchName: 'Branch'
    }

    const exportData: any[] = []

    conversations.forEach(c => {
      c.messages.forEach(m => {
        exportData.push({
          conversationId: c.id,
          customerName: c.customer?.name || 'Unknown',
          messageId: m.id,
          sender: m.sender,
          content: options.language === 'ar' && m.contentAr ? m.contentAr : m.content,
          sentiment: options.includeSentiment ? (m.metadata?.sentiment || '') : '',
          aiConfidence: options.includeAIMetrics ? (m.metadata?.confidence ? `${Math.round(m.metadata.confidence * 100)}%` : '') : '',
          timestamp: new Date(m.timestamp).toLocaleString(options.language === 'ar' ? 'ar-SA' : 'en-US'),
          branchName: c.branch?.name || 'N/A'
        })
      })
    })

    const filename = `detailed_conversations_export_${new Date().toISOString().split('T')[0]}.csv`
    this.exportToCSV(exportData, headers, filename, options.language)
  }

  // Analytics data export
  static exportAnalyticsData(
    analyticsData: any,
    options: ExportOptions
  ) {
    const headers = options.language === 'ar' ? {
      metric: 'المقياس',
      value: 'القيمة',
      period: 'الفترة',
      trend: 'الاتجاه',
      date: 'التاريخ'
    } : {
      metric: 'Metric',
      value: 'Value',
      period: 'Period',
      trend: 'Trend',
      date: 'Date'
    }

    // Mock analytics data structure
    const exportData = [
      {
        metric: options.language === 'ar' ? 'إجمالي المحادثات' : 'Total Conversations',
        value: analyticsData.totalConversations || 1247,
        period: options.language === 'ar' ? 'شهري' : 'Monthly',
        trend: '+12.3%',
        date: new Date().toLocaleDateString(options.language === 'ar' ? 'ar-SA' : 'en-US')
      },
      {
        metric: options.language === 'ar' ? 'متوسط التقييم' : 'Average Rating',
        value: analyticsData.averageRating || '4.2/5',
        period: options.language === 'ar' ? 'شهري' : 'Monthly',
        trend: '+0.3',
        date: new Date().toLocaleDateString(options.language === 'ar' ? 'ar-SA' : 'en-US')
      },
      {
        metric: options.language === 'ar' ? 'معدل الاستجابة' : 'Response Rate',
        value: `${analyticsData.responseRate || 94.5}%`,
        period: options.language === 'ar' ? 'أسبوعي' : 'Weekly',
        trend: '+2.1%',
        date: new Date().toLocaleDateString(options.language === 'ar' ? 'ar-SA' : 'en-US')
      }
    ]

    if (options.includeAIMetrics) {
      exportData.push({
        metric: options.language === 'ar' ? 'معدل الأتمتة' : 'Automation Rate',
        value: `${analyticsData.automationRate || 87.2}%`,
        period: options.language === 'ar' ? 'شهري' : 'Monthly',
        trend: '+5.7%',
        date: new Date().toLocaleDateString(options.language === 'ar' ? 'ar-SA' : 'en-US')
      })
    }

    const filename = `analytics_export_${new Date().toISOString().split('T')[0]}.csv`
    this.exportToCSV(exportData, headers, filename, options.language)
  }

  // Helper method to convert array to CSV string
  private static convertToCSV(data: any[], headers: { [key: string]: string }, language: 'ar' | 'en'): string {
    const headerKeys = Object.keys(headers)
    const headerValues = Object.values(headers)
    
    // Create header row
    const csvRows = [headerValues.join(',')]
    
    // Create data rows
    data.forEach(row => {
      const values = headerKeys.map(key => {
        let value = row[key] || ''
        
        // Handle special characters and quotes in CSV
        if (typeof value === 'string') {
          // Escape quotes and wrap in quotes if contains comma, quote, or newline
          if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            value = `"${value.replace(/"/g, '""')}"`
          }
        }
        
        return value
      })
      csvRows.push(values.join(','))
    })
    
    return csvRows.join('\n')
  }

  // Helper method to trigger file download
  private static downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}