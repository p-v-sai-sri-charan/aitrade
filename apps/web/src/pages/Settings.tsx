import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useResetPaperTrading, useSettings, useUpdateSettings } from "../hooks/useSettings";

const settingsSchema = z.object({
  aiProvider: z.enum(["mock", "anthropic", "openai", "gemini", "local", "ollama"]),
  languagePreference: z.enum(["hi-IN", "en-IN", "hinglish", "auto"]),
  voiceOutputEnabled: z.boolean(),
  tradingKillSwitch: z.boolean(),
  maxOrderValue: z.coerce.number().positive(),
  maxQuantity: z.coerce.number().int().positive(),
  maxPriceDeviationPct: z.coerce.number().positive(),
  dailyLossLimit: z.coerce.number().positive(),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

export default function Settings() {
  const settingsQuery = useSettings();
  const updateSettings = useUpdateSettings();
  const resetPaperTrading = useResetPaperTrading();
  const [confirmingReset, setConfirmingReset] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<SettingsFormValues>({ resolver: zodResolver(settingsSchema) });

  useEffect(() => {
    if (settingsQuery.data) {
      reset({
        aiProvider: settingsQuery.data.aiProvider,
        languagePreference: settingsQuery.data.languagePreference,
        voiceOutputEnabled: settingsQuery.data.voiceOutputEnabled,
        tradingKillSwitch: settingsQuery.data.tradingKillSwitch,
        maxOrderValue: settingsQuery.data.riskLimits.maxOrderValue,
        maxQuantity: settingsQuery.data.riskLimits.maxQuantity,
        maxPriceDeviationPct: settingsQuery.data.riskLimits.maxPriceDeviationPct,
        dailyLossLimit: settingsQuery.data.riskLimits.dailyLossLimit,
      });
    }
  }, [settingsQuery.data, reset]);

  const onSubmit = handleSubmit((values) => {
    updateSettings.mutate(
      {
        aiProvider: values.aiProvider,
        languagePreference: values.languagePreference,
        voiceOutputEnabled: values.voiceOutputEnabled,
        tradingKillSwitch: values.tradingKillSwitch,
        riskLimits: {
          maxOrderValue: values.maxOrderValue,
          maxQuantity: values.maxQuantity,
          maxPriceDeviationPct: values.maxPriceDeviationPct,
          dailyLossLimit: values.dailyLossLimit,
        },
      },
      {
        onSuccess: () => {
          setSavedMessage(true);
          setTimeout(() => setSavedMessage(false), 2500);
        },
      },
    );
  });

  if (settingsQuery.isLoading) {
    return (
      <AppShell title="Settings">
        <Card>Loading settings...</Card>
      </AppShell>
    );
  }

  return (
    <AppShell title="Settings">
      <form onSubmit={onSubmit} className="space-y-4">
        <Card title="AI provider">
          <select
            {...register("aiProvider")}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="mock">Mock (offline, no API key needed)</option>
            <option value="anthropic">Anthropic Claude</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Google Gemini</option>
            <option value="local">Local OpenAI-compatible</option>
            <option value="ollama">Ollama</option>
          </select>
          <p className="mt-2 text-xs text-slate-500">
            API keys are configured on the server via environment variables and are never sent to or
            stored in this app.
          </p>
        </Card>

        <Card title="Language preference">
          <select
            {...register("languagePreference")}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="auto">Auto-detect</option>
            <option value="en-IN">English</option>
            <option value="hi-IN">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
        </Card>

        <Card title="Voice output">
          <label className="flex items-center justify-between text-sm">
            <span>Speak order summaries and confirmations aloud</span>
            <input type="checkbox" {...register("voiceOutputEnabled")} className="h-5 w-5" />
          </label>
        </Card>

        <Card title="Risk limits">
          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs text-slate-500">
              Max order value (₹)
              <input
                type="number"
                {...register("maxOrderValue")}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
              />
              {errors.maxOrderValue && <p className="text-loss">{errors.maxOrderValue.message}</p>}
            </label>
            <label className="text-xs text-slate-500">
              Max quantity
              <input
                type="number"
                {...register("maxQuantity")}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
              />
              {errors.maxQuantity && <p className="text-loss">{errors.maxQuantity.message}</p>}
            </label>
            <label className="text-xs text-slate-500">
              Max price deviation (%)
              <input
                type="number"
                step="0.1"
                {...register("maxPriceDeviationPct")}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
              />
            </label>
            <label className="text-xs text-slate-500">
              Daily loss limit (₹)
              <input
                type="number"
                {...register("dailyLossLimit")}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
              />
            </label>
          </div>
        </Card>

        <Card title="Trading kill switch">
          <label className="flex items-center justify-between text-sm">
            <span>Block all new orders immediately</span>
            <input type="checkbox" {...register("tradingKillSwitch")} className="h-5 w-5" />
          </label>
        </Card>

        <Button type="submit" className="w-full" disabled={!isDirty || updateSettings.isPending}>
          {updateSettings.isPending ? "Saving..." : savedMessage ? "Saved" : "Save settings"}
        </Button>
      </form>

      <Card title="Paper trading reset">
        <p className="text-sm text-slate-500">
          Wipes all paper orders and positions and restores your starting balance. This cannot be
          undone.
        </p>
        {!confirmingReset ? (
          <Button variant="danger" className="mt-3 w-full" onClick={() => setConfirmingReset(true)}>
            Reset paper trading account
          </Button>
        ) : (
          <div className="mt-3 flex gap-2">
            <Button variant="secondary" className="flex-1" onClick={() => setConfirmingReset(false)}>
              Keep my data
            </Button>
            <Button
              variant="danger"
              className="flex-1"
              disabled={resetPaperTrading.isPending}
              onClick={() =>
                resetPaperTrading.mutate(undefined, { onSuccess: () => setConfirmingReset(false) })
              }
            >
              Yes, reset
            </Button>
          </div>
        )}
      </Card>
    </AppShell>
  );
}
