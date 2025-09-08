"""
Reports API endpoints
Handles report generation and delivery
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
import json

from ..processors.feedback_aggregator import FeedbackAggregator
from ..generators.insight_generator import InsightGenerator
from ..schemas import (
    DailyReportRequest,
    DailyReportResponse,
    ReportScheduleRequest,
    InsightRequest,
    AnalyticsMetrics
)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_feedback_aggregator(request: Request) -> FeedbackAggregator:
    """Dependency to get feedback aggregator"""
    return request.app.state.feedback_aggregator


def get_insight_generator(request: Request) -> InsightGenerator:
    """Dependency to get insight generator"""
    return request.app.state.insight_generator


@router.get("/daily-summary", response_model=DailyReportResponse)
async def generate_daily_summary(
    restaurant_id: UUID,
    target_date: Optional[date] = None,
    aggregator: FeedbackAggregator = Depends(get_feedback_aggregator),
    insight_gen: InsightGenerator = Depends(get_insight_generator)
):
    """
    Generate daily summary report for a restaurant
    If no date specified, uses yesterday
    """
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).date()
    
    try:
        # Aggregate feedback data
        metrics = await aggregator.aggregate_daily_metrics(
            restaurant_id,
            target_date
        )
        
        # Generate AI insights
        insights = await insight_gen.generate_daily_insights(
            restaurant_id,
            target_date,
            metrics
        )
        
        # Create report
        report = DailyReportResponse(
            restaurant_id=restaurant_id,
            report_date=target_date,
            metrics=metrics,
            insights=insights,
            generated_at=datetime.now()
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating daily report: {str(e)}"
        )


@router.post("/daily-summary")
async def create_daily_summary(
    request: DailyReportRequest,
    background_tasks: BackgroundTasks,
    aggregator: FeedbackAggregator = Depends(get_feedback_aggregator),
    insight_gen: InsightGenerator = Depends(get_insight_generator)
):
    """
    Create and optionally send daily summary report
    Can be called by Celery tasks
    """
    try:
        # Generate report
        metrics = await aggregator.aggregate_daily_metrics(
            request.restaurant_id,
            request.date
        )
        
        insights = await insight_gen.generate_daily_insights(
            request.restaurant_id,
            request.date,
            metrics
        )
        
        report_data = {
            "restaurant_id": str(request.restaurant_id),
            "report_date": request.date.isoformat(),
            "metrics": metrics.dict(),
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
        # Store report in database
        await aggregator.store_report(request.restaurant_id, request.date, report_data)
        
        # Send report if requested
        if request.send_report:
            background_tasks.add_task(
                _send_daily_report,
                request.restaurant_id,
                report_data,
                request.delivery_channels
            )
        
        return {
            "success": True,
            "report_id": f"{request.restaurant_id}_{request.date.isoformat()}",
            "message": "Report generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating daily report: {str(e)}"
        )


@router.post("/schedule")
async def schedule_report(request: ReportScheduleRequest):
    """
    Schedule recurring report generation
    """
    try:
        # This would integrate with Celery Beat to schedule periodic reports
        # For now, return success with schedule details
        
        schedule_data = {
            "restaurant_id": str(request.restaurant_id),
            "report_type": request.report_type,
            "frequency": request.frequency,
            "time": request.time.isoformat() if request.time else None,
            "channels": request.channels,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Store schedule configuration (implementation needed)
        # await store_report_schedule(schedule_data)
        
        return {
            "success": True,
            "schedule_id": f"schedule_{request.restaurant_id}_{request.report_type}",
            "message": "Report schedule created successfully",
            "next_run": _calculate_next_run_time(request.frequency, request.time)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scheduling report: {str(e)}"
        )


@router.get("/insights")
async def get_insights(
    restaurant_id: UUID,
    date_from: date,
    date_to: date,
    metrics: Optional[List[str]] = None,
    insight_gen: InsightGenerator = Depends(get_insight_generator)
):
    """
    Get AI-generated insights for a date range
    """
    try:
        insights = await insight_gen.generate_period_insights(
            restaurant_id,
            date_from,
            date_to,
            metrics or ["response_rate", "sentiment", "ratings"]
        )
        
        return {
            "restaurant_id": str(restaurant_id),
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating insights: {str(e)}"
        )


@router.get("/trends/{restaurant_id}")
async def get_feedback_trends(
    restaurant_id: UUID,
    days: int = 30,
    aggregator: FeedbackAggregator = Depends(get_feedback_aggregator)
):
    """
    Get feedback trends over time
    """
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends = await aggregator.get_trends(
            restaurant_id,
            start_date,
            end_date
        )
        
        return {
            "restaurant_id": str(restaurant_id),
            "period": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "days": days
            },
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trends: {str(e)}"
        )


@router.get("/comparison/{restaurant_id}")
async def get_period_comparison(
    restaurant_id: UUID,
    current_start: date,
    current_end: date,
    previous_start: date,
    previous_end: date,
    aggregator: FeedbackAggregator = Depends(get_feedback_aggregator)
):
    """
    Compare metrics between two periods
    """
    try:
        current_metrics = await aggregator.aggregate_period_metrics(
            restaurant_id,
            current_start,
            current_end
        )
        
        previous_metrics = await aggregator.aggregate_period_metrics(
            restaurant_id,
            previous_start,
            previous_end
        )
        
        # Calculate changes
        changes = _calculate_metric_changes(current_metrics, previous_metrics)
        
        return {
            "restaurant_id": str(restaurant_id),
            "current_period": {
                "from": current_start.isoformat(),
                "to": current_end.isoformat(),
                "metrics": current_metrics.dict()
            },
            "previous_period": {
                "from": previous_start.isoformat(),
                "to": previous_end.isoformat(),
                "metrics": previous_metrics.dict()
            },
            "changes": changes,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating comparison: {str(e)}"
        )


async def _send_daily_report(
    restaurant_id: UUID,
    report_data: Dict[str, Any],
    channels: List[str]
):
    """
    Send daily report via specified channels
    Background task
    """
    try:
        for channel in channels:
            if channel == "whatsapp":
                await _send_whatsapp_report(restaurant_id, report_data)
            elif channel == "email":
                await _send_email_report(restaurant_id, report_data)
            # Add more channels as needed
                
    except Exception as e:
        print(f"Error sending report: {e}")


async def _send_whatsapp_report(restaurant_id: UUID, report_data: Dict[str, Any]):
    """Send report via WhatsApp"""
    # Get restaurant owner's phone number from database
    # Format report as WhatsApp message
    # Send via WhatsApp gateway service
    
    import httpx
    
    # This is a simplified implementation
    report_message = _format_report_for_whatsapp(report_data)
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://whatsapp-gateway:8002/api/messages/send",
            json={
                "to": "+966501234567",  # Get from restaurant settings
                "type": "text",
                "text": {"body": report_message}
            }
        )


async def _send_email_report(restaurant_id: UUID, report_data: Dict[str, Any]):
    """Send report via email"""
    # Implementation for email delivery
    pass


def _format_report_for_whatsapp(report_data: Dict[str, Any]) -> str:
    """Format report data for WhatsApp message"""
    metrics = report_data["metrics"]
    insights = report_data["insights"]
    date_str = report_data["report_date"]
    
    message = f"""📊 تقرير يومي - {date_str}

📈 الإحصائيات:
• طلبات التقييم المرسلة: {metrics.get('campaigns_sent', 0)}
• معدل الاستجابة: {metrics.get('response_rate', 0):.1f}%
• متوسط التقييم: {metrics.get('average_rating', 0):.1f}/5
• التقييمات الإيجابية: {metrics.get('positive_count', 0)}
• التقييمات السلبية: {metrics.get('negative_count', 0)}

🤖 رؤى ذكية:
{chr(10).join(f'• {insight}' for insight in insights.get('key_points', []))}

{insights.get('recommendation', 'استمروا في العمل الممتاز! 👏')}
"""
    
    return message


def _calculate_next_run_time(frequency: str, time: Optional[datetime]) -> str:
    """Calculate next scheduled run time"""
    now = datetime.now()
    
    if frequency == "daily":
        if time:
            next_run = now.replace(
                hour=time.hour,
                minute=time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(days=1)
        else:
            next_run = now + timedelta(days=1)
    elif frequency == "weekly":
        next_run = now + timedelta(days=7)
    else:  # monthly
        next_run = now + timedelta(days=30)
    
    return next_run.isoformat()


def _calculate_metric_changes(
    current: AnalyticsMetrics,
    previous: AnalyticsMetrics
) -> Dict[str, Dict[str, Any]]:
    """Calculate percentage changes between metric periods"""
    changes = {}
    
    metrics_to_compare = [
        ("campaigns_sent", "طلبات التقييم"),
        ("responses_received", "الاستجابات"),
        ("response_rate", "معدل الاستجابة"),
        ("average_rating", "متوسط التقييم"),
        ("positive_count", "التقييمات الإيجابية"),
        ("negative_count", "التقييمات السلبية")
    ]
    
    for metric_key, metric_name in metrics_to_compare:
        current_value = getattr(current, metric_key, 0)
        previous_value = getattr(previous, metric_key, 0)
        
        if previous_value > 0:
            change_pct = ((current_value - previous_value) / previous_value) * 100
        else:
            change_pct = 100.0 if current_value > 0 else 0.0
        
        changes[metric_key] = {
            "name": metric_name,
            "current": current_value,
            "previous": previous_value,
            "change_percent": round(change_pct, 1),
            "trend": "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"
        }
    
    return changes