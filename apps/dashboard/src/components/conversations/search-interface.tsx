'use client'

import { useState } from 'react'
import { useAppStore } from '@/stores/app-store'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Search, Filter, Calendar, X } from 'lucide-react'

interface SearchFilters {
  query: string
  phoneNumber: string
  dateRange: {
    from: string
    to: string
  }
  branchId: string
  conversationType: 'all' | 'feedback' | 'order' | 'support' | 'general'
}

interface SearchInterfaceProps {
  onSearch: (filters: SearchFilters) => void
  isLoading?: boolean
}

export function SearchInterface({ onSearch, isLoading }: SearchInterfaceProps) {
  const { ui, branches } = useAppStore()
  const isRTL = ui.language === 'ar'
  
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    phoneNumber: '',
    dateRange: {
      from: '',
      to: '',
    },
    branchId: '',
    conversationType: 'all',
  })
  
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSearch = () => {
    onSearch(filters)
  }

  const handleClearFilters = () => {
    setFilters({
      query: '',
      phoneNumber: '',
      dateRange: { from: '', to: '' },
      branchId: '',
      conversationType: 'all',
    })
    onSearch({
      query: '',
      phoneNumber: '',
      dateRange: { from: '', to: '' },
      branchId: '',
      conversationType: 'all',
    })
  }

  const conversationTypes = [
    { value: 'all', label: isRTL ? 'الكل' : 'All' },
    { value: 'feedback', label: isRTL ? 'ملاحظات' : 'Feedback' },
    { value: 'order', label: isRTL ? 'طلبات' : 'Orders' },
    { value: 'support', label: isRTL ? 'دعم' : 'Support' },
    { value: 'general', label: isRTL ? 'عام' : 'General' },
  ]

  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Main search */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={isRTL ? 'البحث في المحادثات...' : 'Search conversations...'}
              value={filters.query}
              onChange={(e) => setFilters({ ...filters, query: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch} disabled={isLoading}>
            <Search className="h-4 w-4 mr-2" />
            {isLoading ? (isRTL ? 'بحث...' : 'Searching...') : (isRTL ? 'بحث' : 'Search')}
          </Button>
          <Button variant="outline" onClick={() => setShowAdvanced(!showAdvanced)}>
            <Filter className="h-4 w-4 mr-2" />
            {isRTL ? 'فلاتر متقدمة' : 'Advanced'}
          </Button>
        </div>

        {/* Advanced filters */}
        {showAdvanced && (
          <div className="border-t pt-4 space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {/* Phone Number */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  {isRTL ? 'رقم الهاتف' : 'Phone Number'}
                </label>
                <input
                  type="text"
                  placeholder={isRTL ? 'مثال: +966501234567' : 'e.g. +966501234567'}
                  value={filters.phoneNumber}
                  onChange={(e) => setFilters({ ...filters, phoneNumber: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Date From */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  {isRTL ? 'من تاريخ' : 'From Date'}
                </label>
                <input
                  type="date"
                  value={filters.dateRange.from}
                  onChange={(e) => setFilters({ 
                    ...filters, 
                    dateRange: { ...filters.dateRange, from: e.target.value } 
                  })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Date To */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  {isRTL ? 'إلى تاريخ' : 'To Date'}
                </label>
                <input
                  type="date"
                  value={filters.dateRange.to}
                  onChange={(e) => setFilters({ 
                    ...filters, 
                    dateRange: { ...filters.dateRange, to: e.target.value } 
                  })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Branch */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  {isRTL ? 'الفرع' : 'Branch'}
                </label>
                <select
                  value={filters.branchId}
                  onChange={(e) => setFilters({ ...filters, branchId: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">{isRTL ? 'جميع الفروع' : 'All Branches'}</option>
                  {branches.map((branch) => (
                    <option key={branch.id} value={branch.id}>
                      {isRTL ? branch.nameAr : branch.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Conversation Type */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  {isRTL ? 'نوع المحادثة' : 'Conversation Type'}
                </label>
                <select
                  value={filters.conversationType}
                  onChange={(e) => setFilters({ 
                    ...filters, 
                    conversationType: e.target.value as SearchFilters['conversationType'] 
                  })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {conversationTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex justify-between">
              <Button variant="outline" onClick={handleClearFilters}>
                <X className="h-4 w-4 mr-2" />
                {isRTL ? 'مسح الفلاتر' : 'Clear Filters'}
              </Button>
              
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowAdvanced(false)}>
                  {isRTL ? 'إخفاء' : 'Hide'}
                </Button>
                <Button onClick={handleSearch} disabled={isLoading}>
                  {isLoading ? (isRTL ? 'بحث...' : 'Searching...') : (isRTL ? 'تطبيق الفلاتر' : 'Apply Filters')}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Active filters display */}
        {(filters.query || filters.phoneNumber || filters.dateRange.from || filters.branchId || filters.conversationType !== 'all') && (
          <div className="flex flex-wrap gap-2">
            {filters.query && (
              <Badge variant="secondary">
                {isRTL ? 'البحث:' : 'Search:'} &quot;{filters.query}&quot;
              </Badge>
            )}
            {filters.phoneNumber && (
              <Badge variant="secondary">
                {isRTL ? 'الهاتف:' : 'Phone:'} {filters.phoneNumber}
              </Badge>
            )}
            {filters.dateRange.from && (
              <Badge variant="secondary">
                {isRTL ? 'من:' : 'From:'} {filters.dateRange.from}
              </Badge>
            )}
            {filters.dateRange.to && (
              <Badge variant="secondary">
                {isRTL ? 'إلى:' : 'To:'} {filters.dateRange.to}
              </Badge>
            )}
            {filters.conversationType !== 'all' && (
              <Badge variant="secondary">
                {conversationTypes.find(t => t.value === filters.conversationType)?.label}
              </Badge>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}