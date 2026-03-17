import { useCallback, useRef, useState } from "react";
import type { VoiceMode } from "../types";

interface UseVoiceOptions {
    onTranscription?: (text: string) => void;
    onAgentResponse?: (text: string, agent: string) => void;
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
    const [isConnecting, setIsConnecting] = useState(false);
    const [transcript, setTranscript] = useState("");
    const wsRef = useRef<WebSocket | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const audioCtxCaptureRef = useRef<AudioContext | null>(null);
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

            // Voice Live API sends raw PCM16 audio — convert to float32 for Web Audio API
            const int16 = new Int16Array(audioData);
            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) {
                float32[i] = (int16[i] ?? 0) / 32768;
            }

            const buffer = ctx.createBuffer(1, float32.length, 24000);
            buffer.getChannelData(0).set(float32);

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
            setIsConnecting(true);
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
                        options.onAgentResponse?.(data["text"], data["agent"] ?? "chat");
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
                streamRef.current = stream;

                // Use Web Audio API to capture raw PCM16 (Voice Live API requires PCM16 @ 24kHz)
                const audioCtx = new AudioContext({ sampleRate: 24000 });
                audioCtxCaptureRef.current = audioCtx;
                const source = audioCtx.createMediaStreamSource(stream);

                // ScriptProcessorNode to get raw float samples and convert to PCM16
                const processor = audioCtx.createScriptProcessor(4096, 1, 1);
                processor.onaudioprocess = (e: AudioProcessingEvent) => {
                    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
                    const float32 = e.inputBuffer.getChannelData(0);
                    // Convert float32 [-1,1] to int16
                    const pcm16 = new Int16Array(float32.length);
                    for (let i = 0; i < float32.length; i++) {
                        const s = Math.max(-1, Math.min(1, float32[i]!));
                        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
                    }
                    wsRef.current.send(pcm16.buffer);
                };

                source.connect(processor);
                processor.connect(audioCtx.destination);

                setIsListening(true);
                setIsConnecting(false);
                setVoiceMode("full_voice");
            } catch {
                ws.close();
                wsRef.current = null;
                setIsConnecting(false);
                options.onError?.("Microphone access denied");
            }
        },
        [playNextAudio, options],
    );

    const stopListening = useCallback(() => {
        if (audioCtxCaptureRef.current) {
            void audioCtxCaptureRef.current.close();
            audioCtxCaptureRef.current = null;
        }
        streamRef.current?.getTracks().forEach((t: MediaStreamTrack) => t.stop());
        streamRef.current = null;

        wsRef.current?.close();
        wsRef.current = null;

        audioQueueRef.current = [];
        isPlayingRef.current = false;
        setIsListening(false);
        setVoiceMode("text_only");
        setTranscript("");
    }, []);

    return { voiceMode, isListening, isConnecting, transcript, startListening, stopListening };
}
