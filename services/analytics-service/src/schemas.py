"""
Analytics Service Schemas
Pydantic models for the analytics service
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, date, time
from uuid import UUID


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class AnalyticsMetrics(BaseSchema):
    """Daily analytics metrics"""
    date: Optional[date] = None
    campaigns_created: int = 0
    campaigns_sent: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    responses_received: int = 0
    response_rate: float = 0.0
    feedback_collected: int = 0
    average_rating: float = 0.0
    average_sentiment: float = 0.0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    rating_distribution: Dict[str, int] = Field(default_factory=dict)
    topic_counts: Dict[str, int] = Field(default_factory=dict)
    top_issues: Dict[str, int] = Field(default_factory=dict)
    completion_rate: float = 0.0


class DailyReportRequest(BaseSchema):
    """Request for daily report generation"""
    restaurant_id: UUID
    date: date
    send_report: bool = False
    delivery_channels: List[str] = Field(default_factory=lambda: ["whatsapp"])


class DailyReportResponse(BaseSchema):
    """Daily report response"""
    restaurant_id: UUID
    report_date: date
    metrics: AnalyticsMetrics
    insights: Dict[str, Any]
    generated_at: datetime


class ReportScheduleRequest(BaseSchema):
    """Request to schedule recurring reports"""
    restaurant_id: UUID
    report_type: str = "daily_summary"
    frequency: str = Field(..., regex="^(daily|weekly|monthly)$")
    time: Optional[time] = None
    channels: List[str] = Field(default_factory=lambda: ["whatsapp"])
    timezone: str = "Asia/Riyadh"


class InsightRequest(BaseSchema):
    """Request for AI insights"""
    restaurant_id: UUID
    date_from: date
    date_to: date
    metrics: Optional[List[str]] = None
    include_recommendations: bool = True


class AlertData(BaseSchema):
    """Alert information"""
    type: str  # warning, alert, info
    title: str
    message: str
    priority: str  # low, medium, high, immediate
    created_at: datetime = Field(default_factory=datetime.now)


class TrendData(BaseSchema):
    """Trend analysis data"""
    date: date
    campaigns_sent: int
    response_rate: float
    average_rating: float
    positive_count: int
    negative_count: int


class TopicTrend(BaseSchema):
    """Topic trend over time"""
    topic: str
    daily_data: List[Dict[str, Any]]
    trend_direction: str  # up, down, stable
    change_percent: float


class ComparisonMetrics(BaseSchema):
    """Metrics comparison between periods"""
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    changes: Dict[str, Dict[str, Any]]
    generated_at: datetime


class FeedbackInsights(BaseSchema):
    """AI-generated insights from feedback"""
    summary: str
    key_points: List[str]
    recommendations: List[str]
    alerts: List[AlertData]
    trends: Dict[str, str]
    performance_score: Optional[float] = None
    performance_grade: Optional[str] = None


class ReportDeliveryStatus(BaseSchema):
    """Status of report delivery"""
    report_id: str
    restaurant_id: UUID
    channels: List[str]
    delivery_status: Dict[str, str]  # channel -> status
    sent_at: Optional[datetime] = None
    error_messages: Dict[str, str] = Field(default_factory=dict)


class AnalyticsReport(BaseSchema):
    """Stored analytics report"""
    id: Optional[str] = None
    restaurant_id: UUID
    report_date: date
    report_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None


class CampaignPerformance(BaseSchema):
    """Campaign performance metrics"""
    campaign_id: UUID
    campaign_name: str
    created_at: datetime
    total_recipients: int
    messages_sent: int
    responses_received: int
    response_rate: float
    average_rating: Optional[float] = None
    positive_feedback: int = 0
    negative_feedback: int = 0
    completion_rate: float = 0.0


class RestaurantInsights(BaseSchema):
    """Restaurant-specific insights"""
    restaurant_id: UUID
    period: Dict[str, str]  # from, to dates
    overall_performance: Dict[str, Any]
    top_strengths: List[str]
    improvement_areas: List[str]
    customer_satisfaction_trend: str
    recommendation_score: Optional[float] = None
    benchmark_comparison: Optional[Dict[str, Any]] = None


class FeedbackAnalysis(BaseSchema):
    """Detailed feedback analysis"""
    total_feedback: int
    rating_breakdown: Dict[str, int]  # "1": count, "2": count, etc.
    sentiment_analysis: Dict[str, Any]
    topic_analysis: Dict[str, int]
    common_complaints: List[Dict[str, Any]]
    positive_highlights: List[str]
    customer_suggestions: List[str]


class TimeSeriesData(BaseSchema):
    """Time series data for charts"""
    labels: List[str]  # dates or time periods
    datasets: List[Dict[str, Any]]  # chart.js compatible format


class ExportRequest(BaseSchema):
    """Request for data export"""
    restaurant_id: UUID
    date_from: date
    date_to: date
    format: str = Field("csv", regex="^(csv|xlsx|pdf)$")
    include_raw_data: bool = False
    include_insights: bool = True


class BenchmarkData(BaseSchema):
    """Industry benchmark data"""
    industry_avg_rating: float
    industry_response_rate: float
    industry_sentiment_score: float
    restaurant_percentile: Dict[str, float]  # metric -> percentile
    comparison_insights: List[str]


class RealTimeMetrics(BaseSchema):
    """Real-time dashboard metrics"""
    active_campaigns: int
    pending_responses: int
    today_feedback: int
    live_sentiment: float
    current_alerts: List[AlertData]
    last_updated: datetime


class NotificationPreferences(BaseSchema):
    """User notification preferences"""
    restaurant_id: UUID
    user_id: UUID
    email_enabled: bool = True
    whatsapp_enabled: bool = True
    push_enabled: bool = True
    alert_threshold: str = "medium"  # low, medium, high
    report_frequency: str = "daily"
    quiet_hours: Optional[Dict[str, str]] = None  # start_time, end_time