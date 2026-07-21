import { WebSpeechVoiceService, type VoiceService } from "@vaanitrade/voice";

/**
 * Single shared VoiceService instance for the app. Swap this factory for a
 * Capacitor-backed implementation later without touching any component --
 * everything else in the app depends on the `VoiceService` interface only.
 */
export const voiceService: VoiceService = new WebSpeechVoiceService();
