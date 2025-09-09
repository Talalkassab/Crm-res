'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { SettingsPanel } from '@/components/settings/settings-panel'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Settings, User, Bell, Shield, Palette, Globe } from 'lucide-react'

type SettingsTab = 'restaurant' | 'profile' | 'notifications' | 'security' | 'appearance' | 'integrations'

export default function SettingsPage() {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'
  const [activeTab, setActiveTab] = useState<SettingsTab>('restaurant')

  const tabs: { id: SettingsTab; label: string; icon: React.ElementType; description: string }[] = [
    {
      id: 'restaurant',
      label: isRTL ? 'إعدادات المطعم' : 'Restaurant Settings',
      icon: Settings,
      description: isRTL ? 'ساعات العمل والمعلومات الأساسية' : 'Operating hours and basic information',
    },
    {
      id: 'profile',
      label: isRTL ? 'الملف الشخصي' : 'Profile',
      icon: User,
      description: isRTL ? 'معلوماتك الشخصية والحساب' : 'Your personal information and account',
    },
    {
      id: 'notifications',
      label: isRTL ? 'الإشعارات' : 'Notifications',
      icon: Bell,
      description: isRTL ? 'تفضيلات الإشعارات والتنبيهات' : 'Notification preferences and alerts',
    },
    {
      id: 'security',
      label: isRTL ? 'الأمان' : 'Security',
      icon: Shield,
      description: isRTL ? 'كلمة المرور وإعدادات الأمان' : 'Password and security settings',
    },
    {
      id: 'appearance',
      label: isRTL ? 'المظهر' : 'Appearance',
      icon: Palette,
      description: isRTL ? 'السمة واللغة' : 'Theme and language preferences',
    },
    {
      id: 'integrations',
      label: isRTL ? 'التكاملات' : 'Integrations',
      icon: Globe,
      description: isRTL ? 'الاتصال بالخدمات الخارجية' : 'Connect external services',
    },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'restaurant':
        return <SettingsPanel />
      case 'profile':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isRTL ? 'إعدادات الملف الشخصي' : 'Profile Settings'}
            </h3>
            <p className="text-muted-foreground">
              {isRTL ? 'قريباً...' : 'Coming soon...'}
            </p>
          </Card>
        )
      case 'notifications':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isRTL ? 'إعدادات الإشعارات' : 'Notification Settings'}
            </h3>
            <p className="text-muted-foreground">
              {isRTL ? 'قريباً...' : 'Coming soon...'}
            </p>
          </Card>
        )
      case 'security':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isRTL ? 'إعدادات الأمان' : 'Security Settings'}
            </h3>
            <p className="text-muted-foreground">
              {isRTL ? 'قريباً...' : 'Coming soon...'}
            </p>
          </Card>
        )
      case 'appearance':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isRTL ? 'إعدادات المظهر' : 'Appearance Settings'}
            </h3>
            <p className="text-muted-foreground">
              {isRTL ? 'قريباً...' : 'Coming soon...'}
            </p>
          </Card>
        )
      case 'integrations':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isRTL ? 'إعدادات التكاملات' : 'Integration Settings'}
            </h3>
            <p className="text-muted-foreground">
              {isRTL ? 'قريباً...' : 'Coming soon...'}
            </p>
          </Card>
        )
      default:
        return <SettingsPanel />
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isRTL ? 'الإعدادات' : 'Settings'}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isRTL ? 'إدارة إعدادات المطعم والنظام' : 'Manage your restaurant and system settings'}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Settings Navigation */}
        <div className="space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-primary/10 text-primary border border-primary/20'
                  : 'hover:bg-muted'
              }`}
            >
              <div className="flex items-center gap-3">
                <tab.icon className="h-4 w-4" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{tab.label}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {tab.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}