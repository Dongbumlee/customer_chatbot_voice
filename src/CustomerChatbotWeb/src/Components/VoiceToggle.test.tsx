import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { VoiceToggle } from "./VoiceToggle";

describe("VoiceToggle", () => {
  it("renders 'Voice Off' when mode is text_only", () => {
    // Arrange & Act
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} onToggle={vi.fn()} />,
    );

    // Assert
    expect(screen.getByText("🎤 Voice Off")).toBeInTheDocument();
  });

  it("renders 'Voice On' when mode is full_voice and not listening", () => {
    // Arrange & Act
    render(
      <VoiceToggle voiceMode="full_voice" isListening={false} onToggle={vi.fn()} />,
    );

    // Assert
    expect(screen.getByText("🎤 Voice On")).toBeInTheDocument();
  });

  it("renders 'Listening...' when actively listening", () => {
    // Arrange & Act
    render(
      <VoiceToggle voiceMode="full_voice" isListening={true} onToggle={vi.fn()} />,
    );

    // Assert
    expect(screen.getByText("🎙️ Listening...")).toBeInTheDocument();
  });

  it("calls onToggle when clicked", () => {
    // Arrange
    const onToggle = vi.fn();
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} onToggle={onToggle} />,
    );

    // Act
    fireEvent.click(screen.getByRole("button"));

    // Assert
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("has correct aria-label for text mode", () => {
    // Arrange & Act
    render(
      <VoiceToggle voiceMode="text_only" isListening={false} onToggle={vi.fn()} />,
    );

    // Assert
    expect(screen.getByLabelText("Enable voice mode")).toBeInTheDocument();
  });

  it("has correct aria-label for voice mode", () => {
    // Arrange & Act
    render(
      <VoiceToggle voiceMode="full_voice" isListening={false} onToggle={vi.fn()} />,
    );

    // Assert
    expect(screen.getByLabelText("Disable voice mode")).toBeInTheDocument();
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
