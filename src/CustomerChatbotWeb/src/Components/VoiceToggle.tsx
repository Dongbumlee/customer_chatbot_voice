import type { VoiceMode } from "../types";

interface VoiceToggleProps {
  voiceMode: VoiceMode;
  isListening: boolean;
  onToggle: () => void;
}

/**
 * Voice mode toggle button — switches between text and voice input.
 * Shows microphone animation when actively listening.
 */
export function VoiceToggle({ voiceMode, isListening, onToggle }: VoiceToggleProps) {
  return (
    <button
      className={`voice-toggle ${isListening ? "listening" : ""}`}
      onClick={onToggle}
      aria-label={voiceMode === "text_only" ? "Enable voice mode" : "Disable voice mode"}
      title={voiceMode === "text_only" ? "Enable voice mode" : "Disable voice mode"}
    >
      {isListening ? "🎙️ Listening..." : voiceMode === "text_only" ? "🎤 Voice Off" : "🎤 Voice On"}
    </button>
  );
}
