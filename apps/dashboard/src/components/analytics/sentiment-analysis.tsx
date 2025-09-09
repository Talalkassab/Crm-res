'use client'

import { useAppStore } from '@/stores/app-store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Smile, Meh, Frown, TrendingUp, TrendingDown } from 'lucide-react'

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#f59e0b',
  negative: '#ef4444',
}

export function SentimentAnalysis() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock sentiment distribution data
  const sentimentData = [
    { 
      name: isRTL ? 'إيجابي' : 'Positive',
      value: 68,
      count: 342,
      color: SENTIMENT_COLORS.positive 
    },
    { 
      name: isRTL ? 'محايد' : 'Neutral',
      value: 24,
      count: 120,
      color: SENTIMENT_COLORS.neutral 
    },
    { 
      name: isRTL ? 'سلبي' : 'Negative',
      value: 8,
      count: 40,
      color: SENTIMENT_COLORS.negative 
    },
  ]

  // Sentiment trend over time
  const sentimentTrend = [
    { date: isRTL ? '1 يناير' : 'Jan 1', positive: 65, neutral: 27, negative: 8 },
    { date: isRTL ? '8 يناير' : 'Jan 8', positive: 70, neutral: 22, negative: 8 },
    { date: isRTL ? '15 يناير' : 'Jan 15', positive: 68, neutral: 25, negative: 7 },
    { date: isRTL ? '22 يناير' : 'Jan 22', positive: 72, neutral: 21, negative: 7 },
    { date: isRTL ? '29 يناير' : 'Jan 29', positive: 68, neutral: 24, negative: 8 },
  ]

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <Smile className="h-4 w-4 text-green-600" />
      case 'neutral':
        return <Meh className="h-4 w-4 text-yellow-600" />
      case 'negative':
        return <Frown className="h-4 w-4 text-red-600" />
      default:
        return null
    }
  }

  const renderCustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-medium">{`${payload[0].payload.name}: ${payload[0].value}%`}</p>
          <p className="text-sm text-muted-foreground">{`${payload[0].payload.count} ${isRTL ? 'رد' : 'responses'}`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Sentiment Distribution Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {isRTL ? 'توزيع المشاعر' : 'Sentiment Distribution'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col lg:flex-row items-center gap-4">
            <div className="w-full lg:w-1/2">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={renderCustomTooltip} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="w-full lg:w-1/2 space-y-3">
              {sentimentData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-2">
                    {getSentimentIcon(index === 0 ? 'positive' : index === 1 ? 'neutral' : 'negative')}
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold">{item.value}%</div>
                    <div className="text-xs text-muted-foreground">{item.count}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sentiment Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {isRTL ? 'اتجاه المشاعر' : 'Sentiment Trend'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={sentimentTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="positive"
                stackId="1"
                stroke={SENTIMENT_COLORS.positive}
                fill={SENTIMENT_COLORS.positive}
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="neutral"
                stackId="1"
                stroke={SENTIMENT_COLORS.neutral}
                fill={SENTIMENT_COLORS.neutral}
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="negative"
                stackId="1"
                stroke={SENTIMENT_COLORS.negative}
                fill={SENTIMENT_COLORS.negative}
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}