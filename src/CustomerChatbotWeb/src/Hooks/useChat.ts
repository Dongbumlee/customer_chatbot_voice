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

    const startSession = useCallback(async (accessToken: string) => {
        const newSession = await createSession(accessToken);
        setSession(newSession);
        setMessages([]);
        return newSession;
    }, []);

    const send = useCallback(
        async (content: string, accessToken: string) => {
            if (!session) return;
            setIsLoading(true);
            try {
                const response = await sendMessage(
                    { session_id: session.session_id, content, modality: "text" },
                    accessToken,
                );
                setMessages((prev) => [
                    ...prev,
                    {
                        message_id: crypto.randomUUID(),
                        session_id: session.session_id,
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
            } finally {
                setIsLoading(false);
            }
        },
        [session],
    );

    return { messages, session, isLoading, startSession, send };
}
