import { useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { VoiceToggle } from "./VoiceToggle";
import { useAuth } from "../Hooks/useAuth";
import { useChat } from "../Hooks/useChat";
import { useVoice } from "../Hooks/useVoice";

/**
 * Main chat panel — displays messages and input controls.
 */
export function ChatPanel() {
  const [input, setInput] = useState("");
  const { getAccessToken } = useAuth();
  const { messages, session, isLoading, startSession, send } = useChat();
  const { voiceMode, isListening, toggleVoiceMode } = useVoice();

  const handleSend = async () => {
    if (!input.trim()) return;
    const token = await getAccessToken();
    if (!session) {
      await startSession(token);
    }
    await send(input, token);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>Customer Chatbot</h2>
        <VoiceToggle
          voiceMode={voiceMode}
          isListening={isListening}
          onToggle={toggleVoiceMode}
        />
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <MessageBubble key={msg.message_id} message={msg} />
        ))}
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
