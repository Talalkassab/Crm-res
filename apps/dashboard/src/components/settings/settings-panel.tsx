'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Save, AlertTriangle, CheckCircle } from 'lucide-react'

interface OperatingHours {
  [key: string]: {
    open: string
    close: string
    enabled: boolean
  }
}

interface RestaurantSettings {
  name: string
  nameAr: string
  description: string
  descriptionAr: string
  operatingHours: OperatingHours
  timezone: string
  supportedLanguages: ('ar' | 'en')[]
  defaultLanguage: 'ar' | 'en'
  enablePrayerTimeClosures: boolean
  prayerTimeCity: string
  emergencyContact: string
  maxDailyOrders: number
}

export function SettingsPanel() {
  const { ui, restaurant, setRestaurant } = useAppStore()
  const isRTL = ui.language === 'ar'
  
  const [settings, setSettings] = useState<RestaurantSettings>({
    name: restaurant?.name || '',
    nameAr: restaurant?.nameAr || '',
    description: '',
    descriptionAr: '',
    operatingHours: {
      sunday: { open: '08:00', close: '23:00', enabled: true },
      monday: { open: '08:00', close: '23:00', enabled: true },
      tuesday: { open: '08:00', close: '23:00', enabled: true },
      wednesday: { open: '08:00', close: '23:00', enabled: true },
      thursday: { open: '08:00', close: '23:00', enabled: true },
      friday: { open: '14:00', close: '23:00', enabled: true }, // Special Friday hours
      saturday: { open: '08:00', close: '23:00', enabled: true },
    },
    timezone: 'Asia/Riyadh',
    supportedLanguages: ['ar', 'en'],
    defaultLanguage: 'ar',
    enablePrayerTimeClosures: true,
    prayerTimeCity: 'Riyadh',
    emergencyContact: '+966501234567',
    maxDailyOrders: 100,
  })
  
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<{type: 'success' | 'error', message: string} | null>(null)

  const dayNames = {
    sunday: { en: 'Sunday', ar: 'الأحد' },
    monday: { en: 'Monday', ar: 'الاثنين' },
    tuesday: { en: 'Tuesday', ar: 'الثلاثاء' },
    wednesday: { en: 'Wednesday', ar: 'الأربعاء' },
    thursday: { en: 'Thursday', ar: 'الخميس' },
    friday: { en: 'Friday', ar: 'الجمعة' },
    saturday: { en: 'Saturday', ar: 'السبت' },
  }

  const saudiCities = [
    { value: 'Riyadh', label: isRTL ? 'الرياض' : 'Riyadh' },
    { value: 'Jeddah', label: isRTL ? 'جدة' : 'Jeddah' },
    { value: 'Makkah', label: isRTL ? 'مكة المكرمة' : 'Makkah' },
    { value: 'Madinah', label: isRTL ? 'المدينة المنورة' : 'Madinah' },
    { value: 'Dammam', label: isRTL ? 'الدمام' : 'Dammam' },
    { value: 'Taif', label: isRTL ? 'الطائف' : 'Taif' },
    { value: 'Tabuk', label: isRTL ? 'تبوك' : 'Tabuk' },
  ]

  const handleSave = async () => {
    setIsSaving(true)
    setSaveMessage(null)

    try {
      // Mock API call - in real app, this would save to backend
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Update restaurant in store if needed
      if (restaurant) {
        setRestaurant({
          ...restaurant,
          name: settings.name,
          nameAr: settings.nameAr,
        })
      }

      setSaveMessage({
        type: 'success',
        message: isRTL ? 'تم حفظ الإعدادات بنجاح' : 'Settings saved successfully'
      })
    } catch (error) {
      setSaveMessage({
        type: 'error',
        message: isRTL ? 'حدث خطأ أثناء حفظ الإعدادات' : 'Error saving settings'
      })
    } finally {
      setIsSaving(false)
    }
  }

  const updateOperatingHours = (day: string, field: 'open' | 'close' | 'enabled', value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      operatingHours: {
        ...prev.operatingHours,
        [day]: {
          ...prev.operatingHours[day],
          [field]: value
        }
      }
    }))
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isRTL ? 'المعلومات الأساسية' : 'Basic Information'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-medium mb-2 block">
                {isRTL ? 'اسم المطعم (الإنجليزية)' : 'Restaurant Name (English)'}
              </label>
              <input
                type="text"
                value={settings.name}
                onChange={(e) => setSettings({...settings, name: e.target.value})}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Restaurant Name"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">
                {isRTL ? 'اسم المطعم (العربية)' : 'Restaurant Name (Arabic)'}
              </label>
              <input
                type="text"
                value={settings.nameAr}
                onChange={(e) => setSettings({...settings, nameAr: e.target.value})}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="اسم المطعم"
                dir="rtl"
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-medium mb-2 block">
                {isRTL ? 'رقم الطوارئ' : 'Emergency Contact'}
              </label>
              <input
                type="tel"
                value={settings.emergencyContact}
                onChange={(e) => setSettings({...settings, emergencyContact: e.target.value})}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="+966XXXXXXXXX"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">
                {isRTL ? 'الحد الأقصى للطلبات اليومية' : 'Max Daily Orders'}
              </label>
              <input
                type="number"
                value={settings.maxDailyOrders}
                onChange={(e) => setSettings({...settings, maxDailyOrders: parseInt(e.target.value) || 0})}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                min="1"
                max="1000"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Operating Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            {isRTL ? 'ساعات العمل' : 'Operating Hours'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(dayNames).map(([day, names]) => (
              <div key={day} className="flex items-center gap-4 p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.operatingHours[day].enabled}
                    onChange={(e) => updateOperatingHours(day, 'enabled', e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="font-medium w-20 text-sm">
                    {names[ui.language]}
                  </span>
                </div>
                
                {settings.operatingHours[day].enabled ? (
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      type="time"
                      value={settings.operatingHours[day].open}
                      onChange={(e) => updateOperatingHours(day, 'open', e.target.value)}
                      className="px-2 py-1 border rounded text-sm"
                    />
                    <span className="text-sm text-muted-foreground">
                      {isRTL ? 'إلى' : 'to'}
                    </span>
                    <input
                      type="time"
                      value={settings.operatingHours[day].close}
                      onChange={(e) => updateOperatingHours(day, 'close', e.target.value)}
                      className="px-2 py-1 border rounded text-sm"
                    />
                  </div>
                ) : (
                  <span className="text-sm text-muted-foreground">
                    {isRTL ? 'مغلق' : 'Closed'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Language Settings */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isRTL ? 'إعدادات اللغة' : 'Language Settings'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              {isRTL ? 'اللغة الافتراضية' : 'Default Language'}
            </label>
            <select
              value={settings.defaultLanguage}
              onChange={(e) => setSettings({...settings, defaultLanguage: e.target.value as 'ar' | 'en'})}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="ar">{isRTL ? 'العربية' : 'Arabic'}</option>
              <option value="en">{isRTL ? 'الإنجليزية' : 'English'}</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              {isRTL ? 'اللغات المدعومة' : 'Supported Languages'}
            </label>
            <div className="flex gap-2">
              <Badge variant={settings.supportedLanguages.includes('ar') ? 'default' : 'secondary'}>
                {isRTL ? 'العربية' : 'Arabic'}
              </Badge>
              <Badge variant={settings.supportedLanguages.includes('en') ? 'default' : 'secondary'}>
                {isRTL ? 'الإنجليزية' : 'English'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prayer Time Settings */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isRTL ? 'إعدادات أوقات الصلاة' : 'Prayer Time Settings'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.enablePrayerTimeClosures}
              onChange={(e) => setSettings({...settings, enablePrayerTimeClosures: e.target.checked})}
              className="w-4 h-4"
            />
            <label className="text-sm">
              {isRTL ? 'إغلاق مؤقت أثناء أوقات الصلاة' : 'Temporary closure during prayer times'}
            </label>
          </div>

          {settings.enablePrayerTimeClosures && (
            <div>
              <label className="text-sm font-medium mb-2 block">
                {isRTL ? 'المدينة' : 'City'}
              </label>
              <select
                value={settings.prayerTimeCity}
                onChange={(e) => setSettings({...settings, prayerTimeCity: e.target.value})}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {saudiCities.map((city) => (
                  <option key={city.value} value={city.value}>
                    {city.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Save Button and Status */}
      <div className="flex items-center justify-between">
        <div>
          {saveMessage && (
            <div className={`flex items-center gap-2 text-sm ${
              saveMessage.type === 'success' ? 'text-green-600' : 'text-red-600'
            }`}>
              {saveMessage.type === 'success' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
              {saveMessage.message}
            </div>
          )}
        </div>

        <Button onClick={handleSave} disabled={isSaving} size="lg">
          {isSaving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
              {isRTL ? 'جاري الحفظ...' : 'Saving...'}
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              {isRTL ? 'حفظ الإعدادات' : 'Save Settings'}
            </>
          )}
        </Button>
      </div>
    </div>
  )
}