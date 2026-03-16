import type { ChatMessage } from "../types";
import { ProductCard } from "./ProductCard";
import type { Product } from "../types";

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Message bubble — renders a single chat message.
 * Shows different styles for user vs assistant messages.
 * Renders inline product cards when metadata includes them.
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const productCards = (message.metadata?.product_cards as Product[] | undefined) ?? [];

  return (
    <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
      {message.modality === "voice" && (
        <span className="message-bubble__voice-indicator" title="Voice message">
          🎙️
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
    </div>
  );
}
