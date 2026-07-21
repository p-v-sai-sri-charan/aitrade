import type { CommandLanguage } from "@vaanitrade/shared-types";

const LANGUAGE_LABELS: Record<CommandLanguage, string> = {
  "hi-IN": "Hindi",
  "en-IN": "English",
  hinglish: "Hinglish",
};

interface TranscriptViewProps {
  transcript: string;
  language?: CommandLanguage | null;
}

export function TranscriptView({ transcript, language }: TranscriptViewProps) {
  return (
    <div className="rounded-2xl bg-slate-100 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Transcript</span>
        {language && (
          <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
            {LANGUAGE_LABELS[language] ?? language}
          </span>
        )}
      </div>
      <p className="mt-2 min-h-[1.5rem] text-base text-slate-800" aria-live="polite">
        {transcript || <span className="text-slate-400">Say something like "Reliance ke 10 shares 2950 limit price par buy karo"</span>}
      </p>
    </div>
  );
}
