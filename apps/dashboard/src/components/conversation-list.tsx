'use client'

import { useState } from 'react'
import { MessageCircle, Clock, CheckCircle, AlertCircle } from 'lucide-react'

interface Conversation {
  id: string
  customerName: string
  phoneNumber: string
  lastMessage: string
  timestamp: string
  status: 'active' | 'waiting' | 'resolved' | 'urgent'
  messageCount: number
  sentiment: 'positive' | 'neutral' | 'negative'
}

const mockConversations: Conversation[] = [
  {
    id: '1',
    customerName: 'أحمد محمد',
    phoneNumber: '+966501234567',
    lastMessage: 'شكراً لكم، الطعام كان لذيذ جداً!',
    timestamp: 'منذ 5 دقائق',
    status: 'resolved',
    messageCount: 8,
    sentiment: 'positive'
  },
  {
    id: '2',
    customerName: 'فاطمة العتيبي',
    phoneNumber: '+966507654321',
    lastMessage: 'هل يمكنني تغيير موعد الحجز؟',
    timestamp: 'منذ 12 دقيقة',
    status: 'waiting',
    messageCount: 3,
    sentiment: 'neutral'
  },
  {
    id: '3',
    customerName: 'سعد القحطاني',
    phoneNumber: '+966509876543',
    lastMessage: 'الخدمة كانت بطيئة جداً!',
    timestamp: 'منذ 20 دقيقة',
    status: 'urgent',
    messageCount: 5,
    sentiment: 'negative'
  },
  {
    id: '4',
    customerName: 'نورا السعيد',
    phoneNumber: '+966501112233',
    lastMessage: 'أريد حجز طاولة لشخصين',
    timestamp: 'منذ ساعة',
    status: 'active',
    messageCount: 2,
    sentiment: 'neutral'
  }
]

function getStatusIcon(status: Conversation['status']) {
  switch (status) {
    case 'active':
      return <MessageCircle className="w-4 h-4 text-blue-500" />
    case 'waiting':
      return <Clock className="w-4 h-4 text-yellow-500" />
    case 'resolved':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'urgent':
      return <AlertCircle className="w-4 h-4 text-red-500" />
  }
}

function getStatusColor(status: Conversation['status']) {
  switch (status) {
    case 'active':
      return 'bg-blue-100 text-blue-800'
    case 'waiting':
      return 'bg-yellow-100 text-yellow-800'
    case 'resolved':
      return 'bg-green-100 text-green-800'
    case 'urgent':
      return 'bg-red-100 text-red-800'
  }
}

function getStatusText(status: Conversation['status']) {
  switch (status) {
    case 'active':
      return 'نشط'
    case 'waiting':
      return 'في الانتظار'
    case 'resolved':
      return 'تم الحل'
    case 'urgent':
      return 'عاجل'
  }
}

function getSentimentColor(sentiment: Conversation['sentiment']) {
  switch (sentiment) {
    case 'positive':
      return 'text-green-600'
    case 'neutral':
      return 'text-gray-600'
    case 'negative':
      return 'text-red-600'
  }
}

export function ConversationList() {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="space-y-4">
          {mockConversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                selectedConversation === conversation.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedConversation(conversation.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 space-x-reverse">
                    <div className="flex-shrink-0">
                      {getStatusIcon(conversation.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {conversation.customerName}
                        </p>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(conversation.status)}`}>
                          {getStatusText(conversation.status)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 truncate">
                        {conversation.phoneNumber}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-2">
                    <p className={`text-sm ${getSentimentColor(conversation.sentiment)}`}>
                      {conversation.lastMessage}
                    </p>
                  </div>
                  
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <span>{conversation.timestamp}</span>
                    <span>{conversation.messageCount} رسالة</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {mockConversations.length === 0 && (
          <div className="text-center py-8">
            <MessageCircle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">لا توجد محادثات</h3>
            <p className="mt-1 text-sm text-gray-500">ستظهر المحادثات هنا عند وصولها</p>
          </div>
        )}
      </div>
    </div>
  )
}