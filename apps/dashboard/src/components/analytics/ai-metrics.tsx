'use client'

import { useAppStore } from '@/stores/app-store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Area, AreaChart } from 'recharts'
import { 
  Bot, 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Target, 
  Clock, 
  CheckCircle2,
  AlertTriangle,
  Activity
} from 'lucide-react'

export function AIMetrics() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock AI performance data
  const aiMetricsData = {
    automationRate: 87.2,
    automationTrend: 5.3,
    avgConfidence: 0.78,
    confidenceTrend: 3.1,
    escalationRate: 12.8,
    escalationTrend: -8.2,
    successfulResolutions: 91.5,
    resolutionTrend: 4.2,
    responseTime: '1.8s',
    responseTimeTrend: -12.3,
  }

  // Confidence distribution over time
  const confidenceData = [
    { time: isRTL ? '00:00' : '12 AM', high: 45, medium: 32, low: 8 },
    { time: isRTL ? '06:00' : '6 AM', high: 28, medium: 18, low: 4 },
    { time: isRTL ? '12:00' : '12 PM', high: 78, medium: 45, low: 12 },
    { time: isRTL ? '18:00' : '6 PM', high: 89, medium: 52, low: 15 },
    { time: isRTL ? '00:00' : '12 AM', high: 34, medium: 28, low: 6 },
  ]

  // AI performance trend over the last 30 days
  const performanceTrend = [
    { date: '1', automation: 82, confidence: 0.74, escalation: 18 },
    { date: '7', automation: 84, confidence: 0.76, escalation: 16 },
    { date: '14', automation: 86, confidence: 0.77, escalation: 14 },
    { date: '21', automation: 87, confidence: 0.78, escalation: 13 },
    { date: '30', automation: 87.2, confidence: 0.78, escalation: 12.8 },
  ]

  // Conversation types handled by AI
  const aiHandledTypes = [
    { 
      type: isRTL ? 'ملاحظات' : 'Feedback',
      handled: 94,
      total: 156,
      avgConfidence: 0.89,
      successRate: 96
    },
    { 
      type: isRTL ? 'طلبات' : 'Orders',
      handled: 142,
      total: 178,
      avgConfidence: 0.85,
      successRate: 92
    },
    { 
      type: isRTL ? 'أسئلة عامة' : 'General',
      handled: 89,
      total: 134,
      avgConfidence: 0.72,
      successRate: 88
    },
    { 
      type: isRTL ? 'دعم' : 'Support',
      handled: 67,
      total: 98,
      avgConfidence: 0.68,
      successRate: 82
    },
  ]

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceBgColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 border-green-200'
    if (confidence >= 0.6) return 'bg-yellow-100 border-yellow-200'
    return 'bg-red-100 border-red-200'
  }

  const getTrendIcon = (trend: number) => {
    return trend > 0 ? (
      <TrendingUp className="h-4 w-4 text-green-600" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-600" />
    )
  }

  return (
    <div className="space-y-6">
      {/* Key AI Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {isRTL ? 'معدل الأتمتة' : 'Automation Rate'}
                </p>
                <p className="text-2xl font-bold">{aiMetricsData.automationRate}%</p>
                <div className="flex items-center text-xs mt-1">
                  {getTrendIcon(aiMetricsData.automationTrend)}
                  <span className={aiMetricsData.automationTrend > 0 ? 'text-green-600' : 'text-red-600'}>
                    {aiMetricsData.automationTrend > 0 ? '+' : ''}{aiMetricsData.automationTrend}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {isRTL ? 'متوسط الثقة' : 'Avg Confidence'}
                </p>
                <p className="text-2xl font-bold">{Math.round(aiMetricsData.avgConfidence * 100)}%</p>
                <div className="flex items-center text-xs mt-1">
                  {getTrendIcon(aiMetricsData.confidenceTrend)}
                  <span className={aiMetricsData.confidenceTrend > 0 ? 'text-green-600' : 'text-red-600'}>
                    {aiMetricsData.confidenceTrend > 0 ? '+' : ''}{aiMetricsData.confidenceTrend}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <Target className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {isRTL ? 'وقت الاستجابة' : 'Response Time'}
                </p>
                <p className="text-2xl font-bold">{aiMetricsData.responseTime}</p>
                <div className="flex items-center text-xs mt-1">
                  {getTrendIcon(aiMetricsData.responseTimeTrend)}
                  <span className={aiMetricsData.responseTimeTrend < 0 ? 'text-green-600' : 'text-red-600'}>
                    {aiMetricsData.responseTimeTrend > 0 ? '+' : ''}{aiMetricsData.responseTimeTrend}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {isRTL ? 'معدل النجاح' : 'Success Rate'}
                </p>
                <p className="text-2xl font-bold">{aiMetricsData.successfulResolutions}%</p>
                <div className="flex items-center text-xs mt-1">
                  {getTrendIcon(aiMetricsData.resolutionTrend)}
                  <span className={aiMetricsData.resolutionTrend > 0 ? 'text-green-600' : 'text-red-600'}>
                    {aiMetricsData.resolutionTrend > 0 ? '+' : ''}{aiMetricsData.resolutionTrend}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Performance Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {isRTL ? 'اتجاه الأداء (30 يوم)' : 'Performance Trend (30 Days)'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="automation" 
                  stroke="#3b82f6" 
                  name={isRTL ? 'الأتمتة %' : 'Automation %'}
                />
                <Line 
                  type="monotone" 
                  dataKey="escalation" 
                  stroke="#ef4444" 
                  name={isRTL ? 'التصعيد %' : 'Escalation %'}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Confidence Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {isRTL ? 'توزيع الثقة حسب الوقت' : 'Confidence Distribution by Time'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={confidenceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="high" 
                  stackId="1" 
                  stroke="#10b981" 
                  fill="#10b981"
                  fillOpacity={0.6}
                  name={isRTL ? 'ثقة عالية' : 'High Confidence'}
                />
                <Area 
                  type="monotone" 
                  dataKey="medium" 
                  stackId="1" 
                  stroke="#f59e0b" 
                  fill="#f59e0b"
                  fillOpacity={0.6}
                  name={isRTL ? 'ثقة متوسطة' : 'Medium Confidence'}
                />
                <Area 
                  type="monotone" 
                  dataKey="low" 
                  stackId="1" 
                  stroke="#ef4444" 
                  fill="#ef4444"
                  fillOpacity={0.6}
                  name={isRTL ? 'ثقة منخفضة' : 'Low Confidence'}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* AI Performance by Conversation Type */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {isRTL ? 'أداء الذكي الاصطناعي حسب نوع المحادثة' : 'AI Performance by Conversation Type'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {aiHandledTypes.map((item, index) => (
              <div key={index} className={`p-4 rounded-lg border ${getConfidenceBgColor(item.avgConfidence)}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Bot className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <h4 className="font-medium">{item.type}</h4>
                      <p className="text-sm text-muted-foreground">
                        {item.handled}/{item.total} {isRTL ? 'تم التعامل معها' : 'handled'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${getConfidenceColor(item.avgConfidence)}`}>
                      {Math.round(item.avgConfidence * 100)}%
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {isRTL ? 'ثقة متوسطة' : 'avg confidence'}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{isRTL ? 'معدل الأتمتة' : 'Automation Rate'}</span>
                    <span>{Math.round((item.handled / item.total) * 100)}%</span>
                  </div>
                  <Progress value={(item.handled / item.total) * 100} className="h-2" />
                  
                  <div className="flex justify-between text-sm">
                    <span>{isRTL ? 'معدل النجاح' : 'Success Rate'}</span>
                    <span>{item.successRate}%</span>
                  </div>
                  <Progress value={item.successRate} className="h-2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}