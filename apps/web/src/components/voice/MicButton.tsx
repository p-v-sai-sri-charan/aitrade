import { useCallback, useEffect, useState } from "react";
import { voiceService } from "../../services/voice/voiceService";
import type { VoiceRecognitionLanguage } from "@vaanitrade/voice";

interface MicButtonProps {
  language: VoiceRecognitionLanguage;
  disabled?: boolean;
  onListeningChange?: (isListening: boolean) => void;
  onInterimTranscript?: (text: string) => void;
  onFinalTranscript?: (text: string) => void;
  onError?: (message: string) => void;
}

export function MicButton({
  language,
  disabled,
  onListeningChange,
  onInterimTranscript,
  onFinalTranscript,
  onError,
}: MicButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [supported] = useState(() => voiceService.isSupported());

  useEffect(() => {
    voiceService.configure({
      onListeningStateChange: (listening) => {
        setIsListening(listening);
        onListeningChange?.(listening);
      },
      onInterimTranscript: (text) => onInterimTranscript?.(text),
      onFinalTranscript: (text) => onFinalTranscript?.(text),
      onError: (error) => onError?.(error.message),
    });
  }, [onListeningChange, onInterimTranscript, onFinalTranscript, onError]);

  const handleClick = useCallback(async () => {
    if (isListening) {
      await voiceService.stopListening();
      return;
    }
    const granted = await voiceService.requestPermission();
    if (!granted && supported) {
      // Some browsers only expose permission state via the recognition
      // start() error path; try anyway rather than blocking the user.
    }
    await voiceService.startListening(language);
  }, [isListening, language, supported]);

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || !supported}
        aria-pressed={isListening}
        aria-label={isListening ? "Stop listening" : "Start voice command"}
        className={`flex h-24 w-24 items-center justify-center rounded-full text-white shadow-lg transition disabled:cursor-not-allowed disabled:opacity-50 ${
          isListening ? "animate-pulse bg-red-500" : "bg-brand-600 hover:bg-brand-700"
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="h-10 w-10">
          <rect x="9" y="3" width="6" height="11" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0M12 18v3" strokeLinecap="round" />
        </svg>
      </button>
      <p className="text-sm text-slate-500">
        {!supported
          ? "Voice input isn't supported in this browser -- type your command instead."
          : isListening
            ? "Listening... tap to stop"
            : "Tap to speak"}
      </p>
    </div>
  );
}
