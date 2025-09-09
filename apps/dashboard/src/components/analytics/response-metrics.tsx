'use client'

import { useAppStore } from '@/stores/app-store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Clock, MessageSquare, CheckCircle, AlertCircle } from 'lucide-react'

export function ResponseMetrics() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock response time data by hour
  const responseTimeData = [
    { hour: '00:00', avgTime: 1.2, responses: 12 },
    { hour: '02:00', avgTime: 0.8, responses: 8 },
    { hour: '04:00', avgTime: 1.5, responses: 5 },
    { hour: '06:00', avgTime: 2.1, responses: 18 },
    { hour: '08:00', avgTime: 3.2, responses: 45 },
    { hour: '10:00', avgTime: 2.8, responses: 67 },
    { hour: '12:00', avgTime: 4.1, responses: 89 },
    { hour: '14:00', avgTime: 3.7, responses: 78 },
    { hour: '16:00', avgTime: 3.9, responses: 82 },
    { hour: '18:00', avgTime: 4.5, responses: 95 },
    { hour: '20:00', avgTime: 3.1, responses: 71 },
    { hour: '22:00', avgTime: 2.3, responses: 34 },
  ]

  // Response rate by conversation type
  const responseRateByType = [
    { 
      type: isRTL ? 'ملاحظات' : 'Feedback',
      rate: 96.5,
      count: 234,
      avgTime: '1.8m'
    },
    { 
      type: isRTL ? 'طلبات' : 'Orders',
      rate: 98.2,
      count: 156,
      avgTime: '2.1m'
    },
    { 
      type: isRTL ? 'دعم' : 'Support',
      rate: 89.3,
      count: 89,
      avgTime: '4.2m'
    },
    { 
      type: isRTL ? 'عام' : 'General',
      rate: 92.1,
      count: 67,
      avgTime: '3.5m'
    },
  ]

  // Summary metrics
  const summaryMetrics = [
    {
      title: isRTL ? 'متوسط وقت الاستجابة' : 'Avg Response Time',
      value: '2.4m',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: isRTL ? 'معدل الاستجابة' : 'Response Rate',
      value: '94.5%',
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: isRTL ? 'الردود اليوم' : 'Responses Today',
      value: '342',
      icon: MessageSquare,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: isRTL ? 'الاستجابات المتأخرة' : 'Late Responses',
      value: '18',
      icon: AlertCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ]

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {summaryMetrics.map((metric, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${metric.bgColor}`}>
                  <metric.icon className={`h-4 w-4 ${metric.color}`} />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{metric.value}</div>
                  <div className="text-xs text-muted-foreground">{metric.title}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Response Time by Hour */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {isRTL ? 'وقت الاستجابة حسب الساعة' : 'Response Time by Hour'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `${value}${name === 'avgTime' ? 'm' : ''}`,
                    name === 'avgTime' ? (isRTL ? 'متوسط الوقت' : 'Avg Time') : (isRTL ? 'الردود' : 'Responses')
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="avgTime"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Response Rate by Type */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {isRTL ? 'معدل الاستجابة حسب النوع' : 'Response Rate by Type'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {responseRateByType.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{item.type}</span>
                      <span className="text-sm font-bold">{item.rate}%</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{item.count} {isRTL ? 'محادثة' : 'conversations'}</span>
                      <span>{isRTL ? 'متوسط:' : 'Avg:'} {item.avgTime}</span>
                    </div>
                    <div className="mt-2 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${item.rate}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}