import pytest
from src.prompts.arabic_prompts import ArabicPromptManager
from src.schemas import PersonalityType, DialectType

@pytest.mark.unit
@pytest.mark.arabic
class TestArabicPromptManager:
    """Test suite for Arabic prompt management."""
    
    @pytest.fixture
    def prompt_manager(self):
        """Create prompt manager instance."""
        return ArabicPromptManager()
    
    def test_get_system_prompt_default(self, prompt_manager):
        """Test getting system prompt with default parameters."""
        prompt = prompt_manager.get_system_prompt()
        
        # Should contain basic Arabic restaurant AI instructions
        assert "مساعد ذكي" in prompt
        assert "مطعم" in prompt or "restaurant" in prompt.lower()
        assert "العربية السعودية" in prompt or "saudi" in prompt.lower()
    
    def test_get_system_prompt_formal_personality(self, prompt_manager):
        """Test formal personality prompt."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.formal,
            dialect=DialectType.saudi
        )
        
        # Should contain formal personality indicators
        assert any(word in prompt for word in ["رسمية", "مهذبة", "احترام", "formal"])
        assert any(word in prompt for word in ["حضرتك", "سيادتك", "يشرفنا"])
    
    def test_get_system_prompt_casual_personality(self, prompt_manager):
        """Test casual personality prompt."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.casual,
            dialect=DialectType.saudi
        )
        
        # Should contain casual personality indicators
        assert any(word in prompt for word in ["ودودة", "غير رسمي", "casual", "دفئاً"])
        assert any(word in prompt for word in ["أهلاً وسهلاً", "نورتوا"])
    
    def test_get_system_prompt_saudi_dialect(self, prompt_manager):
        """Test Saudi dialect specific prompt."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.formal,
            dialect=DialectType.saudi
        )
        
        # Should contain Saudi dialect awareness
        assert any(word in prompt for word in ["سعودية", "وش رايك", "توا", "هلا والله"])
    
    def test_get_system_prompt_egyptian_dialect(self, prompt_manager):
        """Test Egyptian dialect specific prompt."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.casual,
            dialect=DialectType.egyptian
        )
        
        # Should contain Egyptian dialect awareness
        assert any(word in prompt for word in ["مصرية", "ايه رايك", "معلش", "أوي"])
    
    def test_get_system_prompt_levantine_dialect(self, prompt_manager):
        """Test Levantine dialect specific prompt."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.casual,
            dialect=DialectType.levantine
        )
        
        # Should contain Levantine dialect awareness
        assert any(word in prompt for word in ["شامية", "شو رايك", "منيح", "كتير"])
    
    def test_get_system_prompt_with_negative_context(self, prompt_manager):
        """Test prompt with negative sentiment context."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.formal,
            dialect=DialectType.saudi,
            context={"sentiment": "negative"}
        )
        
        # Should contain negative handling instructions
        assert any(word in prompt for word in ["مستاءً", "اعتذاراً", "حلولاً", "تفهماً"])
    
    def test_get_system_prompt_with_ramadan_context(self, prompt_manager):
        """Test prompt with Ramadan context."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.traditional,
            dialect=DialectType.saudi,
            context={"is_ramadan": True}
        )
        
        # Should contain Ramadan-specific instructions
        assert any(word in prompt for word in ["رمضان", "صيام", "إفطار", "سحور"])
    
    def test_get_system_prompt_first_time_customer(self, prompt_manager):
        """Test prompt for first-time customer."""
        prompt = prompt_manager.get_system_prompt(
            personality=PersonalityType.casual,
            dialect=DialectType.saudi,
            context={"first_time_customer": True}
        )
        
        # Should contain welcome instructions for new customers
        assert any(word in prompt for word in ["نورتوا", "مرحباً", "تخصصات", "شعبية"])
    
    def test_cultural_sensitivity_validation(self, prompt_manager):
        """Test cultural sensitivity validation."""
        # Test a culturally appropriate prompt
        good_prompt = "مرحباً بكم في مطعمنا، بارك الله فيكم"
        result = prompt_manager.validate_prompt_cultural_sensitivity(good_prompt)
        
        assert result["culturally_sensitive"] is True
        assert result["has_islamic_elements"] is True
        assert len(result["issues"]) == 0
        
        # Test a potentially problematic prompt
        bad_prompt = "Welcome to our restaurant, we serve pork and wine"
        result = prompt_manager.validate_prompt_cultural_sensitivity(bad_prompt)
        
        assert result["culturally_sensitive"] is False
        assert len(result["issues"]) > 0
        assert any("pork" in issue for issue in result["issues"])
    
    def test_response_examples_retrieval(self, prompt_manager):
        """Test getting response examples."""
        # Test formal greeting example
        example = prompt_manager.get_response_examples("greeting_formal")
        
        assert "ar" in example
        assert "السلام عليكم" in example["ar"]
        assert "context" in example
        
        # Test casual greeting example
        example = prompt_manager.get_response_examples("greeting_casual")
        
        assert "ar" in example
        assert any(word in example["ar"] for word in ["هلا", "نورت"])
    
    def test_complaint_response_example(self, prompt_manager):
        """Test complaint response example."""
        example = prompt_manager.get_response_examples("complaint_response")
        
        assert "ar" in example
        assert any(word in example["ar"] for word in ["نعتذر", "بشدة", "حل"])
    
    def test_prayer_time_response_example(self, prompt_manager):
        """Test prayer time response example."""
        example = prompt_manager.get_response_examples("prayer_time_response")
        
        assert "ar" in example
        assert any(word in example["ar"] for word in ["صلاة", "نعتذر", "وقت"])
    
    def test_prompt_contains_islamic_awareness(self, prompt_manager):
        """Test that prompts contain Islamic awareness."""
        prompt = prompt_manager.get_system_prompt()
        
        # Should contain Islamic/cultural awareness instructions
        islamic_indicators = [
            "صلاة", "الإسلامية", "الثقافة", "religious", "prayer", "cultural"
        ]
        assert any(indicator in prompt for indicator in islamic_indicators)
    
    def test_prompt_contains_response_guidelines(self, prompt_manager):
        """Test that prompts contain response guidelines."""
        prompt = prompt_manager.get_system_prompt()
        
        # Should contain response guidelines
        guideline_indicators = [
            "إرشادات", "الرد", "guidelines", "مختصراً", "واضحاً"
        ]
        assert any(indicator in prompt for indicator in guideline_indicators)
    
    def test_personality_prompt_consistency(self, prompt_manager):
        """Test that personality prompts are consistent."""
        formal_prompt = prompt_manager.get_system_prompt(personality=PersonalityType.formal)
        casual_prompt = prompt_manager.get_system_prompt(personality=PersonalityType.casual)
        
        # Both should contain base restaurant AI content
        assert "مساعد ذكي" in formal_prompt
        assert "مساعد ذكي" in casual_prompt
        
        # But should have different personality instructions
        assert formal_prompt != casual_prompt
    
    def test_dialect_prompt_uniqueness(self, prompt_manager):
        """Test that dialect prompts are unique."""
        saudi_prompt = prompt_manager.get_system_prompt(dialect=DialectType.saudi)
        egyptian_prompt = prompt_manager.get_system_prompt(dialect=DialectType.egyptian)
        levantine_prompt = prompt_manager.get_system_prompt(dialect=DialectType.levantine)
        
        # All should be different
        assert saudi_prompt != egyptian_prompt
        assert saudi_prompt != levantine_prompt
        assert egyptian_prompt != levantine_prompt
    
    def test_empty_context_handling(self, prompt_manager):
        """Test handling of empty context."""
        prompt = prompt_manager.get_system_prompt(context={})
        
        # Should still generate a valid prompt
        assert len(prompt) > 100  # Should be substantial
        assert "مساعد ذكي" in prompt
    
    def test_none_context_handling(self, prompt_manager):
        """Test handling of None context."""
        prompt = prompt_manager.get_system_prompt(context=None)
        
        # Should still generate a valid prompt
        assert len(prompt) > 100
        assert "مساعد ذكي" in prompt