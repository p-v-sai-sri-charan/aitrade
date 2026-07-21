import type { SecureStorageService } from "./SecureStorageService";

const PREFIX = "vaanitrade:";

export class LocalStorageService implements SecureStorageService {
  async get(key: string): Promise<string | null> {
    try {
      return window.localStorage.getItem(PREFIX + key);
    } catch {
      return null;
    }
  }

  async set(key: string, value: string): Promise<void> {
    try {
      window.localStorage.setItem(PREFIX + key, value);
    } catch {
      // Storage may be unavailable (private browsing, quota) -- fail silently,
      // this is only used for non-critical UI preferences.
    }
  }

  async remove(key: string): Promise<void> {
    try {
      window.localStorage.removeItem(PREFIX + key);
    } catch {
      // no-op
    }
  }
}

export const secureStorage: SecureStorageService = new LocalStorageService();
