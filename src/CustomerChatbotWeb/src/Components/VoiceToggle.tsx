import type { VoiceMode } from "../types";

interface VoiceToggleProps {
  voiceMode: VoiceMode;
  isListening: boolean;
  isConnecting: boolean;
  onToggle: () => void;
}

/**
 * Voice mode toggle button with 3 states: Start, Connecting, End.
 */
export function VoiceToggle({ voiceMode, isListening, isConnecting, onToggle }: VoiceToggleProps) {
  if (isConnecting) {
    return (
      <button className="voice-toggle connecting" disabled>
        ⏳ Connecting...
      </button>
    );
  }

  const isActive = voiceMode !== "text_only" || isListening;

  return (
    <button
      className={`voice-toggle ${isActive ? "listening" : ""}`}
      onClick={onToggle}
      aria-label={isActive ? "End voice conversation" : "Start voice conversation"}
      title={isActive ? "Click to end voice mode" : "Click to start voice mode"}
    >
      {isActive ? "🔴 End Voice" : "🎤 Start Voice"}
    </button>
  );
}
