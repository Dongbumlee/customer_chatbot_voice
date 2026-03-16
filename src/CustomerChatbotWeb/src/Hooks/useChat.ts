import { useCallback, useState } from "react";
import { sendMessage, createSession } from "../Services/chatApi";
import type { ChatMessage, ChatSession } from "../types";

/**
 * Chat hook — manages chat session state and message sending.
 */
export function useChat() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [session, setSession] = useState<ChatSession | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const startSession = useCallback(async (accessToken: string) => {
        try {
            setError(null);
            const newSession = await createSession(accessToken);
            setSession(newSession);
            setMessages([]);
            return newSession;
        } catch (e) {
            const msg = e instanceof Error ? e.message : "Failed to create session";
            setError(msg);
            throw e;
        }
    }, []);

    const send = useCallback(
        async (content: string, accessToken: string, sessionOverride?: ChatSession) => {
            const activeSession = sessionOverride ?? session;
            if (!activeSession) return;
            setIsLoading(true);
            setError(null);
            try {
                const response = await sendMessage(
                    { session_id: activeSession.session_id, content, modality: "text" },
                    accessToken,
                );
                setMessages((prev) => [
                    ...prev,
                    {
                        message_id: crypto.randomUUID(),
                        session_id: activeSession.session_id,
                        content,
                        role: "user",
                        modality: "text",
                        timestamp: new Date().toISOString(),
                    },
                    {
                        message_id: response.message_id,
                        session_id: response.session_id,
                        content: response.content,
                        role: "assistant",
                        modality: "text",
                        agent: response.agent ?? undefined,
                        metadata: response.metadata ?? undefined,
                        timestamp: response.timestamp,
                    },
                ]);
            } catch (e) {
                const msg = e instanceof Error ? e.message : "Failed to send message";
                setError(msg);
            } finally {
                setIsLoading(false);
            }
        },
        [session],
    );

    return { messages, session, isLoading, error, startSession, send };
}
