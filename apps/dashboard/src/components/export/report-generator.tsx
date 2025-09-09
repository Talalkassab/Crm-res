'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Download, Calendar, FileText, Database, Settings, CheckCircle, AlertCircle } from 'lucide-react'

interface ExportConfig {
  type: 'feedback' | 'conversations' | 'analytics' | 'all'
  format: 'csv' | 'excel' | 'pdf'
  dateRange: {
    from: string
    to: string
  }
  includeDetails: boolean
  includeSentiment: boolean
  includeAIMetrics: boolean
}

interface ExportJob {
  id: string
  type: ExportConfig['type']
  format: ExportConfig['format']
  status: 'pending' | 'processing' | 'completed' | 'error'
  createdAt: string
  downloadUrl?: string
  error?: string
}

export function ReportGenerator() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  
  const [config, setConfig] = useState<ExportConfig>({
    type: 'feedback',
    format: 'csv',
    dateRange: {
      from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      to: new Date().toISOString().split('T')[0],
    },
    includeDetails: true,
    includeSentiment: true,
    includeAIMetrics: false,
  })
  
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([
    {
      id: 'job1',
      type: 'feedback',
      format: 'csv',
      status: 'completed',
      createdAt: '2024-01-15T10:30:00Z',
      downloadUrl: '/exports/feedback_2024-01-15.csv',
    },
    {
      id: 'job2',
      type: 'conversations',
      format: 'excel',
      status: 'processing',
      createdAt: '2024-01-15T11:00:00Z',
    },
  ])
  
  const [isGenerating, setIsGenerating] = useState(false)

  const exportTypes = [
    { 
      value: 'feedback', 
      label: isRTL ? 'ملاحظات العملاء' : 'Customer Feedback',
      icon: FileText,
      description: isRTL ? 'تصدير جميع ملاحظات العملاء وتقييماتهم' : 'Export all customer feedback and ratings'
    },
    { 
      value: 'conversations', 
      label: isRTL ? 'المحادثات' : 'Conversations',
      icon: Database,
      description: isRTL ? 'تصدير سجل المحادثات مع العملاء' : 'Export conversation history with customers'
    },
    { 
      value: 'analytics', 
      label: isRTL ? 'التحليلات' : 'Analytics',
      icon: Settings,
      description: isRTL ? 'تصدير البيانات التحليلية والإحصائيات' : 'Export analytics data and statistics'
    },
  ]

  const formatOptions = [
    { value: 'csv', label: 'CSV', icon: FileText },
    { value: 'excel', label: 'Excel', icon: FileText },
    { value: 'pdf', label: 'PDF', icon: FileText },
  ]

  const handleGenerate = async () => {
    setIsGenerating(true)
    
    // Create new export job
    const newJob: ExportJob = {
      id: `job${Date.now()}`,
      type: config.type,
      format: config.format,
      status: 'processing',
      createdAt: new Date().toISOString(),
    }
    
    setExportJobs(prev => [newJob, ...prev])
    
    // Simulate export process
    setTimeout(() => {
      setExportJobs(prev => prev.map(job => 
        job.id === newJob.id 
          ? { 
              ...job, 
              status: 'completed',
              downloadUrl: `/exports/${config.type}_${new Date().toISOString().split('T')[0]}.${config.format}`
            }
          : job
      ))
      setIsGenerating(false)
    }, 3000)
  }

  const handleDownload = (job: ExportJob) => {
    if (job.downloadUrl) {
      // Mock download - in real app, this would trigger actual download
      const link = document.createElement('a')
      link.href = job.downloadUrl
      link.download = `${job.type}_export.${job.format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(isRTL ? 'ar-SA' : 'en-US')
  }

  const getStatusColor = (status: ExportJob['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'processing':
        return 'text-blue-600 bg-blue-50'
      case 'error':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'error':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent" />
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Export Configuration */}
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              {isRTL ? 'إنشاء تقرير جديد' : 'Generate New Report'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Export Type Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">
                {isRTL ? 'نوع البيانات' : 'Data Type'}
              </label>
              <div className="grid gap-3 md:grid-cols-3">
                {exportTypes.map((type) => (
                  <div
                    key={type.value}
                    onClick={() => setConfig({ ...config, type: type.value as ExportConfig['type'] })}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      config.type === type.value
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <type.icon className="h-4 w-4" />
                      <span className="font-medium text-sm">{type.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{type.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Date Range */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  {isRTL ? 'من تاريخ' : 'From Date'}
                </label>
                <input
                  type="date"
                  value={config.dateRange.from}
                  onChange={(e) => setConfig({
                    ...config,
                    dateRange: { ...config.dateRange, from: e.target.value }
                  })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  {isRTL ? 'إلى تاريخ' : 'To Date'}
                </label>
                <input
                  type="date"
                  value={config.dateRange.to}
                  onChange={(e) => setConfig({
                    ...config,
                    dateRange: { ...config.dateRange, to: e.target.value }
                  })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {/* Format Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">
                {isRTL ? 'صيغة الملف' : 'File Format'}
              </label>
              <div className="flex gap-2">
                {formatOptions.map((format) => (
                  <Button
                    key={format.value}
                    variant={config.format === format.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setConfig({ ...config, format: format.value as ExportConfig['format'] })}
                  >
                    <format.icon className="h-4 w-4 mr-2" />
                    {format.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Options */}
            <div>
              <label className="text-sm font-medium mb-3 block">
                {isRTL ? 'خيارات التصدير' : 'Export Options'}
              </label>
              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.includeDetails}
                    onChange={(e) => setConfig({ ...config, includeDetails: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">
                    {isRTL ? 'تضمين التفاصيل الكاملة' : 'Include full details'}
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.includeSentiment}
                    onChange={(e) => setConfig({ ...config, includeSentiment: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">
                    {isRTL ? 'تضمين تحليل المشاعر' : 'Include sentiment analysis'}
                  </span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.includeAIMetrics}
                    onChange={(e) => setConfig({ ...config, includeAIMetrics: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">
                    {isRTL ? 'تضمين مقاييس الذكاء الاصطناعي' : 'Include AI metrics'}
                  </span>
                </label>
              </div>
            </div>

            {/* Generate Button */}
            <Button 
              onClick={handleGenerate} 
              disabled={isGenerating}
              className="w-full"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                  {isRTL ? 'جاري الإنشاء...' : 'Generating...'}
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  {isRTL ? 'إنشاء التقرير' : 'Generate Report'}
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Export History */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {isRTL ? 'سجل التصدير' : 'Export History'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {exportJobs.map((job) => (
                <div key={job.id} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(job.status)}
                      <span className="text-sm font-medium capitalize">{job.type}</span>
                    </div>
                    <Badge className={getStatusColor(job.status)}>
                      {job.status}
                    </Badge>
                  </div>
                  
                  <div className="text-xs text-muted-foreground mb-2">
                    {formatDate(job.createdAt)} • {job.format.toUpperCase()}
                  </div>
                  
                  {job.status === 'completed' && job.downloadUrl && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(job)}
                      className="w-full"
                    >
                      <Download className="h-3 w-3 mr-1" />
                      {isRTL ? 'تحميل' : 'Download'}
                    </Button>
                  )}
                  
                  {job.status === 'error' && job.error && (
                    <div className="text-xs text-red-600 mt-1">
                      {job.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}