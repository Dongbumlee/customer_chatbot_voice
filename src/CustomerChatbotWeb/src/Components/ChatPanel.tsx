import { useCallback, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { VoiceToggle } from "./VoiceToggle";
import { useAuth } from "../Hooks/useAuth";
import { useChat } from "../Hooks/useChat";
import { useVoice } from "../Hooks/useVoice";
import type { ChatMessage } from "../types";

/**
 * Main chat panel — displays messages and input controls.
 */
export function ChatPanel() {
  const [input, setInput] = useState("");
  const { getAccessToken } = useAuth();
  const { messages, session, isLoading, error, startSession, send } = useChat();
  const [voiceMessages, setVoiceMessages] = useState<ChatMessage[]>([]);

  const addVoiceMessage = useCallback((role: "user" | "assistant", content: string) => {
    setVoiceMessages((prev) => [
      ...prev,
      {
        message_id: crypto.randomUUID(),
        session_id: "voice",
        content,
        role,
        modality: "voice",
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const [voiceError, setVoiceError] = useState<string | null>(null);

  const {
    voiceMode,
    isListening,
    transcript,
    startListening,
    stopListening,
    toggleVoiceMode,
  } = useVoice({
    onTranscription: (text) => addVoiceMessage("user", text),
    onAgentResponse: (text) => addVoiceMessage("assistant", text),
    onError: (err) => setVoiceError(err),
  });

  const handleSend = async () => {
    if (!input.trim()) return;
    const token = await getAccessToken();
    let activeSession = session;
    if (!activeSession) {
      activeSession = await startSession(token);
    }
    await send(input, token, activeSession);
    setInput("");
  };

  const handleVoiceToggle = async () => {
    if (isListening) {
      stopListening();
    } else {
      const token = await getAccessToken();
      let activeSession = session;
      if (!activeSession) {
        activeSession = await startSession(token);
      }
      await startListening(activeSession.session_id, token);
    }
    toggleVoiceMode();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const allMessages = [...messages, ...voiceMessages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>Customer Chatbot</h2>
        <VoiceToggle
          voiceMode={voiceMode}
          isListening={isListening}
          onToggle={handleVoiceToggle}
        />
      </div>

      <div className="chat-messages">
        {(error || voiceError) && (
          <div className="error-banner">
            {error || voiceError}
          </div>
        )}
        {allMessages.map((msg) => (
          <MessageBubble key={msg.message_id} message={msg} />
        ))}
        {isListening && (
          <div className="voice-status-bar">
            <span className="voice-pulse">🔴</span>
            <span>Voice mode active — just speak naturally, the AI will respond automatically</span>
            {transcript && <span className="voice-transcript">🎙️ {transcript}</span>}
          </div>
        )}
        {isLoading && <div className="typing-indicator">Thinking...</div>}
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
