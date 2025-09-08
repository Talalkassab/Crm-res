/**
 * Campaign List Component
 * Displays and manages feedback campaigns
 */

"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Calendar,
  Users,
  MessageSquare,
  TrendingUp,
  Play,
  Pause,
  MoreVertical,
  Search,
  Filter,
  Plus
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'scheduled' | 'active' | 'completed' | 'cancelled';
  created_at: string;
  scheduled_start?: string;
  scheduled_end?: string;
  recipient_count?: number;
  metrics?: {
    messages_sent: number;
    responses_received: number;
    response_rate: number;
    average_rating: number;
    completion_rate: number;
  };
}

interface CampaignListProps {
  restaurantId: string;
  onCreateNew?: () => void;
  onViewCampaign?: (campaignId: string) => void;
  onEditCampaign?: (campaignId: string) => void;
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  scheduled: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  completed: 'bg-purple-100 text-purple-800',
  cancelled: 'bg-red-100 text-red-800',
};

const statusLabels = {
  draft: 'مسودة',
  scheduled: 'مجدولة',
  active: 'نشطة',
  completed: 'مكتملة',
  cancelled: 'ملغية',
};

export default function CampaignList({
  restaurantId,
  onCreateNew,
  onViewCampaign,
  onEditCampaign
}: CampaignListProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'created_at' | 'name' | 'response_rate'>('created_at');
  
  useEffect(() => {
    fetchCampaigns();
  }, [restaurantId, statusFilter]);
  
  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      params.append('restaurant_id', restaurantId);
      params.append('limit', '50');
      
      const response = await fetch(`/api/feedback-campaigns?${params}`);
      
      if (!response.ok) {
        throw new Error('فشل في تحميل الحملات');
      }
      
      const data = await response.json();
      setCampaigns(data);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ غير متوقع');
    } finally {
      setLoading(false);
    }
  };
  
  const handleScheduleCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`/api/feedback-campaigns/${campaignId}/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: new Date().toISOString(),
          end_time: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
        }),
      });
      
      if (response.ok) {
        fetchCampaigns(); // Refresh list
      }
    } catch (err) {
      console.error('Failed to schedule campaign:', err);
    }
  };
  
  const filteredAndSortedCampaigns = campaigns
    .filter(campaign => {
      const matchesSearch = searchTerm === '' || 
        campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        campaign.description?.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesSearch;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name, 'ar');
        case 'response_rate':
          return (b.metrics?.response_rate || 0) - (a.metrics?.response_rate || 0);
        default: // created_at
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">جاري تحميل الحملات...</p>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">حملات التقييم</h2>
        <Button onClick={onCreateNew} className="flex items-center">
          <Plus className="h-4 w-4 mr-2" />
          إنشاء حملة جديدة
        </Button>
      </div>
      
      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="البحث في الحملات..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 text-right"
              />
            </div>
            
            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الحالات</SelectItem>
                <SelectItem value="draft">مسودة</SelectItem>
                <SelectItem value="scheduled">مجدولة</SelectItem>
                <SelectItem value="active">نشطة</SelectItem>
                <SelectItem value="completed">مكتملة</SelectItem>
                <SelectItem value="cancelled">ملغية</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Sort By */}
            <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_at">تاريخ الإنشاء</SelectItem>
                <SelectItem value="name">الاسم</SelectItem>
                <SelectItem value="response_rate">معدل الاستجابة</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      
      {/* Campaign Grid */}
      {filteredAndSortedCampaigns.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">لا توجد حملات</h3>
            <p className="text-muted-foreground mb-4">
              {searchTerm || statusFilter !== 'all' 
                ? 'لم يتم العثور على حملات تطابق معايير البحث'
                : 'ابدأ بإنشاء أول حملة تقييم'
              }
            </p>
            {(!searchTerm && statusFilter === 'all') && (
              <Button onClick={onCreateNew}>إنشاء حملة جديدة</Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredAndSortedCampaigns.map((campaign) => (
            <Card key={campaign.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-1 text-right">
                      {campaign.name}
                    </CardTitle>
                    <Badge 
                      className={`${statusColors[campaign.status]} text-xs`}
                      variant="secondary"
                    >
                      {statusLabels[campaign.status]}
                    </Badge>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem 
                        onClick={() => onViewCampaign?.(campaign.id)}
                      >
                        عرض التفاصيل
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onEditCampaign?.(campaign.id)}
                      >
                        تعديل
                      </DropdownMenuItem>
                      {campaign.status === 'draft' && (
                        <DropdownMenuItem 
                          onClick={() => handleScheduleCampaign(campaign.id)}
                        >
                          <Play className="h-4 w-4 mr-2" />
                          بدء الحملة
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                
                {campaign.description && (
                  <p className="text-sm text-muted-foreground text-right mt-2">
                    {campaign.description}
                  </p>
                )}
              </CardHeader>
              
              <CardContent className="pt-0">
                <div className="space-y-3">
                  {/* Basic Stats */}
                  <div className="flex justify-between text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <Users className="h-4 w-4 mr-1" />
                      <span>{campaign.recipient_count || 0} عميل</span>
                    </div>
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="h-4 w-4 mr-1" />
                      <span>{formatDate(campaign.created_at)}</span>
                    </div>
                  </div>
                  
                  {/* Performance Metrics */}
                  {campaign.metrics && (
                    <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">رسائل مرسلة:</span>
                        <span className="font-medium">{campaign.metrics.messages_sent}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">معدل الاستجابة:</span>
                        <span className="font-medium">
                          {campaign.metrics.response_rate.toFixed(1)}%
                        </span>
                      </div>
                      {campaign.metrics.average_rating > 0 && (
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">متوسط التقييم:</span>
                          <span className="font-medium">
                            {campaign.metrics.average_rating.toFixed(1)}/5
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Scheduled Times */}
                  {(campaign.scheduled_start || campaign.scheduled_end) && (
                    <div className="text-xs text-muted-foreground space-y-1">
                      {campaign.scheduled_start && (
                        <div>البداية: {formatDate(campaign.scheduled_start)}</div>
                      )}
                      {campaign.scheduled_end && (
                        <div>النهاية: {formatDate(campaign.scheduled_end)}</div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}