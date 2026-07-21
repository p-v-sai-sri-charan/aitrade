export type VoiceRecognitionLanguage = "hi-IN" | "en-IN";

export interface VoiceServiceEvents {
  onInterimTranscript?: (transcript: string) => void;
  onFinalTranscript?: (transcript: string) => void;
  onError?: (error: VoiceServiceError) => void;
  onListeningStateChange?: (isListening: boolean) => void;
}

export interface VoiceServiceError {
  code:
    | "NOT_SUPPORTED"
    | "PERMISSION_DENIED"
    | "NO_SPEECH"
    | "NETWORK"
    | "ABORTED"
    | "UNKNOWN";
  message: string;
}

/**
 * Isolates microphone / speech-to-text / text-to-speech behind an
 * interface so the UI never depends on a specific browser API. A
 * Capacitor or React Native implementation can be swapped in later
 * without touching any component.
 */
export interface VoiceService {
  isSupported(): boolean;
  requestPermission(): Promise<boolean>;
  /** Begin listening. Interim/final results arrive via the events passed to configure(). */
  startListening(language?: VoiceRecognitionLanguage): Promise<void>;
  /** Stop listening and resolve with the final transcript captured. */
  stopListening(): Promise<string>;
  /** Speak text aloud (used for order summaries / confirmations). */
  speak(text: string, language?: VoiceRecognitionLanguage): Promise<void>;
  cancelSpeech(): void;
  configure(events: VoiceServiceEvents): void;
}
