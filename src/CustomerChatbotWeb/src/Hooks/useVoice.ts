import { useCallback, useRef, useState } from "react";
import type { VoiceMode } from "../types";

interface UseVoiceOptions {
    onTranscription?: (text: string) => void;
    onAgentResponse?: (text: string) => void;
    onError?: (error: string) => void;
}

const API_WS_BASE = import.meta.env.VITE_API_BASE_URL
    ? import.meta.env.VITE_API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
    : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;

/**
 * Voice hook — manages microphone input and WebSocket voice streaming
 * via Azure Voice Live API relay.
 */
export function useVoice(options: UseVoiceOptions = {}) {
    const [voiceMode, setVoiceMode] = useState<VoiceMode>("text_only");
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState("");
    const wsRef = useRef<WebSocket | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const audioQueueRef = useRef<ArrayBuffer[]>([]);
    const isPlayingRef = useRef(false);

    const playNextAudio = useCallback(async () => {
        if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
        isPlayingRef.current = true;

        const audioData = audioQueueRef.current.shift();
        if (!audioData || audioData.byteLength === 0) {
            isPlayingRef.current = false;
            return;
        }

        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new AudioContext({ sampleRate: 24000 });
            }
            const ctx = audioContextRef.current;
            const buffer = await ctx.decodeAudioData(audioData.slice(0));
            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);
            source.onended = () => {
                isPlayingRef.current = false;
                void playNextAudio();
            };
            source.start();
        } catch {
            isPlayingRef.current = false;
            void playNextAudio();
        }
    }, []);

    const startListening = useCallback(
        async (sessionId: string, accessToken: string) => {
            const ws = new WebSocket(`${API_WS_BASE}/api/voice/stream`);

            ws.onopen = () => {
                ws.send(JSON.stringify({ type: "auth", token: accessToken, session_id: sessionId }));
            };

            ws.onmessage = (event: MessageEvent) => {
                if (typeof event.data === "string") {
                    const data = JSON.parse(event.data) as Record<string, string>;
                    const type = data["type"];

                    if (type === "transcription" && data["text"]) {
                        setTranscript(data["text"]);
                        options.onTranscription?.(data["text"]);
                    } else if (type === "assistant_transcript" && data["text"]) {
                        // Streaming assistant text
                    } else if (type === "response_done" && data["text"]) {
                        options.onAgentResponse?.(data["text"]);
                    } else if (type === "error" && data["detail"]) {
                        options.onError?.(data["detail"]);
                    }
                } else if (event.data instanceof Blob) {
                    void event.data.arrayBuffer().then((buf: ArrayBuffer) => {
                        audioQueueRef.current.push(buf);
                        void playNextAudio();
                    });
                }
            };

            ws.onerror = () => {
                options.onError?.("Voice connection error");
            };

            wsRef.current = ws;

            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: { sampleRate: 24000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
                });
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
                options.onError?.("Microphone access denied");
            }
        },
        [playNextAudio, options],
    );

    const stopListening = useCallback(() => {
        mediaRecorderRef.current?.stop();
        mediaRecorderRef.current?.stream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
        mediaRecorderRef.current = null;

        wsRef.current?.close();
        wsRef.current = null;

        audioQueueRef.current = [];
        isPlayingRef.current = false;
        setIsListening(false);
        setTranscript("");
    }, []);

    const toggleVoiceMode = useCallback(() => {
        setVoiceMode((prev: VoiceMode) => (prev === "text_only" ? "full_voice" : "text_only"));
    }, []);

    return { voiceMode, isListening, transcript, startListening, stopListening, toggleVoiceMode };
}
