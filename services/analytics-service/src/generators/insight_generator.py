"""
AI Insight Generator
Generates natural language insights from analytics data
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
import httpx
import json
import os

from ..schemas import AnalyticsMetrics


class InsightGenerator:
    """Generate AI-powered insights from feedback analytics"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3-haiku"
    
    async def generate_daily_insights(
        self,
        restaurant_id: UUID,
        target_date: date,
        metrics: AnalyticsMetrics
    ) -> Dict[str, Any]:
        """
        Generate daily insights from metrics data
        """
        context = self._prepare_context(metrics, "daily")
        
        # Generate different types of insights
        insights = {
            "summary": await self._generate_summary_insights(context),
            "key_points": await self._generate_key_points(context),
            "recommendations": await self._generate_recommendations(context),
            "alerts": await self._generate_alerts(context),
            "trends": await self._generate_trend_insights(context)
        }
        
        return insights
    
    async def generate_period_insights(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date,
        metrics_list: List[str]
    ) -> Dict[str, Any]:
        """
        Generate insights for a date range
        """
        # This would aggregate metrics over the period
        # For now, return basic structure
        return {
            "summary": "تم تحليل فترة متعددة الأيام",
            "key_points": ["نقطة رئيسية 1", "نقطة رئيسية 2"],
            "recommendations": ["توصية 1", "توصية 2"],
            "period_analysis": f"تحليل الفترة من {start_date} إلى {end_date}"
        }
    
    def _prepare_context(self, metrics: AnalyticsMetrics, period_type: str) -> Dict[str, Any]:
        """Prepare context data for AI analysis"""
        return {
            "period_type": period_type,
            "date": metrics.date.isoformat() if metrics.date else None,
            "campaigns": {
                "created": metrics.campaigns_created,
                "sent": metrics.campaigns_sent,
                "messages_sent": metrics.messages_sent,
                "response_rate": metrics.response_rate,
                "completion_rate": metrics.completion_rate
            },
            "ratings": {
                "average": metrics.average_rating,
                "distribution": metrics.rating_distribution,
                "positive_count": metrics.positive_count,
                "negative_count": metrics.negative_count,
                "neutral_count": metrics.neutral_count
            },
            "sentiment": {
                "average": metrics.average_sentiment,
                "positive_ratio": (metrics.positive_count / max(metrics.feedback_collected, 1)) * 100,
                "negative_ratio": (metrics.negative_count / max(metrics.feedback_collected, 1)) * 100
            },
            "topics": {
                "most_mentioned": metrics.topic_counts,
                "top_issues": metrics.top_issues
            },
            "performance": {
                "total_feedback": metrics.feedback_collected,
                "messages_delivered": metrics.messages_delivered
            }
        }
    
    async def _generate_summary_insights(self, context: Dict[str, Any]) -> str:
        """Generate overall summary insights"""
        prompt = f"""
        أنت محلل بيانات متخصص في تجربة العملاء للمطاعم السعودية.
        قم بتحليل البيانات التالية وإنشاء ملخص بصيغة طبيعية باللغة العربية:

        البيانات:
        {json.dumps(context, ensure_ascii=False, indent=2)}

        اكتب ملخص تحليلي يغطي:
        1. الأداء العام للحملات
        2. رضا العملاء (التقييمات والمشاعر)
        3. أهم الملاحظات الإيجابية والسلبية
        4. مقارنة سريعة بالمعايير المتوقعة

        الملخص يجب أن يكون:
        - واضح ومباشر
        - لا يتجاوز 150 كلمة
        - يستخدم الأرقام بطريقة مفهومة
        - يركز على النقاط المهمة فقط
        """
        
        response = await self._call_ai_api(prompt)
        return response.strip()
    
    async def _generate_key_points(self, context: Dict[str, Any]) -> List[str]:
        """Generate key insight points"""
        prompt = f"""
        بناءً على البيانات التالية، استخرج أهم 4-5 نقاط رئيسية:

        {json.dumps(context, ensure_ascii=False, indent=2)}

        النقاط يجب أن تكون:
        - مختصرة (جملة واحدة لكل نقطة)
        - تركز على الأرقام المهمة
        - تبرز النجاحات والتحديات
        - قابلة للتنفيذ أو مفيدة للقرار

        أرجع النتيجة كقائمة JSON من النقاط.
        مثال: ["النقطة الأولى", "النقطة الثانية"]
        """
        
        response = await self._call_ai_api(prompt)
        
        try:
            # Try to parse as JSON list
            if response.strip().startswith('['):
                return json.loads(response)
            else:
                # Fall back to splitting by lines
                return [line.strip('- ').strip() for line in response.split('\n') if line.strip()]
        except:
            return ["تم استلام البيانات وتحليلها بنجاح"]
    
    async def _generate_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        prompt = f"""
        بناءً على تحليل البيانات التالية، قدم توصيات عملية وقابلة للتطبيق:

        {json.dumps(context, ensure_ascii=False, indent=2)}

        التوصيات يجب أن تكون:
        - عملية وقابلة للتطبيق
        - مبنية على البيانات المقدمة
        - تساعد في تحسين تجربة العملاء
        - واضحة ومحددة

        أرجع 3-4 توصيات كقائمة JSON.
        مثال: ["التوصية الأولى", "التوصية الثانية"]
        """
        
        response = await self._call_ai_api(prompt)
        
        try:
            if response.strip().startswith('['):
                return json.loads(response)
            else:
                return [line.strip('- ').strip() for line in response.split('\n') if line.strip()][:4]
        except:
            return ["الاستمرار في مراقبة أداء الحملات وتحسينها"]
    
    async def _generate_alerts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for issues that need attention"""
        alerts = []
        
        # Low response rate alert
        if context["campaigns"]["response_rate"] < 20:
            alerts.append({
                "type": "warning",
                "title": "معدل استجابة منخفض",
                "message": f"معدل الاستجابة {context['campaigns']['response_rate']}% أقل من المتوقع",
                "priority": "medium"
            })
        
        # High negative feedback alert
        if context["sentiment"]["negative_ratio"] > 30:
            alerts.append({
                "type": "alert",
                "title": "زيادة في التقييمات السلبية",
                "message": f"نسبة التقييمات السلبية وصلت إلى {context['sentiment']['negative_ratio']:.1f}%",
                "priority": "high"
            })
        
        # Low average rating alert
        if context["ratings"]["average"] < 3.5:
            alerts.append({
                "type": "warning",
                "title": "انخفاض متوسط التقييم",
                "message": f"متوسط التقييم {context['ratings']['average']:.1f} يحتاج تحسين",
                "priority": "medium"
            })
        
        # Top issues alert
        top_issues = context["topics"]["top_issues"]
        if top_issues:
            most_common_issue = max(top_issues.items(), key=lambda x: x[1])
            if most_common_issue[1] >= 3:  # 3 or more complaints
                alerts.append({
                    "type": "info",
                    "title": "مشكلة متكررة",
                    "message": f"تم ذكر '{most_common_issue[0]}' {most_common_issue[1]} مرات",
                    "priority": "medium"
                })
        
        return alerts
    
    async def _generate_trend_insights(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate insights about trends (would need historical data)"""
        # This would compare with previous periods
        # For now, return basic analysis
        
        insights = {}
        
        # Response rate trend
        response_rate = context["campaigns"]["response_rate"]
        if response_rate >= 40:
            insights["response"] = "معدل استجابة ممتاز يتجاوز 40%"
        elif response_rate >= 25:
            insights["response"] = "معدل استجابة جيد ضمن المعدل الطبيعي"
        else:
            insights["response"] = "معدل استجابة منخفض يحتاج تحسين"
        
        # Rating trend
        avg_rating = context["ratings"]["average"]
        if avg_rating >= 4.5:
            insights["rating"] = "تقييمات ممتازة تدل على رضا عالي"
        elif avg_rating >= 3.5:
            insights["rating"] = "تقييمات جيدة مع إمكانية للتحسين"
        else:
            insights["rating"] = "تقييمات تحتاج اهتمام وتحسين فوري"
        
        # Sentiment trend
        negative_ratio = context["sentiment"]["negative_ratio"]
        if negative_ratio < 10:
            insights["sentiment"] = "مشاعر إيجابية عامة من العملاء"
        elif negative_ratio < 25:
            insights["sentiment"] = "مشاعر متوازنة مع بعض التحديات"
        else:
            insights["sentiment"] = "مشاعر سلبية تتطلب تدخل سريع"
        
        return insights
    
    async def _call_ai_api(self, prompt: str) -> str:
        """Call OpenRouter API for AI generation"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.openrouter_url,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return "تعذر إنشاء الرؤى الذكية حالياً"
                    
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return "تعذر إنشاء الرؤى الذكية حالياً"
    
    def _calculate_performance_score(self, context: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        scores = []
        
        # Response rate score (0-30 points)
        response_rate = context["campaigns"]["response_rate"]
        response_score = min(response_rate / 40 * 30, 30)  # 40% response rate = full score
        scores.append(response_score)
        
        # Average rating score (0-40 points)
        avg_rating = context["ratings"]["average"]
        rating_score = (avg_rating / 5.0) * 40
        scores.append(rating_score)
        
        # Sentiment score (0-30 points)
        positive_ratio = context["sentiment"]["positive_ratio"]
        negative_ratio = context["sentiment"]["negative_ratio"]
        sentiment_score = max(0, (positive_ratio - negative_ratio) / 100 * 30)
        scores.append(sentiment_score)
        
        return sum(scores)
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "ممتاز"
        elif score >= 75:
            return "جيد جداً"
        elif score >= 60:
            return "جيد"
        elif score >= 45:
            return "مقبول"
        else:
            return "يحتاج تحسين"