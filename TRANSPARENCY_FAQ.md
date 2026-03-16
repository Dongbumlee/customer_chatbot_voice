# Transparency FAQ — Customer Chatbot GSA with Voice

## What is the Customer Chatbot?

The Customer Chatbot is an AI-powered conversational assistant that helps users discover
products, get answers to policy questions, and interact through text or voice. It uses
Azure AI services for intelligent responses.

## What can the system do?

- Answer product questions and provide recommendations via specialized AI agents
- Respond to policy inquiries (returns, warranty, shipping) using RAG over official documents
- Accept both text and voice input, with real-time speech-to-text and text-to-speech
- Display visual product cards with images, pricing, and descriptions
- Maintain conversation history per user

## What is the system's intended use?

The system is designed for customer-facing product discovery and support within the scope
of the product catalog and published company policies. It is NOT intended for:
- Processing payments or executing transactions
- Providing medical, legal, or financial advice
- Replacing human support for complex escalations

## How was the system evaluated?

- Automated testing: Unit, integration, and E2E tests covering agent logic, API endpoints,
  and voice pipeline
- RAI evaluation: Prompt injection testing, content safety filter validation, bias audits
  on product recommendations
- Manual QA: User acceptance testing across text and voice modalities

## What are the limitations?

- Voice mode requires an active internet connection and browser microphone access
- The system may occasionally provide imprecise product information; always verify details
- Multi-language support quality varies by language
- The system identifies itself as an AI and never claims to be human

## What data does the system collect?

- Chat messages (text transcripts only — audio is NOT stored)
- User profile information from Microsoft Entra ID (display name, email)
- Session metadata (timestamps, modality used)

Chat history has a configurable TTL in Cosmos DB for automatic cleanup.
