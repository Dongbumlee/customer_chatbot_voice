import { useCallback, useRef, useState } from "react";
import type { VoiceMode } from "../types";

interface UseVoiceOptions {
    onTranscription?: (text: string) => void;
    onAgentResponse?: (content: string, agent: string) => void;
}

/**
 * Voice hook — manages microphone input and WebSocket voice streaming.
 *
 * Connects to the backend WebSocket at `/api/voice/stream`, captures
 * microphone audio via MediaRecorder, streams binary frames to the
 * server, and plays back TTS audio responses via AudioContext.
 */
export function useVoice(options: UseVoiceOptions = {}) {
    const [voiceMode, setVoiceMode] = useState<VoiceMode>("text_only");
    const [isListening, setIsListening] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);

    const playAudio = useCallback(async (audioData: ArrayBuffer) => {
        if (!audioContextRef.current) {
            audioContextRef.current = new AudioContext();
        }
        const ctx = audioContextRef.current;
        const buffer = await ctx.decodeAudioData(audioData.slice(0));
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);
        source.start();
    }, []);

    const startListening = useCallback(
        async (sessionId: string, accessToken: string) => {
            const wsBase = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;
            const ws = new WebSocket(`${wsBase}/api/voice/stream`);

            ws.onopen = () => {
                ws.send(JSON.stringify({ type: "auth", token: accessToken, session_id: sessionId }));
            };

            ws.onmessage = (event: MessageEvent) => {
                if (typeof event.data === "string") {
                    const data = JSON.parse(event.data) as Record<string, string>;
                    if (data["type"] === "transcription" && data["text"]) {
                        options.onTranscription?.(data["text"]);
                    } else if (data["type"] === "response" && data["content"]) {
                        options.onAgentResponse?.(data["content"], data["agent"] ?? "unknown");
                    }
                } else if (event.data instanceof Blob) {
                    void event.data.arrayBuffer().then(playAudio);
                }
            };

            wsRef.current = ws;

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

                recorder.ondataavailable = (e: BlobEvent) => {
                    if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
                        void e.data.arrayBuffer().then((buf: ArrayBuffer) => wsRef.current?.send(buf));
                    }
                };

                recorder.start(250);
                mediaRecorderRef.current = recorder;
                setIsListening(true);
            } catch {
                ws.close();
                wsRef.current = null;
            }
        },
        [playAudio, options],
    );

    const stopListening = useCallback(() => {
        mediaRecorderRef.current?.stop();
        mediaRecorderRef.current?.stream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
        mediaRecorderRef.current = null;

        wsRef.current?.close();
        wsRef.current = null;

        setIsListening(false);
    }, []);

    const toggleVoiceMode = useCallback(() => {
        setVoiceMode((prev: VoiceMode) => (prev === "text_only" ? "full_voice" : "text_only"));
    }, []);

    return { voiceMode, isListening, startListening, stopListening, toggleVoiceMode };
}
