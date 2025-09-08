#!/usr/bin/env python3
"""Test script to verify service startup."""

import os
import sys
import asyncio

# Set environment for testing
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-startup-check'
os.environ['ENVIRONMENT'] = 'test'

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_service_startup():
    """Test that all services can be imported and initialized."""
    try:
        print("🧪 Testing AI Processor service startup...")
        
        # Test imports
        print("📦 Testing imports...")
        from schemas import AIProcessingRequest, AIProcessingResponse
        from services.sentiment_analyzer import SentimentAnalyzer
        from services.prayer_time_service import PrayerTimeService
        from services.arabic_processor import ArabicProcessor
        from services.openrouter_service import OpenRouterService
        from agents.message_processor import MessageProcessor
        print("✅ All imports successful")
        
        # Test service initialization
        print("🔧 Testing service initialization...")
        sentiment_analyzer = SentimentAnalyzer()
        print("✅ SentimentAnalyzer initialized")
        
        prayer_service = PrayerTimeService()
        print("✅ PrayerTimeService initialized")
        
        arabic_processor = ArabicProcessor()
        print("✅ ArabicProcessor initialized")
        
        openrouter_service = OpenRouterService()
        print("✅ OpenRouterService initialized")
        
        message_processor = MessageProcessor()
        print("✅ MessageProcessor initialized")
        
        # Test basic functionality
        print("🔍 Testing basic functionality...")
        
        # Test Arabic processing
        result = arabic_processor.detect_dialect("مرحبا")
        assert result.original_text == "مرحبا"
        print("✅ Arabic processing works")
        
        # Test sentiment analysis
        sentiment_result = await sentiment_analyzer.analyze("مرحبا")
        assert "sentiment" in sentiment_result
        print("✅ Sentiment analysis works")
        
        print("🎉 All tests passed! Service is ready for deployment.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up async resources
        if 'openrouter_service' in locals() and hasattr(openrouter_service, 'client'):
            try:
                await openrouter_service.client.aclose()
            except:
                pass
        
        if 'prayer_service' in locals() and hasattr(prayer_service, 'client'):
            try:
                await prayer_service.client.aclose()
            except:
                pass

if __name__ == "__main__":
    success = asyncio.run(test_service_startup())
    sys.exit(0 if success else 1)