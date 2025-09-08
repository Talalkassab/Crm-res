// AI Processor Service Types - Shared across all services
// This file contains TypeScript definitions that match the Python Pydantic models

export enum SentimentType {
  POSITIVE = "positive",
  NEUTRAL = "neutral",
  NEGATIVE = "negative"
}

export enum PersonalityType {
  FORMAL = "formal",
  CASUAL = "casual",
  TRADITIONAL = "traditional",
  MODERN = "modern"
}

export enum DialectType {
  SAUDI = "ar-SA",
  EGYPTIAN = "ar-EG",
  LEVANTINE = "ar-LV",
  ENGLISH = "en"
}

export interface ConversationContext {
  personality: PersonalityType;
  dialect: DialectType;
  sentiment_history: string[];
  topics_discussed: string[];
  escalation_triggers: string[];
  cultural_context: Record<string, any>;
  conversation_id?: string;
  customer_id?: string;
}

export interface AIProcessingRequest {
  message: string;
  conversation_id: string;
  customer_id: string;
  context?: Record<string, any>;
  restaurant_id?: string;
  language_preference?: string;
}

export interface AIProcessingResponse {
  response: string;
  sentiment: string;
  confidence: number;
  suggested_actions: string[];
  is_prayer_time: boolean;
  should_escalate: boolean;
  dialect_detected?: string;
  cultural_phrases_used: string[];
}

export interface WhatsAppWebhook {
  object: string;
  entry: Array<Record<string, any>>;
}

export interface SentimentAnalysisResult {
  sentiment: SentimentType;
  confidence: number;
  negative_indicators: string[];
  positive_indicators: string[];
  escalation_needed: boolean;
}

export interface PrayerTimeStatus {
  is_prayer_time: boolean;
  current_prayer?: string;
  next_prayer?: string;
  time_until_next?: number; // minutes
  city: string;
}

export interface OpenRouterRequest {
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature: number;
  max_tokens?: number;
  stream: boolean;
}

export interface OpenRouterResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<Record<string, any>>;
  usage: Record<string, number>;
}

export interface ArabicProcessingResult {
  original_text: string;
  processed_text: string;
  dialect_detected: DialectType;
  cultural_phrases: string[];
  confidence: number;
}