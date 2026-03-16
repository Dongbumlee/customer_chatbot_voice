import type { VoiceMode } from "../types";

interface VoiceToggleProps {
  voiceMode: VoiceMode;
  isListening: boolean;
  onToggle: () => void;
}

/**
 * Voice mode toggle button.
 * When off: shows "Start Voice". When on: shows "End Voice" with pulsing indicator.
 */
export function VoiceToggle({ voiceMode, isListening, onToggle }: VoiceToggleProps) {
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
