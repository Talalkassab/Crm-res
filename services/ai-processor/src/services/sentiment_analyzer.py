import re
from typing import Dict, List, Any
from ..schemas import SentimentAnalysisResult, SentimentType

class SentimentAnalyzer:
    """Arabic sentiment analysis service."""
    
    def __init__(self):
        # Arabic negative indicators
        self.negative_keywords = {
            'bad': ['سيء', 'سيئة', 'بشع', 'فظيع', 'مقرف', 'لا يعجبني', 'مش كويس', 'مش طيب'],
            'complaint': ['شكوى', 'مشكلة', 'مشاكل', 'اشتكي', 'غير راضي', 'مش راضي'],
            'anger': ['غاضب', 'متضايق', 'متأذي', 'زعلان', 'متكدر', 'محبط'],
            'disappointment': ['خيبة أمل', 'مخيب للآمال', 'متوقع أحسن', 'مش زي ما متوقع'],
            'service': ['خدمة سيئة', 'معاملة سيئة', 'موظفين مش مهذبين', 'بطء في الخدمة']
        }
        
        # Arabic positive indicators  
        self.positive_keywords = {
            'excellent': ['ممتاز', 'رائع', 'مذهل', 'جميل', 'حلو', 'طيب', 'كويس'],
            'love': ['أحب', 'بحب', 'عاجبني', 'معجبني', 'يعجبني'],
            'praise': ['برavo', 'تسلم', 'الله يعطيك العافية', 'ما شاء الله', 'بارك الله فيكم'],
            'satisfaction': ['راضي', 'مسرور', 'سعيد', 'منبسط', 'مبسوط'],
            'quality': ['جودة عالية', 'طعم رائع', 'نكهة ممتازة', 'طازج', 'لذيذ']
        }
        
        # Cultural and religious sensitivity indicators
        self.cultural_phrases = [
            'السلام عليكم', 'بارك الله فيك', 'جزاك الله خير', 
            'إن شاء الله', 'ما شاء الله', 'الله يعطيك العافية',
            'بإذنك', 'لو سمحت', 'بعد إذنك'
        ]
        
        # Escalation triggers
        self.escalation_triggers = [
            'مدير', 'إدارة', 'شكوى رسمية', 'أريد أن أشتكي',
            'سأتصل بالشؤون الصحية', 'سأكتب تقييم سيء', 
            'هذا آخر مرة', 'لن آتي مرة أخرى'
        ]
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of Arabic text."""
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Detect sentiment
            sentiment_score = self._calculate_sentiment_score(cleaned_text)
            sentiment = self._determine_sentiment(sentiment_score)
            
            # Find indicators
            negative_indicators = self._find_indicators(cleaned_text, self.negative_keywords)
            positive_indicators = self._find_indicators(cleaned_text, self.positive_keywords)
            
            # Check for escalation triggers
            escalation_needed = self._check_escalation_triggers(cleaned_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                sentiment_score, negative_indicators, positive_indicators
            )
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "negative_indicators": negative_indicators,
                "positive_indicators": positive_indicators,
                "escalation_needed": escalation_needed,
                "cultural_phrases": self._find_cultural_phrases(cleaned_text)
            }
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "negative_indicators": [],
                "positive_indicators": [],
                "escalation_needed": False,
                "cultural_phrases": []
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize Arabic text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize Arabic characters
        text = re.sub(r'[إأآا]', 'ا', text)  # Normalize Alif
        text = re.sub(r'[ىي]', 'ي', text)     # Normalize Yeh
        text = re.sub(r'ة', 'ه', text)        # Normalize Teh Marbuta
        text = re.sub(r'[ؤئ]', 'و', text)     # Normalize Waw
        
        return text.lower()
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score from -1 (negative) to +1 (positive)."""
        positive_count = 0
        negative_count = 0
        
        # Count positive keywords
        for category, keywords in self.positive_keywords.items():
            for keyword in keywords:
                positive_count += len(re.findall(keyword, text))
        
        # Count negative keywords  
        for category, keywords in self.negative_keywords.items():
            for keyword in keywords:
                negative_count += len(re.findall(keyword, text))
        
        # Calculate score
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        positive_ratio = positive_count / total_words
        negative_ratio = negative_count / total_words
        
        return positive_ratio - negative_ratio
    
    def _determine_sentiment(self, score: float) -> str:
        """Determine sentiment category from score."""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _find_indicators(self, text: str, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """Find sentiment indicators in text."""
        indicators = []
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword in text:
                    indicators.append(keyword)
        return indicators
    
    def _find_cultural_phrases(self, text: str) -> List[str]:
        """Find cultural/religious phrases in text."""
        found_phrases = []
        for phrase in self.cultural_phrases:
            if phrase in text:
                found_phrases.append(phrase)
        return found_phrases
    
    def _check_escalation_triggers(self, text: str) -> bool:
        """Check if text contains escalation triggers."""
        for trigger in self.escalation_triggers:
            if trigger in text:
                return True
        return False
    
    def _calculate_confidence(
        self, 
        sentiment_score: float, 
        negative_indicators: List[str],
        positive_indicators: List[str]
    ) -> float:
        """Calculate confidence score for sentiment analysis."""
        # Base confidence from score magnitude
        base_confidence = min(abs(sentiment_score) * 2, 0.9)
        
        # Boost confidence if we have clear indicators
        indicator_count = len(negative_indicators) + len(positive_indicators)
        indicator_boost = min(indicator_count * 0.1, 0.3)
        
        # Ensure minimum confidence
        confidence = max(base_confidence + indicator_boost, 0.3)
        
        return min(confidence, 1.0)