/**
 * Isolates persisted key/value storage behind an interface so the UI never
 * depends on `localStorage` directly. A Capacitor build should swap this
 * for `@capacitor/preferences` or a secure-storage plugin without touching
 * any component. Never store API keys or other secrets here -- those live
 * only on the backend.
 */
export interface SecureStorageService {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
}
