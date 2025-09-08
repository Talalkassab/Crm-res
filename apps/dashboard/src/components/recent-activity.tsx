'use client'

import { MessageCircle, CheckCircle, AlertTriangle, Clock } from 'lucide-react'

interface Activity {
  id: string
  type: 'message' | 'resolved' | 'urgent' | 'order'
  message: string
  timestamp: string
  customerName: string
}

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'message',
    message: 'رسالة جديدة من أحمد محمد',
    timestamp: 'منذ 5 دقائق',
    customerName: 'أحمد محمد'
  },
  {
    id: '2',
    type: 'resolved',
    message: 'تم حل مشكلة فاطمة العتيبي',
    timestamp: 'منذ 15 دقيقة',
    customerName: 'فاطمة العتيبي'
  },
  {
    id: '3',
    type: 'urgent',
    message: 'شكوى عاجلة من سعد القحطاني',
    timestamp: 'منذ 20 دقيقة',
    customerName: 'سعد القحطاني'
  },
  {
    id: '4',
    type: 'order',
    message: 'طلب جديد من نورا السعيد',
    timestamp: 'منذ ساعة',
    customerName: 'نورا السعيد'
  },
  {
    id: '5',
    type: 'message',
    message: 'رسالة من خالد الأحمد',
    timestamp: 'منذ ساعتين',
    customerName: 'خالد الأحمد'
  }
]

function getActivityIcon(type: Activity['type']) {
  switch (type) {
    case 'message':
      return <MessageCircle className="w-4 h-4 text-blue-500" />
    case 'resolved':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'urgent':
      return <AlertTriangle className="w-4 h-4 text-red-500" />
    case 'order':
      return <Clock className="w-4 h-4 text-purple-500" />
  }
}

function getActivityColor(type: Activity['type']) {
  switch (type) {
    case 'message':
      return 'text-blue-600'
    case 'resolved':
      return 'text-green-600'
    case 'urgent':
      return 'text-red-600'
    case 'order':
      return 'text-purple-600'
  }
}

export function RecentActivity() {
  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flow-root">
          <ul className="-mb-8">
            {mockActivities.map((activity, activityIdx) => (
              <li key={activity.id}>
                <div className="relative pb-8">
                  {activityIdx !== mockActivities.length - 1 ? (
                    <span
                      className="absolute top-4 right-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex space-x-3 space-x-reverse">
                    <div>
                      <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${getActivityColor(activity.type)}`}>
                        {getActivityIcon(activity.type)}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4 space-x-reverse">
                      <div>
                        <p className={`text-sm ${getActivityColor(activity.type)}`}>
                          {activity.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {activity.customerName}
                        </p>
                      </div>
                      <div className="text-right text-xs whitespace-nowrap text-gray-500">
                        {activity.timestamp}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {mockActivities.length === 0 && (
          <div className="text-center py-4">
            <Clock className="mx-auto h-8 w-8 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">لا يوجد نشاط</h3>
            <p className="mt-1 text-sm text-gray-500">ستظهر الأنشطة هنا عند حدوثها</p>
          </div>
        )}

        <div className="mt-6">
          <a
            href="#"
            className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            عرض جميع الأنشطة
          </a>
        </div>
      </div>
    </div>
  )
}