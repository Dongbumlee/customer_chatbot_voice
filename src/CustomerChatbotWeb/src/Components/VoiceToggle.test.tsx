import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { VoiceToggle } from "./VoiceToggle";

describe("VoiceToggle", () => {
  it("renders 'Start Voice' when mode is text_only", () => {
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} isConnecting={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByText("🎤 Start Voice")).toBeInTheDocument();
  });

  it("renders 'End Voice' when mode is full_voice and listening", () => {
    render(
      <VoiceToggle voiceMode="full_voice" isListening={true} isConnecting={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByText("🔴 End Voice")).toBeInTheDocument();
  });

  it("renders 'Connecting...' when connecting", () => {
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} isConnecting={true} onToggle={vi.fn()} />,
    );
    expect(screen.getByText("⏳ Connecting...")).toBeInTheDocument();
  });

  it("calls onToggle when clicked", () => {
    const onToggle = vi.fn();
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} isConnecting={false} onToggle={onToggle} />,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("has correct aria-label for text mode", () => {
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} isConnecting={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByLabelText("Start voice conversation")).toBeInTheDocument();
  });

  it("has correct aria-label for voice mode", () => {
    render(
      <VoiceToggle voiceMode="full_voice" isListening={true} isConnecting={false} onToggle={vi.fn()} />,
    );
    expect(screen.getByLabelText("End voice conversation")).toBeInTheDocument();
  });

  it("disables button when connecting", () => {
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} isConnecting={true} onToggle={vi.fn()} />,
    );
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies listening CSS class when active", () => {
    // Arrange & Act
    const { container } = render(
      <VoiceToggle voiceMode="full_voice" isListening={true} onToggle={vi.fn()} />,
    );

    // Assert
    const button = container.querySelector(".voice-toggle.listening");
    expect(button).not.toBeNull();
  });
});
