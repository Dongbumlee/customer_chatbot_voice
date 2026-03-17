import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ChatPanel } from "./ChatPanel";

// Mock all hooks used by ChatPanel
const mockSend = vi.fn();
const mockStartSession = vi.fn();
const mockGetAccessToken = vi.fn().mockResolvedValue("mock-token");
const mockToggleVoiceMode = vi.fn();
const mockStartListening = vi.fn();
const mockStopListening = vi.fn();

vi.mock("../Hooks/useAuth", () => ({
  useAuth: () => ({
    getAccessToken: mockGetAccessToken,
    login: vi.fn(),
    logout: vi.fn(),
    account: { username: "test@example.com" },
  }),
}));

vi.mock("../Hooks/useChat", () => ({
  useChat: () => ({
    messages: [
      {
        message_id: "m-001",
        session_id: "s-001",
        content: "Hello!",
        role: "user" as const,
        modality: "text" as const,
        timestamp: "2026-01-01T00:00:00Z",
      },
      {
        message_id: "m-002",
        session_id: "s-001",
        content: "Hi there! How can I help?",
        role: "assistant" as const,
        modality: "text" as const,
        agent: "chat",
        timestamp: "2026-01-01T00:00:01Z",
      },
    ],
    session: { session_id: "s-001", title: "Test", modality: "text", created_at: "", last_active_at: "", is_active: true },
    isLoading: false,
    error: null,
    startSession: mockStartSession,
    send: mockSend,
  }),
}));

vi.mock("../Hooks/useVoice", () => ({
  useVoice: () => ({
    voiceMode: "text_only",
    isListening: false,
    isConnecting: false,
    transcript: "",
    startListening: mockStartListening,
    stopListening: mockStopListening,
  }),
}));

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the chat header", () => {
    // Arrange & Act
    render(<ChatPanel />);

    // Assert
    expect(screen.getByText("Customer Chatbot")).toBeInTheDocument();
  });

  it("renders existing messages", () => {
    // Arrange & Act
    render(<ChatPanel />);

    // Assert
    expect(screen.getByText("Hello!")).toBeInTheDocument();
    expect(screen.getByText("Hi there! How can I help?")).toBeInTheDocument();
  });

  it("renders input field and send button", () => {
    // Arrange & Act
    render(<ChatPanel />);

    // Assert
    expect(screen.getByPlaceholderText("Type a message...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("disables send button when input is empty", () => {
    // Arrange & Act
    render(<ChatPanel />);

    // Assert
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it("enables send button when input has text", () => {
    // Arrange
    render(<ChatPanel />);
    const input = screen.getByPlaceholderText("Type a message...");

    // Act
    fireEvent.change(input, { target: { value: "Test message" } });

    // Assert
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeEnabled();
  });

  it("calls send on button click", async () => {
    // Arrange
    render(<ChatPanel />);
    const input = screen.getByPlaceholderText("Type a message...");

    // Act
    fireEvent.change(input, { target: { value: "Hello agent" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    // Assert
    await waitFor(() => {
      expect(mockSend).toHaveBeenCalledWith(
        "Hello agent",
        "mock-token",
        expect.objectContaining({ session_id: "s-001" }),
      );
    });
  });

  it("clears input after sending", async () => {
    // Arrange
    render(<ChatPanel />);
    const input = screen.getByPlaceholderText("Type a message...");

    // Act
    fireEvent.change(input, { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    // Assert
    await waitFor(() => {
      expect(input).toHaveValue("");
    });
  });

  it("renders voice toggle", () => {
    render(<ChatPanel />);
    expect(screen.getByText("🎤 Start Voice")).toBeInTheDocument();
  });
});
