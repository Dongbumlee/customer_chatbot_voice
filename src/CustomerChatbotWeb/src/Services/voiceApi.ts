/**
 * Voice API service — manages WebSocket connection for voice streaming.
 */

const WS_BASE = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;

/**
 * Create a WebSocket connection for voice streaming.
 * @param accessToken - Bearer token for authentication.
 * @param onTranscription - Callback when transcribed text is received.
 * @param onAudio - Callback when TTS audio chunk is received.
 */
export function connectVoiceStream(
    accessToken: string,
    onTranscription: (text: string) => void,
    onAudio: (audio: ArrayBuffer) => void,
): WebSocket {
    const ws = new WebSocket(`${WS_BASE}/api/voice/stream`);

    ws.onopen = () => {
        // Send auth token as first message
        ws.send(JSON.stringify({ type: "auth", token: accessToken }));
    };

    ws.onmessage = (event) => {
        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);
            if (data.type === "transcription") {
                onTranscription(data.text);
            }
        } else if (event.data instanceof ArrayBuffer) {
            onAudio(event.data);
        }
    };

    return ws;
}
