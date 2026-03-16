# API Documentation: Customer Chatbot API

> **Base URL:** `/api`
> **Authentication:** Microsoft Entra ID Bearer Token
> **Date:** 2026-03-16

---

## Overview

The Customer Chatbot API provides REST endpoints for text-based chat interaction, product
catalog access, and health probes, plus a WebSocket endpoint for real-time voice streaming.
Messages are routed through a multi-agent orchestrator (Chat, Product, Policy agents) powered
by Azure OpenAI GPT-4o and Semantic Kernel.

## Authentication

All chat endpoints require a valid Microsoft Entra ID Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

The voice WebSocket endpoint authenticates via an initial JSON message containing the token.
Health and readiness probes require no authentication. The product endpoint is unauthenticated.

---

## Chat Endpoints

### Send Message

```
POST /api/chat/message
```

Routes a user message through the `ChatbotOrchestrator` for intent classification and
domain-specific agent handling.

**Request Body:**

```json
{
  "session_id": "string",
  "content": "string",
  "modality": "text"
}
```

| Field        | Type   | Required | Description                     |
| ------------ | ------ | -------- | ------------------------------- |
| `session_id` | string | Yes      | Active chat session ID          |
| `content`    | string | Yes      | User message text               |
| `modality`   | string | No       | `"text"` (default) or `"voice"` |

**Response:** `200 OK`

```json
{
  "message_id": "uuid",
  "session_id": "string",
  "content": "Agent response text",
  "agent": "product",
  "metadata": {
    "product_cards": [],
    "sources": []
  },
  "timestamp": "2026-03-16T00:00:00Z"
}
```

| Field        | Type         | Description                                                  |
| ------------ | ------------ | ------------------------------------------------------------ |
| `message_id` | string       | Unique message identifier                                    |
| `session_id` | string       | Session this message belongs to                              |
| `content`    | string       | Agent response content                                       |
| `agent`      | string\|null | Agent that handled the request (`chat`, `product`, `policy`) |
| `metadata`   | object\|null | Additional data (product cards, policy sources)              |
| `timestamp`  | datetime     | Response timestamp (UTC)                                     |

**Errors:**

| Status | Description              |
| ------ | ------------------------ |
| 401    | Missing or invalid token |
| 422    | Invalid request body     |

---

### Create Chat Session

```
POST /api/chat/session
```

Creates a new chat session for the authenticated user.

**Request Body:** None

**Response:** `200 OK`

```json
{
  "session_id": "uuid",
  "title": "New Chat",
  "modality": "text",
  "created_at": "2026-03-16T00:00:00Z",
  "last_active_at": "2026-03-16T00:00:00Z",
  "is_active": true
}
```

| Field            | Type     | Description                       |
| ---------------- | -------- | --------------------------------- |
| `session_id`     | string   | Unique session identifier         |
| `title`          | string   | Session title                     |
| `modality`       | string   | `"text"`, `"voice"`, or `"mixed"` |
| `created_at`     | datetime | Session creation time (UTC)       |
| `last_active_at` | datetime | Last activity time (UTC)          |
| `is_active`      | bool     | Whether session is active         |

**Errors:**

| Status | Description              |
| ------ | ------------------------ |
| 401    | Missing or invalid token |

---

### Get Chat History

```
GET /api/chat/session/{session_id}/history
```

Retrieves all messages for a specific session. Only returns history for sessions owned
by the authenticated user.

**Path Parameters:**

| Parameter    | Type   | Description       |
| ------------ | ------ | ----------------- |
| `session_id` | string | Target session ID |

**Response:** `200 OK`

```json
[
  {
    "message_id": "uuid",
    "session_id": "string",
    "content": "User or agent message",
    "agent": "chat",
    "metadata": null,
    "timestamp": "2026-03-16T00:00:00Z"
  }
]
```

**Errors:**

| Status | Description                            |
| ------ | -------------------------------------- |
| 401    | Missing or invalid token               |
| 404    | Session not found or not owned by user |

---

### End Session

```
DELETE /api/chat/session/{session_id}
```

Ends and archives a chat session. The session's `is_active` flag is set to `false`.

**Path Parameters:**

| Parameter    | Type   | Description       |
| ------------ | ------ | ----------------- |
| `session_id` | string | Target session ID |

**Response:** `204 No Content`

**Errors:**

| Status | Description                            |
| ------ | -------------------------------------- |
| 401    | Missing or invalid token               |
| 404    | Session not found or not owned by user |

---

## Voice Endpoint

### Voice Audio Stream (WebSocket)

```
WS /api/voice/stream
```

Bidirectional WebSocket endpoint for real-time voice interaction. Accepts audio chunks from
the client, streams to Azure Voice Live API for STT, processes via `ChatbotOrchestrator`,
and returns TTS audio and structured responses.

**Protocol:**

1. **Client connects** — WebSocket handshake.
2. **Client sends auth message** (JSON):
   ```json
   {
     "type": "auth",
     "token": "<Entra ID bearer token>",
     "session_id": "optional-session-id"
   }
   ```
3. **Server responds** with session confirmation:
   ```json
   { "type": "session_started", "session_id": "voice-<oid>" }
   ```
4. **Client streams audio** as binary WebSocket frames.
5. **Server sends transcription** events:
   ```json
   { "type": "transcription", "text": "Transcribed user speech" }
   ```
6. **Server sends agent response** (JSON):
   ```json
   {
     "type": "response",
     "content": "Agent response text",
     "agent": "product",
     "intent": "product"
   }
   ```
7. **Server sends TTS audio** as binary WebSocket frame.
8. Either side may close the connection.

**Error Messages:**

```json
{ "type": "error", "detail": "Authentication required" }
```

| Close Code | Description           |
| ---------- | --------------------- |
| 4001       | Authentication failed |

---

## Product Endpoint

### Get Product

```
GET /api/products/{product_id}
```

Returns product details for front-end card rendering. No authentication required.

**Path Parameters:**

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `product_id` | string | The product identifier |

**Response:** `200 OK`

```json
{
  "id": "string",
  "name": "Product Name",
  "category": "Electronics",
  "price": 29.99,
  "description": "Product description text",
  "image_url": "https://...",
  "attributes": {}
}
```

| Field         | Type         | Description                     |
| ------------- | ------------ | ------------------------------- |
| `id`          | string       | Product identifier              |
| `name`        | string       | Product display name            |
| `category`    | string       | Product category                |
| `price`       | float        | Price in default currency       |
| `description` | string       | Product description             |
| `image_url`   | string\|null | Product image URL               |
| `attributes`  | object       | Additional key-value attributes |

**Errors:**

| Status | Description       |
| ------ | ----------------- |
| 404    | Product not found |

---

## Health Probes

### Liveness Probe

```
GET /api/health
```

Returns OK if the API process is running. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Readiness Probe

```
GET /api/ready
```

Returns OK when all dependencies (Cosmos DB) are connected. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ready",
  "version": "0.1.0"
}
```

If Cosmos DB connectivity fails, returns:

```json
{
  "status": "degraded",
  "version": "0.1.0"
}
```

---

## Data Models

### Domain Entities (Cosmos DB via `sas-cosmosdb`)

| Entity        | Container       | Partition Key | Description                    |
| ------------- | --------------- | ------------- | ------------------------------ |
| `ChatSession` | `chat-sessions` | `id`          | User chat session              |
| `ChatMessage` | `chat-messages` | `session_id`  | Single conversation turn       |
| `UserProfile` | `user-profiles` | `id`          | User profile (Entra ID linked) |
| `Product`     | `products`      | `id`          | Product catalog entry          |

### Enumerations

| Enum          | Values                                     | Description                  |
| ------------- | ------------------------------------------ | ---------------------------- |
| `Intent`      | `product`, `policy`, `general`             | Intent classification result |
| `Modality`    | `text`, `voice`, `mixed`                   | Communication modality       |
| `VoiceMode`   | `full_voice`, `voice_in_only`, `text_only` | Voice interaction mode       |
| `MessageRole` | `user`, `assistant`, `system`              | Chat message role            |

---

## Error Response Format

All HTTP errors follow the FastAPI standard format:

```json
{
  "detail": "Human-readable error message"
}
```

---

## Changelog

| Date       | Version | Description                              |
| ---------- | ------- | ---------------------------------------- |
| 2026-03-16 | 0.1.0   | Initial API documentation for v1 release |
