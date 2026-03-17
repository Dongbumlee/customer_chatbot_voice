import type { ChatMessage as ChatMessageType, ChatSession } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL}/api`
    : "/api";

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
 * Callback type for streaming events.
 */
export interface StreamCallbacks {
    onMeta?: (agent: string, intent: string) => void;
    onChunk?: (text: string) => void;
    onProductCards?: (cards: Record<string, unknown>[]) => void;
    onMetadata?: (data: Record<string, unknown>) => void;
    onDone?: () => void;
    onError?: (error: string) => void;
}

/**
 * Send a message and stream the response via SSE.
 */
export async function sendMessageStream(
    request: SendMessageRequest,
    accessToken: string,
    callbacks: StreamCallbacks,
): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/message/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        callbacks.onError?.(`Chat API error: ${response.status}`);
        return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
        callbacks.onError?.("No response stream");
        return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = JSON.parse(line.slice(6)) as Record<string, unknown>;
            const type = data["type"] as string;

            if (type === "meta") {
                callbacks.onMeta?.(data["agent"] as string, data["intent"] as string);
            } else if (type === "chunk") {
                callbacks.onChunk?.(data["content"] as string);
            } else if (type === "product_cards") {
                callbacks.onProductCards?.(data["cards"] as Record<string, unknown>[]);
            } else if (type === "metadata") {
                callbacks.onMetadata?.(data["data"] as Record<string, unknown>);
            } else if (type === "done") {
                callbacks.onDone?.();
            }
        }
    }
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
