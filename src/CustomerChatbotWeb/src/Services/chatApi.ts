import type { ChatMessage as ChatMessageType, ChatSession } from "../types";

const API_BASE = "/api";

interface SendMessageRequest {
    session_id: string;
    content: string;
    modality: "text" | "voice";
}

interface ChatMessageResponse {
    message_id: string;
    session_id: string;
    content: string;
    agent: string | null;
    metadata: Record<string, unknown> | null;
    timestamp: string;
}

/**
 * Send a chat message to the backend API.
 */
export async function sendMessage(
    request: SendMessageRequest,
    accessToken: string,
): Promise<ChatMessageResponse> {
    const response = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error(`Chat API error: ${response.status}`);
    return response.json();
}

/**
 * Create a new chat session.
 */
export async function createSession(accessToken: string): Promise<ChatSession> {
    const response = await fetch(`${API_BASE}/chat/session`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
    });
    if (!response.ok) throw new Error(`Session API error: ${response.status}`);
    return response.json();
}

/**
 * Fetch chat history for a session.
 */
export async function getSessionHistory(
    sessionId: string,
    accessToken: string,
): Promise<ChatMessageType[]> {
    const response = await fetch(`${API_BASE}/chat/session/${sessionId}/history`, {
        headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!response.ok) throw new Error(`History API error: ${response.status}`);
    return response.json();
}
