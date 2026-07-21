import { useMutation } from "@tanstack/react-query";
import type { CommandLanguage, TradeIntentResult } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

interface ParseIntentInput {
  transcript: string;
  detectedLanguage?: CommandLanguage;
}

export function useIntentParse() {
  return useMutation({
    mutationFn: (input: ParseIntentInput) =>
      apiClient.post<TradeIntentResult>("/intent/parse", input),
  });
}
