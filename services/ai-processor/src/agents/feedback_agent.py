"""
Feedback Collection Agent
Handles adaptive conversation flows for feedback collection
"""

from typing import Dict, List, Any, Optional, Tuple
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from datetime import datetime
import json

from ..services.llm_service import LLMService
from ..utils.arabic_utils import ArabicTextProcessor
from ..models.conversation import FeedbackConversation
from ..prompts.feedback_templates import FeedbackPrompts


class FeedbackAgent:
    """Agent specialized in collecting customer feedback through adaptive conversation"""
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.arabic_processor = ArabicTextProcessor()
        self.prompts = FeedbackPrompts()
        self.memory_window = 10  # Keep last 10 messages
        
    async def initiate_feedback_request(
        self,
        conversation_id: str,
        customer_phone: str,
        visit_timestamp: datetime,
        template: str = "default"
    ) -> Dict[str, Any]:
        """
        Start feedback collection conversation
        Returns initial message to send to customer
        """
        # Initialize conversation memory
        memory = ConversationBufferWindowMemory(
            k=self.memory_window,
            return_messages=True,
            input_key="customer_input",
            output_key="ai_response"
        )
        
        # Get template-specific greeting
        greeting_prompt = self.prompts.get_initial_greeting(template)
        
        # Personalize with visit info
        time_since_visit = self._calculate_time_since_visit(visit_timestamp)
        
        initial_message = await self._generate_personalized_greeting(
            greeting_prompt,
            time_since_visit,
            customer_phone
        )
        
        # Store conversation context
        conversation = FeedbackConversation(
            id=conversation_id,
            customer_phone=customer_phone,
            visit_timestamp=visit_timestamp,
            stage="greeting",
            template=template,
            memory=memory,
            context={
                "time_since_visit": time_since_visit,
                "ratings_collected": {},
                "topics_discussed": [],
                "sentiment_scores": []
            }
        )
        
        return {
            "message": initial_message,
            "conversation": conversation,
            "next_action": "await_initial_response"
        }
    
    async def process_customer_response(
        self,
        conversation: FeedbackConversation,
        customer_message: str
    ) -> Dict[str, Any]:
        """
        Process customer response and determine next step in conversation flow
        """
        # Add to memory
        conversation.memory.chat_memory.add_user_message(customer_message)
        
        # Analyze customer message
        analysis = await self._analyze_customer_message(
            customer_message,
            conversation.context
        )
        
        # Update conversation context
        conversation.context.update({
            "last_sentiment": analysis["sentiment_score"],
            "detected_topics": analysis["topics"],
            "has_rating": analysis["has_rating"]
        })
        
        # Determine conversation flow based on current stage and response
        next_step = await self._determine_next_step(conversation, analysis)
        
        # Generate appropriate response
        response = await self._generate_response(conversation, analysis, next_step)
        
        # Update conversation state
        conversation.stage = next_step["stage"]
        conversation.context["ratings_collected"].update(next_step.get("ratings", {}))
        conversation.memory.chat_memory.add_ai_message(response["message"])
        
        return {
            "message": response["message"],
            "conversation": conversation,
            "next_action": next_step["action"],
            "analysis": analysis,
            "should_continue": next_step["continue"],
            "feedback_complete": next_step.get("complete", False)
        }
    
    async def _analyze_customer_message(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze customer message for sentiment, rating, and topics"""
        
        analysis_prompt = self.prompts.get_message_analysis_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", analysis_prompt),
            ("human", f"""
            تحليل هذه الرسالة من العميل:
            الرسالة: {message}
            
            سياق المحادثة السابق: {json.dumps(context, ensure_ascii=False)}
            
            قم بإرجاع JSON مع:
            - sentiment_score: رقم بين -1 و 1
            - topics: قائمة بالمواضيع المذكورة
            - has_rating: هل يحتوي على تقييم رقمي؟
            - extracted_rating: التقييم إن وجد (1-5)
            - confidence: مستوى الثقة (0-1)
            - key_phrases: العبارات الرئيسية
            """)
        ])
        
        chain = prompt | self.llm.get_chain() | self._parse_analysis_output
        
        result = await chain.ainvoke({
            "message": message,
            "context": context
        })
        
        return result
    
    async def _determine_next_step(
        self,
        conversation: FeedbackConversation,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine next step in conversation flow based on current state and analysis"""
        
        current_stage = conversation.stage
        sentiment = analysis["sentiment_score"]
        has_rating = analysis["has_rating"]
        rating = analysis.get("extracted_rating")
        
        # Stage transition logic
        if current_stage == "greeting":
            if has_rating:
                # Customer provided rating in first response
                if rating <= 2:
                    return {
                        "stage": "probing_issues",
                        "action": "ask_specific_problems",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
                elif rating >= 4:
                    return {
                        "stage": "celebrating_positive",
                        "action": "thank_and_ask_details",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
                else:  # rating == 3
                    return {
                        "stage": "understanding_neutral",
                        "action": "ask_improvement_areas",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
            else:
                # No rating yet, ask for it
                return {
                    "stage": "requesting_rating",
                    "action": "ask_for_rating",
                    "continue": True
                }
        
        elif current_stage == "requesting_rating":
            if has_rating:
                # Same logic as greeting with rating
                if rating <= 2:
                    return {
                        "stage": "probing_issues",
                        "action": "ask_specific_problems",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
                elif rating >= 4:
                    return {
                        "stage": "celebrating_positive",
                        "action": "thank_and_ask_details",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
                else:
                    return {
                        "stage": "understanding_neutral",
                        "action": "ask_improvement_areas",
                        "continue": True,
                        "ratings": {"overall": rating}
                    }
            else:
                # Still no rating, try again
                return {
                    "stage": "requesting_rating",
                    "action": "ask_for_rating_again",
                    "continue": True
                }
        
        elif current_stage in ["probing_issues", "understanding_neutral"]:
            # Check if we have enough detail
            message_count = len(conversation.memory.chat_memory.messages)
            if message_count >= 6 or self._has_sufficient_detail(analysis, conversation.context):
                return {
                    "stage": "wrapping_up",
                    "action": "thank_and_apologize",
                    "continue": False,
                    "complete": True
                }
            else:
                return {
                    "stage": current_stage,
                    "action": "ask_follow_up",
                    "continue": True
                }
        
        elif current_stage == "celebrating_positive":
            # For positive feedback, keep it shorter
            message_count = len(conversation.memory.chat_memory.messages)
            if message_count >= 4:
                return {
                    "stage": "wrapping_up",
                    "action": "thank_customer",
                    "continue": False,
                    "complete": True
                }
            else:
                return {
                    "stage": "celebrating_positive",
                    "action": "ask_what_they_loved",
                    "continue": True
                }
        
        elif current_stage == "wrapping_up":
            return {
                "stage": "complete",
                "action": "conversation_complete",
                "continue": False,
                "complete": True
            }
        
        # Default fallback
        return {
            "stage": "wrapping_up",
            "action": "end_conversation",
            "continue": False,
            "complete": True
        }
    
    async def _generate_response(
        self,
        conversation: FeedbackConversation,
        analysis: Dict[str, Any],
        next_step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate appropriate response based on conversation state"""
        
        stage = next_step["stage"]
        action = next_step["action"]
        sentiment = analysis["sentiment_score"]
        rating = conversation.context.get("ratings_collected", {}).get("overall")
        
        # Get stage-specific prompt
        response_prompt = self.prompts.get_response_prompt(stage, action)
        
        # Build context for generation
        context = {
            "conversation_history": self._format_conversation_history(conversation),
            "customer_sentiment": sentiment,
            "customer_rating": rating,
            "stage": stage,
            "action": action,
            "topics_mentioned": analysis.get("topics", []),
            "visit_info": conversation.context.get("time_since_visit", "")
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", response_prompt),
            ("human", f"""
            قم بإنشاء رد مناسب بناءً على:
            السياق: {json.dumps(context, ensure_ascii=False)}
            آخر رسالة من العميل: {analysis.get('original_message', '')}
            المرحلة الحالية: {stage}
            الإجراء المطلوب: {action}
            
            الرد يجب أن يكون:
            - طبيعي ومتدفق
            - مناسب للمشاعر والتقييم
            - يحافظ على الطابع الودود
            - مختصر وواضح
            """)
        ])
        
        chain = prompt | self.llm.get_chain()
        
        response = await chain.ainvoke(context)
        
        return {
            "message": response.content,
            "tone": self._determine_tone(sentiment, rating),
            "intent": action
        }
    
    def _calculate_time_since_visit(self, visit_timestamp: datetime) -> str:
        """Calculate human-readable time since visit"""
        now = datetime.now()
        diff = now - visit_timestamp
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            return "قبل قليل"
        elif diff.total_seconds() < 7200:  # Less than 2 hours
            return "قبل ساعة تقريباً"
        elif diff.days == 0:  # Same day
            hours = int(diff.total_seconds() // 3600)
            return f"قبل {hours} ساعات"
        elif diff.days == 1:
            return "أمس"
        else:
            return f"قبل {diff.days} أيام"
    
    async def _generate_personalized_greeting(
        self,
        template: str,
        time_since_visit: str,
        customer_phone: str
    ) -> str:
        """Generate personalized greeting message"""
        
        greeting_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompts.get_personalization_prompt()),
            ("human", f"""
            إنشاء رسالة ترحيب شخصية بناءً على:
            القالب: {template}
            وقت الزيارة: {time_since_visit}
            
            الرسالة يجب أن:
            - تكون ودودة ومرحبة
            - تشير إلى الزيارة الأخيرة
            - تطلب التقييم بطريقة طبيعية
            - لا تتجاوز 100 كلمة
            """)
        ])
        
        chain = greeting_prompt | self.llm.get_chain()
        result = await chain.ainvoke({
            "template": template,
            "time_since_visit": time_since_visit
        })
        
        return result.content
    
    def _parse_analysis_output(self, response) -> Dict[str, Any]:
        """Parse LLM analysis output into structured data"""
        try:
            # Try to extract JSON from response
            content = response.content
            
            # Look for JSON block
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback to default analysis
        return {
            "sentiment_score": 0.0,
            "topics": [],
            "has_rating": False,
            "extracted_rating": None,
            "confidence": 0.5,
            "key_phrases": []
        }
    
    def _format_conversation_history(
        self,
        conversation: FeedbackConversation
    ) -> List[Dict[str, str]]:
        """Format conversation history for context"""
        history = []
        
        for message in conversation.memory.chat_memory.messages:
            if isinstance(message, HumanMessage):
                history.append({
                    "role": "customer",
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                history.append({
                    "role": "assistant",
                    "content": message.content
                })
        
        return history[-6:]  # Last 6 messages for context
    
    def _has_sufficient_detail(
        self,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if we have enough detail to end conversation"""
        topics = analysis.get("topics", [])
        key_phrases = analysis.get("key_phrases", [])
        
        # Consider sufficient if:
        # 1. Multiple topics mentioned
        # 2. Specific examples given
        # 3. Clear sentiment expressed
        
        return (
            len(topics) >= 2 or
            len(key_phrases) >= 3 or
            abs(analysis.get("sentiment_score", 0)) > 0.7
        )
    
    def _determine_tone(self, sentiment: float, rating: Optional[int]) -> str:
        """Determine appropriate response tone"""
        if rating and rating <= 2:
            return "apologetic"
        elif rating and rating >= 4:
            return "grateful"
        elif sentiment < -0.3:
            return "empathetic"
        elif sentiment > 0.3:
            return "positive"
        else:
            return "neutral"
    
    async def extract_structured_feedback(
        self,
        conversation: FeedbackConversation
    ) -> Dict[str, Any]:
        """Extract structured feedback data from completed conversation"""
        
        # Get all conversation messages
        messages = conversation.memory.chat_memory.messages
        conversation_text = "\n".join([
            f"{'العميل' if isinstance(msg, HumanMessage) else 'المطعم'}: {msg.content}"
            for msg in messages
        ])
        
        extraction_prompt = self.prompts.get_extraction_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", extraction_prompt),
            ("human", f"""
            استخراج البيانات المنظمة من هذه المحادثة:
            
            {conversation_text}
            
            أعد JSON مع:
            - overall_rating: التقييم العام (1-5)
            - aspects: تقييمات مختلفة (طعام، خدمة، نظافة، أسعار)
            - topics_mentioned: المواضيع المذكورة
            - specific_items: أطباق أو منتجات محددة
            - sentiment_score: درجة المشاعر (-1 إلى 1)
            - key_feedback: النقاط الرئيسية
            - improvement_suggestions: اقتراحات التحسين
            - would_recommend: هل سيوصي بالمطعم؟
            """)
        ])
        
        chain = prompt | self.llm.get_chain() | self._parse_extraction_output
        
        result = await chain.ainvoke({
            "conversation": conversation_text,
            "context": conversation.context
        })
        
        # Add conversation metadata
        result.update({
            "conversation_id": conversation.id,
            "customer_phone": conversation.customer_phone,
            "visit_timestamp": conversation.visit_timestamp.isoformat(),
            "conversation_length": len(messages),
            "template_used": conversation.template,
            "extracted_at": datetime.now().isoformat()
        })
        
        return result
    
    def _parse_extraction_output(self, response) -> Dict[str, Any]:
        """Parse feedback extraction output"""
        try:
            content = response.content
            
            # Look for JSON block
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data
            
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback to basic extraction
        return {
            "overall_rating": None,
            "aspects": {},
            "topics_mentioned": [],
            "specific_items": [],
            "sentiment_score": 0.0,
            "key_feedback": [],
            "improvement_suggestions": [],
            "would_recommend": None
        }