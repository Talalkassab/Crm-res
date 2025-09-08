'use client'

import { useState, useEffect } from 'react'
import { Clock, Sun, Moon } from 'lucide-react'

interface PrayerTime {
  name: string
  time: string
  isNext: boolean
}

const mockPrayerTimes: PrayerTime[] = [
  { name: 'الفجر', time: '05:30', isNext: false },
  { name: 'الشروق', time: '06:45', isNext: false },
  { name: 'الظهر', time: '12:15', isNext: true },
  { name: 'العصر', time: '15:30', isNext: false },
  { name: 'المغرب', time: '18:45', isNext: false },
  { name: 'العشاء', time: '20:15', isNext: false }
]

export function PrayerTimeWidget() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isPauseMode, setIsPauseMode] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ar-SA', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  const getCurrentPrayer = () => {
    const now = formatTime(currentTime)
    const currentHour = parseInt(now.split(':')[0])
    const currentMinute = parseInt(now.split(':')[1])
    const currentTimeMinutes = currentHour * 60 + currentMinute

    for (const prayer of mockPrayerTimes) {
      const [prayerHour, prayerMinute] = prayer.time.split(':').map(Number)
      const prayerTimeMinutes = prayerHour * 60 + prayerMinute

      if (currentTimeMinutes < prayerTimeMinutes) {
        return prayer
      }
    }

    return mockPrayerTimes[0] // Default to Fajr if past Isha
  }

  const nextPrayer = getCurrentPrayer()

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">أوقات الصلاة</h3>
          <div className="flex items-center text-sm text-gray-500">
            <Clock className="w-4 h-4 ml-1" />
            {formatTime(currentTime)}
          </div>
        </div>

        {/* Next Prayer Highlight */}
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900">الصلاة التالية</p>
              <p className="text-lg font-bold text-blue-900">{nextPrayer.name}</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-blue-900">{nextPrayer.time}</p>
              <p className="text-xs text-blue-700">متبقي</p>
            </div>
          </div>
        </div>

        {/* Prayer Times List */}
        <div className="space-y-2">
          {mockPrayerTimes.map((prayer, index) => (
            <div
              key={index}
              className={`flex items-center justify-between py-2 px-3 rounded-md ${
                prayer.isNext
                  ? 'bg-blue-100 text-blue-900'
                  : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center">
                {prayer.name === 'الفجر' || prayer.name === 'المغرب' ? (
                  <Sun className="w-4 h-4 text-orange-500 ml-2" />
                ) : (
                  <Moon className="w-4 h-4 text-indigo-500 ml-2" />
                )}
                <span className="text-sm font-medium">{prayer.name}</span>
              </div>
              <span className="text-sm font-mono">{prayer.time}</span>
            </div>
          ))}
        </div>

        {/* Pause Mode Toggle */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">وضع التوقف</p>
              <p className="text-xs text-gray-500">إيقاف الرسائل أثناء الصلاة</p>
            </div>
            <button
              onClick={() => setIsPauseMode(!isPauseMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                isPauseMode ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isPauseMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="mt-3 flex items-center text-xs">
          <div className={`w-2 h-2 rounded-full ml-2 ${isPauseMode ? 'bg-red-500' : 'bg-green-500'}`} />
          <span className={isPauseMode ? 'text-red-600' : 'text-green-600'}>
            {isPauseMode ? 'متوقف مؤقتاً' : 'نشط'}
          </span>
        </div>
      </div>
    </div>
  )
}