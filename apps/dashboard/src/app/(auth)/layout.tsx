'use client'

import { useEffect } from 'react'
import { NavigationMenu } from '@/components/shared/navigation-menu'
import { LanguageToggle } from '@/components/shared/language-toggle'
import { useAppStore } from '@/stores/app-store'
import { cn } from '@/lib/utils'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { ui } = useAppStore()
  const isRTL = ui.language === 'ar'

  useEffect(() => {
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr'
    document.documentElement.lang = ui.language
  }, [isRTL, ui.language])

  return (
    <div className="min-h-screen bg-background">
      <NavigationMenu />
      
      {/* Main content area */}
      <div
        className={cn(
          'transition-all duration-300',
          ui.sidebarOpen ? (isRTL ? 'lg:mr-64' : 'lg:ml-64') : '',
          'pt-16 lg:pt-0'
        )}
      >
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-4 lg:px-6">
          <div className="flex-1" />
          
          <div className="flex items-center gap-4">
            <LanguageToggle />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1">
          <div className="container mx-auto p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}