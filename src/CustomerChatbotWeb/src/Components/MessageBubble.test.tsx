import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "./MessageBubble";
import type { ChatMessage } from "../types";

describe("MessageBubble", () => {
  const userMessage: ChatMessage = {
    message_id: "m-001",
    session_id: "s-001",
    content: "Hello!",
    role: "user",
    modality: "text",
    timestamp: "2026-01-01T00:00:00Z",
  };

  const assistantMessage: ChatMessage = {
    message_id: "m-002",
    session_id: "s-001",
    content: "Hi! How can I help?",
    role: "assistant",
    modality: "text",
    agent: "chat",
    timestamp: "2026-01-01T00:00:01Z",
  };

  it("renders user message content", () => {
    // Arrange & Act
    render(<MessageBubble message={userMessage} />);

    // Assert
    expect(screen.getByText("Hello!")).toBeInTheDocument();
  });

  it("applies user style class for user messages", () => {
    // Arrange & Act
    const { container } = render(<MessageBubble message={userMessage} />);

    // Assert
    const bubble = container.querySelector(".message-bubble--user");
    expect(bubble).not.toBeNull();
  });

  it("applies assistant style class for assistant messages", () => {
    // Arrange & Act
    const { container } = render(<MessageBubble message={assistantMessage} />);

    // Assert
    const bubble = container.querySelector(".message-bubble--assistant");
    expect(bubble).not.toBeNull();
  });

  it("renders agent label for assistant messages", () => {
    // Arrange & Act
    render(<MessageBubble message={assistantMessage} />);

    // Assert
    expect(screen.getByText("chat")).toBeInTheDocument();
  });

  it("does not render agent label for user messages", () => {
    // Arrange & Act
    render(<MessageBubble message={userMessage} />);

    // Assert
    expect(screen.queryByText("chat")).not.toBeInTheDocument();
  });

  it("shows voice indicator for voice messages", () => {
    // Arrange
    const voiceMessage: ChatMessage = {
      ...userMessage,
      modality: "voice",
    };

    // Act
    render(<MessageBubble message={voiceMessage} />);

    // Assert
    expect(screen.getByTitle("Voice message")).toBeInTheDocument();
  });

  it("does not show voice indicator for text messages", () => {
    // Arrange & Act
    render(<MessageBubble message={userMessage} />);

    // Assert
    expect(screen.queryByTitle("Voice message")).not.toBeInTheDocument();
  });

  it("renders product cards when metadata includes them", () => {
    // Arrange
    const messageWithProducts: ChatMessage = {
      ...assistantMessage,
      metadata: {
        product_cards: [
          {
            id: "p1",
            name: "Widget",
            category: "tools",
            price: 9.99,
            description: "A useful widget",
            attributes: {},
          },
        ],
      },
    };

    // Act
    render(<MessageBubble message={messageWithProducts} />);

    // Assert
    expect(screen.getByText("Widget")).toBeInTheDocument();
    expect(screen.getByText("$9.99")).toBeInTheDocument();
  });

  it("does not render product cards when metadata is empty", () => {
    // Arrange & Act
    const { container } = render(<MessageBubble message={assistantMessage} />);

    // Assert
    expect(container.querySelector(".message-bubble__products")).toBeNull();
  });
});
