import type {
  VoiceRecognitionLanguage,
  VoiceService,
  VoiceServiceEvents,
} from "./VoiceService";

// Minimal ambient typing for the (still non-standard) Web Speech API so we
// don't need to pull in a full DOM lib fork. Real browsers that support it
// expose these on `window`.
interface SpeechRecognitionResultLike {
  isFinal: boolean;
  0: { transcript: string };
}
interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

function getSpeechRecognitionCtor(): SpeechRecognitionConstructor | undefined {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

/**
 * Browser fallback implementation of VoiceService using the Web Speech API
 * (SpeechRecognition + SpeechSynthesis). This is intentionally the ONLY
 * place in the codebase that touches `window.speechSynthesis` /
 * `SpeechRecognition` directly.
 */
export class WebSpeechVoiceService implements VoiceService {
  private recognition: SpeechRecognitionLike | null = null;
  private events: VoiceServiceEvents = {};
  private finalTranscript = "";
  private listening = false;

  isSupported(): boolean {
    return (
      typeof window !== "undefined" &&
      (!!getSpeechRecognitionCtor() ||
        typeof window.speechSynthesis !== "undefined")
    );
  }

  configure(events: VoiceServiceEvents): void {
    this.events = events;
  }

  async requestPermission(): Promise<boolean> {
    if (typeof navigator === "undefined" || !navigator.mediaDevices) {
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      return true;
    } catch {
      this.events.onError?.({
        code: "PERMISSION_DENIED",
        message: "Microphone permission was denied.",
      });
      return false;
    }
  }

  async startListening(language: VoiceRecognitionLanguage = "en-IN"): Promise<void> {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      this.events.onError?.({
        code: "NOT_SUPPORTED",
        message: "Speech recognition is not supported in this browser.",
      });
      return;
    }

    this.finalTranscript = "";
    const recognition = new Ctor();
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        if (result.isFinal) {
          this.finalTranscript += transcript + " ";
          this.events.onFinalTranscript?.(this.finalTranscript.trim());
        } else {
          interim += transcript;
        }
      }
      if (interim) {
        this.events.onInterimTranscript?.(interim);
      }
    };

    recognition.onerror = (event) => {
      const code =
        event.error === "not-allowed" || event.error === "permission-denied"
          ? "PERMISSION_DENIED"
          : event.error === "no-speech"
            ? "NO_SPEECH"
            : event.error === "network"
              ? "NETWORK"
              : event.error === "aborted"
                ? "ABORTED"
                : "UNKNOWN";
      this.events.onError?.({ code, message: `Speech recognition error: ${event.error}` });
    };

    recognition.onend = () => {
      this.listening = false;
      this.events.onListeningStateChange?.(false);
    };

    this.recognition = recognition;
    this.listening = true;
    this.events.onListeningStateChange?.(true);
    recognition.start();
  }

  async stopListening(): Promise<string> {
    if (this.recognition && this.listening) {
      this.recognition.stop();
    }
    this.listening = false;
    return this.finalTranscript.trim();
  }

  async speak(text: string, language: VoiceRecognitionLanguage = "en-IN"): Promise<void> {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      return;
    }
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    });
  }

  cancelSpeech(): void {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }
}
