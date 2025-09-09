/**
 * Alert Center Component
 * Displays and manages feedback alerts that require attention
 */

"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  X,
  MessageSquare,
  Star,
  Phone,
  Eye,
  Check,
  AlertCircle
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface FeedbackAlert {
  id: string;
  restaurant_id: string;
  feedback_id?: string;
  conversation_id?: string;
  campaign_id?: string;
  rule_id: string;
  priority: 'low' | 'medium' | 'high' | 'immediate';
  title: string;
  message: string;
  details: {
    customer_phone?: string;
    rating?: number;
    sentiment_score?: number;
    message?: string;
    topics?: string[];
  };
  status: 'pending' | 'acknowledged' | 'resolved' | 'dismissed';
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  acknowledgment_notes?: string;
}

interface AlertCenterProps {
  restaurantId: string;
  onViewConversation?: (conversationId: string) => void;
  onViewFeedback?: (feedbackId: string) => void;
}

const priorityConfig = {
  immediate: {
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: AlertTriangle,
    label: 'عاجل',
    bgClass: 'bg-red-50 border-red-200'
  },
  high: {
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: AlertCircle,
    label: 'مرتفع',
    bgClass: 'bg-orange-50 border-orange-200'
  },
  medium: {
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: Clock,
    label: 'متوسط',
    bgClass: 'bg-yellow-50 border-yellow-200'
  },
  low: {
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: AlertCircle,
    label: 'منخفض',
    bgClass: 'bg-blue-50 border-blue-200'
  }
};

export default function AlertCenter({
  restaurantId,
  onViewConversation,
  onViewFeedback
}: AlertCenterProps) {
  const [alerts, setAlerts] = useState<FeedbackAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<FeedbackAlert | null>(null);
  const [acknowledgeDialog, setAcknowledgeDialog] = useState(false);
  const [acknowledgmentNotes, setAcknowledgmentNotes] = useState('');
  const [filter, setFilter] = useState<'all' | 'pending' | 'acknowledged'>('pending');
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'immediate' | 'high' | 'medium' | 'low'>('all');
  
  useEffect(() => {
    fetchAlerts();
    
    // Set up polling for real-time updates
    const interval = setInterval(fetchAlerts, 30000); // 30 seconds
    
    return () => clearInterval(interval);
  }, [restaurantId, filter, priorityFilter]);
  
  const fetchAlerts = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      params.append('restaurant_id', restaurantId);
      
      if (filter !== 'all') {
        params.append('status', filter);
      }
      
      if (priorityFilter !== 'all') {
        params.append('priority', priorityFilter);
      }
      
      // Mock data for demonstration
      const mockAlerts: FeedbackAlert[] = [
        {
          id: '1',
          restaurant_id: restaurantId,
          feedback_id: 'feedback_1',
          conversation_id: 'conv_1',
          rule_id: 'low_rating_immediate',
          priority: 'immediate',
          title: 'تقييم منخفض جداً (1 نجمة)',
          message: 'عميل أعطى تقييم نجمة واحدة فقط',
          details: {
            customer_phone: '+966501234567',
            rating: 1,
            sentiment_score: -0.8,
            message: 'الطعام كان بارد والخدمة سيئة جداً. لن أعود مرة أخرى!',
            topics: ['طعام', 'خدمة', 'شكوى']
          },
          status: 'pending',
          created_at: new Date().toISOString()
        },
        {
          id: '2',
          restaurant_id: restaurantId,
          feedback_id: 'feedback_2',
          conversation_id: 'conv_2',
          rule_id: 'food_quality_issue',
          priority: 'high',
          title: 'شكوى من جودة الطعام',
          message: 'تم ذكر مشكلة في جودة الطعام 3 مرات اليوم',
          details: {
            customer_phone: '+966502345678',
            rating: 2,
            sentiment_score: -0.6,
            message: 'البرجر كان نيء من الداخل والبطاطس باردة',
            topics: ['طعام', 'جودة', 'برجر']
          },
          status: 'pending',
          created_at: new Date(Date.now() - 15 * 60000).toISOString()
        },
        {
          id: '3',
          restaurant_id: restaurantId,
          conversation_id: 'conv_3',
          rule_id: 'service_complaint',
          priority: 'medium',
          title: 'شكوى من الخدمة',
          message: 'عميل اشتكى من بطء الخدمة',
          details: {
            customer_phone: '+966503456789',
            rating: 3,
            sentiment_score: -0.3,
            message: 'الطعام جيد لكن الانتظار كان طويل جداً',
            topics: ['خدمة', 'انتظار', 'وقت']
          },
          status: 'acknowledged',
          created_at: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
          acknowledged_at: new Date(Date.now() - 60 * 60000).toISOString(),
          acknowledged_by: 'Manager',
          acknowledgment_notes: 'تم التواصل مع فريق المطبخ لتحسين أوقات التحضير'
        }
      ];
      
      setAlerts(mockAlerts);
      
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      // Mock API call
      const response = await fetch(`/api/feedback-alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes: acknowledgmentNotes
        })
      });
      
      if (response.ok) {
        // Update local state
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { 
                ...alert, 
                status: 'acknowledged',
                acknowledged_at: new Date().toISOString(),
                acknowledgment_notes: acknowledgmentNotes
              }
            : alert
        ));
        
        setAcknowledgeDialog(false);
        setSelectedAlert(null);
        setAcknowledgmentNotes('');
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };
  
  const handleDismissAlert = async (alertId: string) => {
    try {
      // Mock API call
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'dismissed' }
          : alert
      ));
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };
  
  const openAcknowledgeDialog = (alert: FeedbackAlert) => {
    setSelectedAlert(alert);
    setAcknowledgeDialog(true);
  };
  
  const formatTimeAgo = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'الآن';
    if (diffMins < 60) return `قبل ${diffMins} دقيقة`;
    if (diffMins < 1440) return `قبل ${Math.floor(diffMins / 60)} ساعة`;
    return time.toLocaleDateString('ar-SA');
  };
  
  const filteredAlerts = alerts.filter(alert => {
    if (filter !== 'all' && alert.status !== filter) return false;
    if (priorityFilter !== 'all' && alert.priority !== priorityFilter) return false;
    return true;
  });
  
  const pendingCount = alerts.filter(a => a.status === 'pending').length;
  const immediateCount = alerts.filter(a => a.priority === 'immediate' && a.status === 'pending').length;
  
  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">جاري تحميل التنبيهات...</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">مركز التنبيهات</h2>
            <p className="text-muted-foreground">
              تنبيهات التقييمات التي تحتاج اهتمام فوري
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {immediateCount > 0 && (
              <Badge variant="destructive" className="animate-pulse">
                {immediateCount} تنبيه عاجل
              </Badge>
            )}
            
            {pendingCount > 0 && (
              <Badge variant="secondary">
                {pendingCount} تنبيه معلق
              </Badge>
            )}
          </div>
        </div>
        
        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">الحالة:</span>
                <div className="flex space-x-1">
                  {[
                    { value: 'all', label: 'الكل' },
                    { value: 'pending', label: 'معلق' },
                    { value: 'acknowledged', label: 'مقروء' }
                  ].map((option) => (
                    <Button
                      key={option.value}
                      variant={filter === option.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter(option.value as any)}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">الأولوية:</span>
                <div className="flex space-x-1">
                  {[
                    { value: 'all', label: 'الكل' },
                    { value: 'immediate', label: 'عاجل' },
                    { value: 'high', label: 'مرتفع' },
                    { value: 'medium', label: 'متوسط' },
                    { value: 'low', label: 'منخفض' }
                  ].map((option) => (
                    <Button
                      key={option.value}
                      variant={priorityFilter === option.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPriorityFilter(option.value as any)}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Alerts List */}
        <Card className="h-[700px] flex flex-col">
          <CardHeader>
            <CardTitle>
              التنبيهات ({filteredAlerts.length})
            </CardTitle>
          </CardHeader>
          
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full p-4">
              {filteredAlerts.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <p className="text-lg font-medium mb-2">لا توجد تنبيهات</p>
                  <p className="text-muted-foreground">
                    {filter === 'pending' 
                      ? 'جميع التنبيهات تم التعامل معها! 🎉'
                      : 'لا توجد تنبيهات تطابق المعايير المختارة'
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredAlerts.map((alert) => {
                    const config = priorityConfig[alert.priority];
                    const IconComponent = config.icon;
                    
                    return (
                      <Card 
                        key={alert.id}
                        className={cn(
                          'border-l-4 transition-all hover:shadow-md',
                          config.bgClass,
                          alert.status === 'pending' ? 'shadow-sm' : 'opacity-75'
                        )}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3 flex-1">
                              <div className="shrink-0 mt-1">
                                <IconComponent className={cn(
                                  'h-5 w-5',
                                  alert.priority === 'immediate' ? 'text-red-600' :
                                  alert.priority === 'high' ? 'text-orange-600' :
                                  alert.priority === 'medium' ? 'text-yellow-600' :
                                  'text-blue-600'
                                )} />
                              </div>
                              
                              <div className="flex-1 space-y-2">
                                <div className="flex items-center justify-between">
                                  <h4 className="font-medium text-right">
                                    {alert.title}
                                  </h4>
                                  
                                  <div className="flex items-center space-x-2">
                                    <Badge 
                                      className={config.color}
                                      variant="secondary"
                                    >
                                      {config.label}
                                    </Badge>
                                    
                                    {alert.status === 'acknowledged' && (
                                      <Badge className="bg-green-100 text-green-800">
                                        مقروء
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                
                                <p className="text-sm text-muted-foreground text-right">
                                  {alert.message}
                                </p>
                                
                                {/* Alert Details */}
                                {alert.details && (
                                  <div className="bg-white/80 rounded-lg p-3 space-y-2 text-sm">
                                    {alert.details.customer_phone && (
                                      <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">العميل:</span>
                                        <span className="flex items-center">
                                          <Phone className="h-3 w-3 mr-1" />
                                          {alert.details.customer_phone}
                                        </span>
                                      </div>
                                    )}
                                    
                                    {alert.details.rating && (
                                      <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">التقييم:</span>
                                        <div className="flex items-center">
                                          {Array.from({ length: 5 }, (_, i) => (
                                            <Star
                                              key={i}
                                              className={cn(
                                                'h-3 w-3',
                                                i < alert.details.rating! 
                                                  ? 'text-yellow-400 fill-yellow-400' 
                                                  : 'text-gray-300'
                                              )}
                                            />
                                          ))}
                                          <span className="mr-1">
                                            {alert.details.rating}/5
                                          </span>
                                        </div>
                                      </div>
                                    )}
                                    
                                    {alert.details.message && (
                                      <div>
                                        <span className="text-muted-foreground text-xs">الرسالة:</span>
                                        <p className="text-right mt-1 italic">
                                          &quot;{alert.details.message}&quot;
                                        </p>
                                      </div>
                                    )}
                                    
                                    {alert.details.topics && alert.details.topics.length > 0 && (
                                      <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">المواضيع:</span>
                                        <div className="flex space-x-1">
                                          {alert.details.topics.map((topic, index) => (
                                            <Badge key={index} variant="outline" className="text-xs">
                                              {topic}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Acknowledgment Info */}
                                {alert.status === 'acknowledged' && alert.acknowledgment_notes && (
                                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                    <p className="text-sm font-medium text-green-800 mb-1">
                                      تم التعامل معه:
                                    </p>
                                    <p className="text-sm text-green-700">
                                      {alert.acknowledgment_notes}
                                    </p>
                                    {alert.acknowledged_at && (
                                      <p className="text-xs text-green-600 mt-1">
                                        {formatTimeAgo(alert.acknowledged_at)}
                                      </p>
                                    )}
                                  </div>
                                )}
                                
                                <div className="flex items-center justify-between pt-2">
                                  <div className="flex space-x-2">
                                    {alert.conversation_id && (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => onViewConversation?.(alert.conversation_id!)}
                                      >
                                        <MessageSquare className="h-3 w-3 mr-1" />
                                        عرض المحادثة
                                      </Button>
                                    )}
                                    
                                    {alert.feedback_id && (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => onViewFeedback?.(alert.feedback_id!)}
                                      >
                                        <Eye className="h-3 w-3 mr-1" />
                                        عرض التقييم
                                      </Button>
                                    )}
                                  </div>
                                  
                                  <span className="text-xs text-muted-foreground">
                                    {formatTimeAgo(alert.created_at)}
                                  </span>
                                </div>
                              </div>
                            </div>
                            
                            {/* Action Buttons */}
                            <div className="flex items-start space-x-2 shrink-0 mr-4">
                              {alert.status === 'pending' && (
                                <>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => openAcknowledgeDialog(alert)}
                                  >
                                    <Check className="h-3 w-3 mr-1" />
                                    تم التعامل
                                  </Button>
                                  
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDismissAlert(alert.id)}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
      
      {/* Acknowledge Dialog */}
      <Dialog open={acknowledgeDialog} onOpenChange={setAcknowledgeDialog}>
        <DialogContent className="text-right" dir="rtl">
          <DialogHeader>
            <DialogTitle>تأكيد التعامل مع التنبيه</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              يرجى إضافة ملاحظات حول الإجراءات المتخذة للتعامل مع هذا التنبيه:
            </p>
            
            <Textarea
              placeholder="مثال: تم التواصل مع العميل والاعتذار، وتم إعطاءه خصم على الوجبة القادمة..."
              value={acknowledgmentNotes}
              onChange={(e) => setAcknowledgmentNotes(e.target.value)}
              rows={4}
            />
          </div>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setAcknowledgeDialog(false)}
            >
              إلغاء
            </Button>
            <Button 
              onClick={() => selectedAlert && handleAcknowledgeAlert(selectedAlert.id)}
              disabled={!acknowledgmentNotes.trim()}
            >
              تأكيد التعامل
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}