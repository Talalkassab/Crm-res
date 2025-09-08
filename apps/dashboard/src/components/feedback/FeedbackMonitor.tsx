/**
 * Real-time Feedback Monitor
 * Shows live conversations and feedback as they come in
 */

"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { 
  MessageCircle, 
  Star, 
  Clock, 
  Phone,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FeedbackMessage {
  id: string;
  customer_phone: string;
  customer_name?: string;
  message: string;
  rating?: number;
  sentiment_score?: number;
  timestamp: string;
  campaign_name?: string;
  status: 'received' | 'processing' | 'analyzed';
  conversation_id: string;
}

interface LiveStats {
  active_conversations: number;
  pending_responses: number;
  today_feedback: number;
  avg_rating: number;
  sentiment_trend: 'up' | 'down' | 'stable';
}

interface FeedbackMonitorProps {
  restaurantId: string;
  onViewConversation?: (conversationId: string) => void;
}

const sentimentColors = {
  positive: 'text-green-600 bg-green-50',
  neutral: 'text-yellow-600 bg-yellow-50',
  negative: 'text-red-600 bg-red-50',
};

const getSentimentType = (score?: number): 'positive' | 'neutral' | 'negative' => {
  if (!score) return 'neutral';
  if (score > 0.3) return 'positive';
  if (score < -0.3) return 'negative';
  return 'neutral';
};

const formatPhoneNumber = (phone: string): string => {
  // Format +966501234567 to +966 50 123 4567
  if (phone.startsWith('+966')) {
    const number = phone.slice(4);
    if (number.length === 9) {
      return `+966 ${number.slice(0, 2)} ${number.slice(2, 5)} ${number.slice(5)}`;
    }
  }
  return phone;
};

export default function FeedbackMonitor({
  restaurantId,
  onViewConversation
}: FeedbackMonitorProps) {
  const [liveStats, setLiveStats] = useState<LiveStats>({
    active_conversations: 0,
    pending_responses: 0,
    today_feedback: 0,
    avg_rating: 0,
    sentiment_trend: 'stable'
  });
  
  const [recentFeedback, setRecentFeedback] = useState<FeedbackMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    // Initialize WebSocket connection for real-time updates
    connectWebSocket();
    
    // Fetch initial data
    fetchLiveStats();
    fetchRecentFeedback();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [restaurantId]);
  
  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (autoScroll && scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [recentFeedback, autoScroll]);
  
  const connectWebSocket = () => {
    // In production, use Supabase Realtime
    // For now, simulate with periodic polling
    const interval = setInterval(() => {
      fetchLiveStats();
      fetchRecentFeedback();
    }, 10000); // Update every 10 seconds
    
    setIsConnected(true);
    
    return () => {
      clearInterval(interval);
      setIsConnected(false);
    };
  };
  
  const fetchLiveStats = async () => {
    try {
      // Simulate API call - replace with actual endpoint
      const mockStats: LiveStats = {
        active_conversations: Math.floor(Math.random() * 10) + 1,
        pending_responses: Math.floor(Math.random() * 5),
        today_feedback: Math.floor(Math.random() * 50) + 10,
        avg_rating: Math.random() * 2 + 3, // 3-5 range
        sentiment_trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any
      };
      
      setLiveStats(mockStats);
    } catch (error) {
      console.error('Failed to fetch live stats:', error);
    }
  };
  
  const fetchRecentFeedback = async () => {
    try {
      // Simulate API call - replace with actual endpoint
      const mockFeedback: FeedbackMessage[] = [
        {
          id: '1',
          customer_phone: '+966501234567',
          customer_name: 'أحمد محمد',
          message: 'الطعام كان ممتاز والخدمة سريعة جداً، شكراً لكم!',
          rating: 5,
          sentiment_score: 0.8,
          timestamp: new Date().toISOString(),
          campaign_name: 'حملة يناير',
          status: 'analyzed',
          conversation_id: 'conv_1'
        },
        {
          id: '2',
          customer_phone: '+966502345678',
          message: 'الطعام جيد لكن الانتظار كان طويل قليلاً',
          rating: 3,
          sentiment_score: 0.1,
          timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
          campaign_name: 'حملة يناير',
          status: 'analyzed',
          conversation_id: 'conv_2'
        }
      ];
      
      setRecentFeedback(prev => {
        // Merge new feedback with existing, avoiding duplicates
        const existing = new Set(prev.map(f => f.id));
        const newFeedback = mockFeedback.filter(f => !existing.has(f.id));
        return [...newFeedback, ...prev].slice(0, 50); // Keep last 50
      });
    } catch (error) {
      console.error('Failed to fetch recent feedback:', error);
    }
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
  
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={cn(
          'h-3 w-3',
          i < rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'
        )}
      />
    ));
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">مراقب التقييمات المباشر</h2>
          <p className="text-muted-foreground">
            متابعة التقييمات والمحادثات في الوقت الفعلي
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={cn(
            'flex items-center px-3 py-1 rounded-full text-sm',
            isConnected 
              ? 'bg-green-100 text-green-700' 
              : 'bg-red-100 text-red-700'
          )}>
            <div className={cn(
              'w-2 h-2 rounded-full mr-2',
              isConnected ? 'bg-green-500' : 'bg-red-500'
            )} />
            {isConnected ? 'متصل' : 'غير متصل'}
          </div>
        </div>
      </div>
      
      {/* Live Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  محادثات نشطة
                </p>
                <p className="text-2xl font-bold">{liveStats.active_conversations}</p>
              </div>
              <MessageCircle className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  في انتظار الرد
                </p>
                <p className="text-2xl font-bold">{liveStats.pending_responses}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  تقييمات اليوم
                </p>
                <p className="text-2xl font-bold">{liveStats.today_feedback}</p>
              </div>
              <Star className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  متوسط التقييم
                </p>
                <div className="flex items-center space-x-1">
                  <p className="text-2xl font-bold">
                    {liveStats.avg_rating.toFixed(1)}
                  </p>
                  {liveStats.sentiment_trend === 'up' && (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  )}
                  {liveStats.sentiment_trend === 'down' && (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  {liveStats.sentiment_trend === 'stable' && (
                    <Minus className="h-4 w-4 text-gray-600" />
                  )}
                </div>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Recent Feedback Feed */}
      <Card className="h-[600px] flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle>التقييمات الحديثة</CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoScroll(!autoScroll)}
              >
                {autoScroll ? 'إيقاف التمرير التلقائي' : 'تفعيل التمرير التلقائي'}
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-hidden p-0">
          <ScrollArea ref={scrollAreaRef} className="h-full p-4">
            <div className="space-y-4">
              {recentFeedback.length === 0 ? (
                <div className="text-center py-12">
                  <MessageCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    لا توجد تقييمات حديثة
                  </p>
                </div>
              ) : (
                recentFeedback.map((feedback) => {
                  const sentimentType = getSentimentType(feedback.sentiment_score);
                  
                  return (
                    <div
                      key={feedback.id}
                      className="flex space-x-3 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                    >
                      <Avatar className="shrink-0">
                        <AvatarFallback>
                          <Phone className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 space-y-2">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-sm">
                              {feedback.customer_name || formatPhoneNumber(feedback.customer_phone)}
                            </p>
                            <div className="flex items-center space-x-2 mt-1">
                              {feedback.campaign_name && (
                                <Badge variant="secondary" className="text-xs">
                                  {feedback.campaign_name}
                                </Badge>
                              )}
                              <span className="text-xs text-muted-foreground">
                                {formatTimeAgo(feedback.timestamp)}
                              </span>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {feedback.rating && (
                              <div className="flex items-center space-x-1">
                                {renderStars(feedback.rating)}
                              </div>
                            )}
                            
                            <Badge 
                              className={cn('text-xs', sentimentColors[sentimentType])}
                              variant="secondary"
                            >
                              {sentimentType === 'positive' && <CheckCircle className="h-3 w-3 mr-1" />}
                              {sentimentType === 'negative' && <AlertTriangle className="h-3 w-3 mr-1" />}
                              {sentimentType === 'neutral' && <Minus className="h-3 w-3 mr-1" />}
                              {sentimentType === 'positive' ? 'إيجابي' : 
                               sentimentType === 'negative' ? 'سلبي' : 'محايد'}
                            </Badge>
                          </div>
                        </div>
                        
                        <p className="text-sm text-right leading-relaxed">
                          {feedback.message}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onViewConversation?.(feedback.conversation_id)}
                            className="text-xs"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            عرض المحادثة
                          </Button>
                          
                          <div className="flex items-center space-x-2">
                            {feedback.status === 'processing' && (
                              <div className="flex items-center text-xs text-muted-foreground">
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary mr-1"></div>
                                جاري التحليل...
                              </div>
                            )}
                            
                            {feedback.sentiment_score && (
                              <span className="text-xs text-muted-foreground">
                                درجة المشاعر: {feedback.sentiment_score.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}