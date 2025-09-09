'use client'

import { useAppStore } from '@/stores/app-store'
import { Button } from '@/components/ui/button'
import { Languages } from 'lucide-react'

export function LanguageToggle() {
  const { ui, toggleLanguage } = useAppStore()
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleLanguage}
      className="relative"
      aria-label={ui.language === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
    >
      <Languages className="h-5 w-5" />
      <span className="sr-only">
        {ui.language === 'ar' ? 'EN' : 'عربي'}
      </span>
      <span className="absolute -bottom-1 -right-1 text-xs font-bold">
        {ui.language === 'ar' ? 'EN' : 'ع'}
      </span>
    </Button>
  )
}