import re
from typing import Dict, List, Any, Optional
from ..schemas import ArabicProcessingResult, DialectType

class ArabicProcessor:
    """Arabic text processing and dialect detection service."""
    
    def __init__(self):
        # Dialect-specific vocabulary patterns
        self.dialect_patterns = {
            DialectType.saudi: {
                'words': ['وش', 'ايش', 'كذا', 'جان', 'توا', 'قاعد', 'يالله', 'يا خوي'],
                'phrases': ['على الله', 'بإذن الله', 'ان شاء الله'],
                'greetings': ['هلا والله', 'أهلين', 'مرحبتين']
            },
            DialectType.egyptian: {
                'words': ['ايه', 'مش', 'كده', 'اهو', 'يلا', 'معلش', 'خالص', 'أوي'],
                'phrases': ['ان شاء الله', 'معلش يا عم', 'خلاص كده'],
                'greetings': ['ازيك', 'أهلا وسهلا', 'نورت']
            },
            DialectType.levantine: {
                'words': ['شو', 'مو', 'هيك', 'منيح', 'كتير', 'شوي', 'يالا', 'منشان'],
                'phrases': ['كيف الحال', 'الله يعطيك العافية', 'بلكي'],
                'greetings': ['أهلا وسهلا', 'كيفك', 'أهلين فيك']
            }
        }
        
        # Cultural and religious phrases
        self.cultural_phrases = {
            'greetings': [
                'السلام عليكم', 'وعليكم السلام', 'أهلا وسهلا', 'مرحبا',
                'صباح الخير', 'صباح النور', 'مساء الخير', 'مساء النور'
            ],
            'blessings': [
                'بارك الله فيك', 'الله يعطيك العافية', 'جزاك الله خير',
                'الله يكرمك', 'بإذن الله', 'ما شاء الله', 'تسلم'
            ],
            'expressions': [
                'إن شاء الله', 'بسم الله', 'الحمد لله', 'استغفر الله',
                'لا حول ولا قوة إلا بالله', 'الله أكبر', 'سبحان الله'
            ]
        }
        
        # Arabic text normalization patterns
        self.normalization_patterns = [
            # Alif variations
            (r'[إأآا]', 'ا'),
            # Yeh variations
            (r'[ىي]', 'ي'),
            # Teh Marbuta
            (r'ة', 'ه'),
            # Waw variations
            (r'[ؤئ]', 'و'),
            # Remove diacritics
            (r'[\u064B-\u065F\u0670\u0640]', ''),
            # Normalize spaces
            (r'\s+', ' ')
        ]
    
    def preprocess(self, text: str) -> str:
        """Preprocess Arabic text for better processing."""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Apply normalization patterns
        for pattern, replacement in self.normalization_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned
    
    def detect_dialect(self, text: str) -> ArabicProcessingResult:
        """Detect Arabic dialect from text."""
        try:
            processed_text = self.preprocess(text)
            
            # Count dialect-specific markers
            dialect_scores = {}
            
            for dialect, patterns in self.dialect_patterns.items():
                score = 0
                matches = []
                
                # Check words
                for word in patterns['words']:
                    if word in processed_text:
                        score += 2
                        matches.append(word)
                
                # Check phrases
                for phrase in patterns['phrases']:
                    if phrase in processed_text:
                        score += 3
                        matches.append(phrase)
                
                # Check greetings  
                for greeting in patterns['greetings']:
                    if greeting in processed_text:
                        score += 1
                        matches.append(greeting)
                
                dialect_scores[dialect] = {'score': score, 'matches': matches}
            
            # Determine most likely dialect
            best_dialect = max(dialect_scores.keys(), key=lambda d: dialect_scores[d]['score'])
            best_score = dialect_scores[best_dialect]['score']
            
            # Calculate confidence
            total_score = sum(data['score'] for data in dialect_scores.values())
            confidence = best_score / max(total_score, 1) if total_score > 0 else 0.5
            
            # If no clear winner, default to Saudi
            if best_score == 0:
                best_dialect = DialectType.saudi
                confidence = 0.3
            
            # Find cultural phrases
            cultural_phrases = self._find_cultural_phrases(processed_text)
            
            return ArabicProcessingResult(
                original_text=text,
                processed_text=processed_text,
                dialect_detected=best_dialect,
                cultural_phrases=cultural_phrases,
                confidence=min(confidence, 1.0)
            )
            
        except Exception as e:
            print(f"Error in dialect detection: {e}")
            return ArabicProcessingResult(
                original_text=text,
                processed_text=self.preprocess(text),
                dialect_detected=DialectType.saudi,
                cultural_phrases=[],
                confidence=0.3
            )
    
    def _find_cultural_phrases(self, text: str) -> List[str]:
        """Find cultural and religious phrases in text."""
        found_phrases = []
        
        for category, phrases in self.cultural_phrases.items():
            for phrase in phrases:
                if phrase in text:
                    found_phrases.append(phrase)
        
        return found_phrases
    
    def generate_appropriate_response_style(self, dialect: DialectType, personality: str = "formal") -> Dict[str, Any]:
        """Generate response style guidelines based on dialect and personality."""
        
        base_style = {
            "tone": "respectful",
            "formality": personality,
            "cultural_awareness": True
        }
        
        if dialect == DialectType.saudi:
            return {
                **base_style,
                "greetings": ["أهلاً وسهلاً", "مرحباً بك", "هلا والله"],
                "expressions": ["بإذن الله", "إن شاء الله", "على الله"],
                "closing": ["الله يعطيك العافية", "تسلم"],
                "vocabulary_preference": "formal_arabic_with_saudi_terms"
            }
        
        elif dialect == DialectType.egyptian:
            return {
                **base_style,
                "greetings": ["أهلاً وسهلاً", "نورتنا", "أزيك"],
                "expressions": ["إن شاء الله", "معلش", "خلاص كده"],
                "closing": ["ربنا يخليك", "تسلم إيديك"],
                "vocabulary_preference": "friendly_egyptian_style"
            }
        
        elif dialect == DialectType.levantine:
            return {
                **base_style,
                "greetings": ["أهلاً وسهلاً", "كيفك", "أهلين فيك"],
                "expressions": ["إن شاء الله", "الله يعطيك العافية", "منيح"],
                "closing": ["يسلمو إيديك", "الله يعطيك العافية"],
                "vocabulary_preference": "warm_levantine_style"
            }
        
        else:  # Default to standard Arabic
            return {
                **base_style,
                "greetings": ["السلام عليكم", "أهلاً وسهلاً", "مرحباً"],
                "expressions": ["بإذن الله", "إن شاء الله", "ما شاء الله"],
                "closing": ["بارك الله فيك", "جزاك الله خيراً"],
                "vocabulary_preference": "standard_arabic"
            }
    
    async def translate(self, text: str, target_language: str = "ar") -> str:
        """Basic translation support (placeholder for future enhancement)."""
        # This is a placeholder - in production, you might integrate with 
        # a proper translation service or use the OpenRouter API for translation
        
        if target_language == "ar" and self._is_english(text):
            # Simple English to Arabic translations for common phrases
            translations = {
                "hello": "مرحبا",
                "thank you": "شكرا لك",
                "please": "من فضلك",
                "sorry": "آسف",
                "yes": "نعم",
                "no": "لا",
                "good": "جيد",
                "bad": "سيء"
            }
            
            lower_text = text.lower().strip()
            return translations.get(lower_text, text)
        
        return text  # Return as-is if no translation needed
    
    def _is_english(self, text: str) -> bool:
        """Check if text is primarily English."""
        # Simple heuristic: if text contains mostly Latin characters
        latin_chars = sum(1 for char in text if ord(char) < 256)
        total_chars = len(text.replace(' ', ''))
        
        return total_chars > 0 and (latin_chars / total_chars) > 0.7
    
    def format_cultural_response(self, base_response: str, cultural_phrases: List[str]) -> str:
        """Format response with appropriate cultural phrases."""
        # Add greeting if customer used one
        for phrase in cultural_phrases:
            if phrase == "السلام عليكم":
                return "وعليكم السلام ورحمة الله وبركاته. " + base_response
            elif phrase in ["بارك الله فيك", "جزاك الله خير"]:
                base_response += ". وفيك بارك الله"
        
        return base_response
    
    def validate_arabic_text(self, text: str) -> Dict[str, Any]:
        """Validate and analyze Arabic text quality."""
        try:
            if not text:
                return {"valid": False, "issues": ["empty_text"]}
            
            issues = []
            
            # Check for mixed scripts (might indicate encoding issues)
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
            has_latin = any('A' <= char <= 'Z' or 'a' <= char <= 'z' for char in text)
            
            if has_arabic and has_latin:
                issues.append("mixed_scripts")
            
            # Check for excessive punctuation
            punct_count = sum(1 for char in text if char in '!@#$%^&*()_+-=[]{}|;:,.<>?/')
            if punct_count / len(text) > 0.3:
                issues.append("excessive_punctuation")
            
            # Check for very short messages (might be spam)
            if len(text.strip()) < 3:
                issues.append("too_short")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "has_arabic": has_arabic,
                "has_latin": has_latin,
                "length": len(text)
            }
            
        except Exception as e:
            print(f"Error validating Arabic text: {e}")
            return {"valid": True, "issues": [], "has_arabic": True, "has_latin": False, "length": len(text)}