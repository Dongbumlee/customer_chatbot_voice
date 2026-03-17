import type { ChatMessage } from "../types";
import { ProductCard } from "./ProductCard";
import { PolicySources } from "./PolicySources";
import type { Product } from "../types";

const AGENT_ICONS: Record<string, string> = {
  chat: "🤖",
  product: "🛍️",
  policy: "📋",
};

interface PolicySource {
  name: string;
  reference?: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Message bubble — renders a single chat message.
 * Shows different styles for user vs assistant messages.
 * Renders inline product cards when metadata includes them.
 * Renders policy sources when metadata includes sources.
 * Displays agent-specific icons for assistant messages.
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const productCards = (message.metadata?.product_cards as Product[] | undefined) ?? [];
  const policySources = (message.metadata?.sources as PolicySource[] | undefined) ?? [];
  const agentIcon = message.agent ? AGENT_ICONS[message.agent] ?? "🤖" : undefined;

  return (
    <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
      {message.modality === "voice" && (
        <span className="message-bubble__voice-indicator" title="Voice message">
          🎙️
        </span>
      )}
      {!isUser && agentIcon && (
        <span className="message-bubble__agent-icon" title={message.agent}>
          {agentIcon}
        </span>
      )}
      <div className="message-bubble__content">{message.content}</div>
      {message.agent && (
        <span className="message-bubble__agent">{message.agent}</span>
      )}
      {productCards.length > 0 && (
        <div className="message-bubble__products">
          {productCards.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
      {policySources.length > 0 && (
        <PolicySources sources={policySources} />
      )}
    </div>
  );
}
