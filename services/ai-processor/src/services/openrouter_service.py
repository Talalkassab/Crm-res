import httpx
import asyncio
import os
from typing import Dict, Any, List, Optional
from ..schemas import OpenRouterRequest, OpenRouterResponse
from ..utils.config import get_config

class OpenRouterService:
    """OpenRouter API integration service for AI model access."""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.primary_model = "google/gemini-flash-1.5"
        self.fallback_models = [
            "anthropic/claude-3-haiku-20240307",
            "meta-llama/llama-3.1-70b-instruct"
        ]
        self.current_model = self.primary_model
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://crm-res.com",
                "X-Title": "CRM-RES AI Processor",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def generate_response(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        sentiment: Optional[str] = None,
        language: str = "ar"
    ) -> str:
        """Generate AI response for a given message."""
        try:
            # Build system prompt based on context
            system_prompt = await self._build_system_prompt(context, sentiment, language)
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add conversation history if available
            if context and "conversation_history" in context:
                # Insert history before the current message
                history = context["conversation_history"][-5:]  # Last 5 messages
                messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
            
            # Make API request with retries
            response = await self._make_request_with_fallback(messages)
            
            if response and response.get("choices"):
                return response["choices"][0]["message"]["content"].strip()
            
            return "عذراً، لا أستطيع معالجة رسالتك في الوقت الحالي. يرجى المحاولة لاحقاً."
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "عذراً، حدث خطأ في معالجة رسالتك. سيتم توجيهك لأحد موظفينا قريباً."
    
    async def _build_system_prompt(
        self, 
        context: Optional[Dict[str, Any]] = None,
        sentiment: Optional[str] = None,
        language: str = "ar"
    ) -> str:
        """Build system prompt based on context and requirements."""
        
        # Base prompt for Arabic restaurant customer service
        base_prompt = """أنت مساعد ذكي لمطعم يتحدث العربية. مهمتك هي التحدث مع الزبائن بطريقة مهذبة ومفيدة.

القواعد المهمة:
- تحدث بالعربية السعودية (إلا إذا طُلب منك غير ذلك)
- كن مهذباً ومحترماً في جميع الأوقات
- اهتم بالثقافة الإسلامية والعادات المحلية
- إذا لم تكن متأكداً من إجابة، اطلب من الزبون انتظار موظف
- لا تقدم معلومات طبية أو قانونية"""
        
        # Add personality based on context
        if context:
            personality = context.get("personality", "formal")
            if personality == "casual":
                base_prompt += "\n- استخدم أسلوباً ودوداً وغير رسمي"
            elif personality == "formal":
                base_prompt += "\n- استخدم أسلوباً رسمياً ومهذباً"
        
        # Add dialect awareness
        if context and "dialect" in context:
            dialect = context["dialect"]
            if dialect == "ar-EG":
                base_prompt += "\n- تعرف على اللهجة المصرية واستجب بطريقة مناسبة"
            elif dialect == "ar-LV":
                base_prompt += "\n- تعرف على اللهجة الشامية واستجب بطريقة مناسبة"
        
        # Add sentiment awareness
        if sentiment == "negative":
            base_prompt += "\n- الزبون يبدو مستاءً، كن أكثر تفهماً واعتذاراً"
            base_prompt += "\n- اعرض حلولاً سريعة أو تحويل للإدارة إذا لزم الأمر"
        elif sentiment == "positive":
            base_prompt += "\n- الزبون راضٍ، حافظ على هذا الشعور الإيجابي"
        
        # Add cultural phrases
        base_prompt += """

العبارات الثقافية المهمة:
- "السلام عليكم" - رد بـ "وعليكم السلام ورحمة الله وبركاته"
- "بارك الله فيك" - رد بـ "وفيك بارك الله"
- "إن شاء الله" - استخدمها عند الحديث عن المستقبل
- "ما شاء الله" - استخدمها عند المدح

أمثلة على الردود:
- للشكاوى: "نعتذر بشدة عن هذه التجربة، سنعمل على حل هذه المشكلة فوراً"
- للمدح: "شكراً لك، ما شاء الله، نسعد بإعجابك"
- للاستفسارات: "بإذنك، دعني أتحقق من هذه المعلومة لك"""
        
        return base_prompt
    
    async def _make_request_with_fallback(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Make API request with model fallback on failure."""
        models_to_try = [self.current_model] + [m for m in self.fallback_models if m != self.current_model]
        
        for model in models_to_try:
            try:
                request_data = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": False
                }
                
                response = await self.client.post("/chat/completions", json=request_data)
                response.raise_for_status()
                
                result = response.json()
                self.current_model = model  # Update current model on success
                return result
                
            except httpx.HTTPStatusError as e:
                print(f"HTTP error with model {model}: {e.response.status_code}")
                if e.response.status_code == 429:  # Rate limit
                    await asyncio.sleep(2)
                    continue
                elif e.response.status_code >= 500:  # Server error
                    continue
                else:
                    break  # Client error, don't retry
            except Exception as e:
                print(f"Error with model {model}: {e}")
                continue
        
        return None
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter."""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            models_data = response.json()
            return [model["id"] for model in models_data.get("data", [])]
        except Exception as e:
            print(f"Error fetching models: {e}")
            return [self.primary_model] + self.fallback_models
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        try:
            available_models = await self.get_available_models()
            if model_name in available_models:
                self.current_model = model_name
                return True
            return False
        except Exception as e:
            print(f"Error switching model: {e}")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()