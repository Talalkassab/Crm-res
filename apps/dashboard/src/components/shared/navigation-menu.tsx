'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/app-store'
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  Settings,
  Search,
  Download,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const navigation = [
  {
    name: { en: 'Dashboard', ar: 'لوحة التحكم' },
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: { en: 'Conversations', ar: 'المحادثات' },
    href: '/conversations',
    icon: MessageSquare,
  },
  {
    name: { en: 'Search', ar: 'البحث' },
    href: '/search',
    icon: Search,
  },
  {
    name: { en: 'Analytics', ar: 'التحليلات' },
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: { en: 'Export', ar: 'التصدير' },
    href: '/export',
    icon: Download,
  },
  {
    name: { en: 'Settings', ar: 'الإعدادات' },
    href: '/settings',
    icon: Settings,
  },
]

export function NavigationMenu() {
  const pathname = usePathname()
  const { ui, setSidebarOpen } = useAppStore()
  const isRTL = ui.language === 'ar'

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setSidebarOpen(!ui.sidebarOpen)}
      >
        {ui.sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 z-40 flex w-64 flex-col bg-card transition-transform duration-300 lg:translate-x-0',
          isRTL ? 'right-0' : 'left-0',
          ui.sidebarOpen ? 'translate-x-0' : isRTL ? 'translate-x-full' : '-translate-x-full'
        )}
      >
        {/* Sidebar header */}
        <div className="flex h-16 items-center justify-between px-4 border-b">
          <h2 className="text-lg font-semibold">
            {isRTL ? 'نظام إدارة المطاعم' : 'CRM-RES'}
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="hidden lg:flex"
            onClick={() => setSidebarOpen(!ui.sidebarOpen)}
          >
            {isRTL ? (
              ui.sidebarOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />
            ) : (
              ui.sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 space-y-1 px-2 py-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {ui.sidebarOpen && (
                  <span>{item.name[ui.language]}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Restaurant selector */}
        {ui.sidebarOpen && (
          <div className="border-t p-4">
            <div className="text-sm text-muted-foreground mb-2">
              {isRTL ? 'الفرع الحالي' : 'Current Branch'}
            </div>
            <div className="font-medium">
              {useAppStore.getState().selectedBranch?.name || (isRTL ? 'جميع الفروع' : 'All Branches')}
            </div>
          </div>
        )}
      </div>

      {/* Overlay for mobile */}
      {ui.sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  )
}