/**
 * Shared TypeScript types for the Customer Chatbot frontend.
 */

export interface ChatMessage {
  message_id: string;
  session_id: string;
  content: string;
  role: "user" | "assistant" | "system";
  modality: "text" | "voice";
  agent?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  modality: "text" | "voice" | "mixed";
  created_at: string;
  last_active_at: string;
  is_active: boolean;
}

export interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
  description: string;
  image_url?: string;
  attributes: Record<string, unknown>;
}

export interface AgentResponse {
  content: string;
  agent: string;
  intent: string;
  product_cards?: Product[];
  metadata?: Record<string, unknown>;
}

export type VoiceMode = "full_voice" | "voice_in_only" | "text_only";
