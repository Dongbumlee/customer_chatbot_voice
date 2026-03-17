import { useCallback, useRef, useState } from "react";
import { sendMessageStream, createSession } from "../Services/chatApi";
import type { ChatMessage, ChatSession } from "../types";

/**
 * Chat hook — manages chat session state and message sending.
 */
export function useChat() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [session, setSession] = useState<ChatSession | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const streamingMsgRef = useRef<string>("");

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

            // Add user message immediately
            const userMsgId = crypto.randomUUID();
            setMessages((prev) => [
                ...prev,
                {
                    message_id: userMsgId,
                    session_id: activeSession.session_id,
                    content,
                    role: "user",
                    modality: "text",
                    timestamp: new Date().toISOString(),
                },
            ]);

            // Add empty assistant message that will stream in
            const assistantMsgId = crypto.randomUUID();
            streamingMsgRef.current = "";
            let agentName = "";
            let msgMetadata: Record<string, unknown> | undefined;

            setMessages((prev) => [
                ...prev,
                {
                    message_id: assistantMsgId,
                    session_id: activeSession.session_id,
                    content: "",
                    role: "assistant",
                    modality: "text",
                    timestamp: new Date().toISOString(),
                },
            ]);

            try {
                await sendMessageStream(
                    { session_id: activeSession.session_id, content, modality: "text" },
                    accessToken,
                    {
                        onMeta: (agent) => {
                            agentName = agent;
                        },
                        onChunk: (text) => {
                            streamingMsgRef.current += text;
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.message_id === assistantMsgId
                                        ? { ...m, content: streamingMsgRef.current, agent: agentName || undefined }
                                        : m,
                                ),
                            );
                        },
                        onProductCards: (cards) => {
                            msgMetadata = { ...msgMetadata, product_cards: cards };
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.message_id === assistantMsgId
                                        ? { ...m, metadata: msgMetadata }
                                        : m,
                                ),
                            );
                        },
                        onMetadata: (data) => {
                            msgMetadata = { ...msgMetadata, ...data };
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.message_id === assistantMsgId
                                        ? { ...m, metadata: msgMetadata }
                                        : m,
                                ),
                            );
                        },
                        onError: (err) => setError(err),
                    },
                );
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
