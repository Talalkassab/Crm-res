'use client'

import { MessageCircle, Users, Clock, TrendingUp } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  change: string
  changeType: 'positive' | 'negative' | 'neutral'
  icon: React.ReactNode
}

function StatCard({ title, value, change, changeType, icon }: StatCardProps) {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }[changeType]

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
              {icon}
            </div>
          </div>
          <div className="mr-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value}
                </div>
                <div className={`mr-2 flex items-baseline text-sm font-semibold ${changeColor}`}>
                  {change}
                </div>
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}

export function StatsCards() {
  const stats = [
    {
      title: 'إجمالي المحادثات',
      value: '1,234',
      change: '+12%',
      changeType: 'positive' as const,
      icon: <MessageCircle className="w-5 h-5 text-blue-600" />
    },
    {
      title: 'العملاء النشطون',
      value: '456',
      change: '+8%',
      changeType: 'positive' as const,
      icon: <Users className="w-5 h-5 text-green-600" />
    },
    {
      title: 'متوسط وقت الاستجابة',
      value: '2.3 دقيقة',
      change: '-15%',
      changeType: 'positive' as const,
      icon: <Clock className="w-5 h-5 text-yellow-600" />
    },
    {
      title: 'معدل الرضا',
      value: '94%',
      change: '+3%',
      changeType: 'positive' as const,
      icon: <TrendingUp className="w-5 h-5 text-purple-600" />
    }
  ]

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  )
}