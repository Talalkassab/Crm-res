'use client'

import { useAppStore } from '@/stores/app-store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface SatisfactionChartProps {
  type?: 'line' | 'bar'
}

export function SatisfactionChart({ type = 'line' }: SatisfactionChartProps) {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'

  // Mock data for ratings trend over last 30 days
  const ratingTrendData = [
    { date: isRTL ? '1 يناير' : 'Jan 1', rating: 4.1, responses: 45 },
    { date: isRTL ? '5 يناير' : 'Jan 5', rating: 4.2, responses: 52 },
    { date: isRTL ? '10 يناير' : 'Jan 10', rating: 4.0, responses: 38 },
    { date: isRTL ? '15 يناير' : 'Jan 15', rating: 4.3, responses: 67 },
    { date: isRTL ? '20 يناير' : 'Jan 20', rating: 4.4, responses: 71 },
    { date: isRTL ? '25 يناير' : 'Jan 25', rating: 4.2, responses: 59 },
    { date: isRTL ? '30 يناير' : 'Jan 30', rating: 4.5, responses: 78 },
  ]

  // Rating distribution data
  const ratingDistribution = [
    { stars: '5★', count: 245, percentage: 42 },
    { stars: '4★', count: 189, percentage: 32 },
    { stars: '3★', count: 98, percentage: 17 },
    { stars: '2★', count: 35, percentage: 6 },
    { stars: '1★', count: 18, percentage: 3 },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Rating Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {isRTL ? 'اتجاه التقييمات' : 'Rating Trend'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            {type === 'line' ? (
              <LineChart data={ratingTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[1, 5]} />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    value.toFixed(1),
                    name === 'rating' ? (isRTL ? 'التقييم' : 'Rating') : (isRTL ? 'الردود' : 'Responses')
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="rating"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ fill: '#2563eb' }}
                />
              </LineChart>
            ) : (
              <BarChart data={ratingTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    value,
                    name === 'responses' ? (isRTL ? 'الردود' : 'Responses') : (isRTL ? 'التقييم' : 'Rating')
                  ]}
                />
                <Bar dataKey="responses" fill="#3b82f6" />
              </BarChart>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Rating Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {isRTL ? 'توزيع التقييمات' : 'Rating Distribution'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {ratingDistribution.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{item.stars}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2 w-32">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-sm">{item.count}</div>
                  <div className="text-xs text-muted-foreground">{item.percentage}%</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}