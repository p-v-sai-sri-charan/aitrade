import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { OrderPreview, OrderRequest } from "@vaanitrade/shared-types";
import type { VoiceRecognitionLanguage } from "@vaanitrade/voice";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { MicButton } from "../components/voice/MicButton";
import { OrderSummaryCard } from "../components/voice/OrderSummaryCard";
import { TranscriptView } from "../components/voice/TranscriptView";
import { isConfirmationPhrase, isRejectionPhrase } from "../lib/confirmation";
import { useIntentParse } from "../hooks/useIntentParse";
import { useConfirmOrder, usePreviewOrder } from "../hooks/useOrders";
import { voiceService } from "../services/voice/voiceService";
import { useVoiceSessionStore } from "../store/useVoiceSessionStore";

function buildSpokenSummary(preview: OrderPreview): string {
  const { request, estimatedTotal, riskCheck } = preview;
  if (!riskCheck.allowed) {
    return `This order cannot be placed. ${riskCheck.message}`;
  }
  return `Confirm ${request.side.toLowerCase()} of ${request.quantity} shares of ${request.symbol} for approximately ${Math.round(
    estimatedTotal,
  )} rupees. Say confirm to proceed.`;
}

export default function VoiceTrade() {
  const navigate = useNavigate();
  const [recognitionLanguage, setRecognitionLanguage] = useState<VoiceRecognitionLanguage>("en-IN");
  const [manualText, setManualText] = useState("");

  const session = useVoiceSessionStore();
  const intentParse = useIntentParse();
  const previewOrder = usePreviewOrder();
  const confirmOrder = useConfirmOrder();

  const submitTranscript = useCallback(
    async (transcript: string) => {
      if (!transcript.trim()) return;
      session.setFinalTranscript(transcript);
      session.setProcessing();
      try {
        const result = await intentParse.mutateAsync({ transcript });
        session.setParsedIntent(result.intent, result.provider);

        if (result.intent.intent === "PLACE_ORDER" && result.intent.missingFields.length === 0) {
          const request: OrderRequest = {
            exchange: "NSE",
            symbol: result.intent.symbol!,
            side: result.intent.side!,
            quantity: result.intent.quantity!,
            orderType: result.intent.orderType!,
            limitPrice: result.intent.limitPrice,
            product: "DELIVERY",
            validity: "DAY",
          };
          const preview = await previewOrder.mutateAsync(request);
          session.setOrderPreview(preview);
          void voiceService.speak(buildSpokenSummary(preview), recognitionLanguage);
        } else if (result.intent.intent === "VIEW_PORTFOLIO") {
          navigate("/portfolio");
        } else if (result.intent.intent === "VIEW_ORDERS" || result.intent.intent === "VIEW_POSITION") {
          navigate("/orders");
        }
      } catch (error) {
        session.setError(error instanceof Error ? error.message : "Something went wrong.");
      }
    },
    [intentParse, previewOrder, session, navigate, recognitionLanguage],
  );

  const handleConfirm = useCallback(async () => {
    if (!session.orderPreview || !session.idempotencyKey) return;
    session.setConfirming();
    try {
      const order = await confirmOrder.mutateAsync({
        previewId: session.orderPreview.previewId,
        idempotencyKey: session.idempotencyKey,
      });
      session.setPlaced(order);
      void voiceService.speak(
        order.status === "FILLED"
          ? `Order filled. Bought ${order.quantity} shares of ${order.symbol}.`
          : `Order ${order.status.toLowerCase()}.`,
        recognitionLanguage,
      );
    } catch (error) {
      session.setError(error instanceof Error ? error.message : "Order could not be placed.");
    }
  }, [confirmOrder, session, recognitionLanguage]);

  const handleCancelPreview = useCallback(() => {
    session.reset();
  }, [session]);

  // Voice confirmation: once an order preview is shown, listen for an exact
  // confirmation/rejection phrase. Vague phrases are ignored on purpose.
  const handleFinalTranscript = useCallback(
    (text: string) => {
      if (session.status === "awaiting_confirmation") {
        if (isConfirmationPhrase(text)) {
          void handleConfirm();
          return;
        }
        if (isRejectionPhrase(text)) {
          handleCancelPreview();
          return;
        }
      }
      void submitTranscript(text);
    },
    [session.status, handleConfirm, handleCancelPreview, submitTranscript],
  );

  useEffect(() => {
    return () => {
      voiceService.cancelSpeech();
    };
  }, []);

  const isBusy = intentParse.isPending || previewOrder.isPending;

  return (
    <AppShell title="Voice Trade">
      <Card>
        <div className="flex justify-center gap-2 pb-4">
          {(["en-IN", "hi-IN"] as VoiceRecognitionLanguage[]).map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => setRecognitionLanguage(lang)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                recognitionLanguage === lang ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {lang === "en-IN" ? "English" : "हिन्दी"}
            </button>
          ))}
        </div>

        <MicButton
          language={recognitionLanguage}
          disabled={isBusy}
          onInterimTranscript={session.setInterimTranscript}
          onFinalTranscript={handleFinalTranscript}
          onError={session.setError}
        />

        <div className="mt-4">
          <TranscriptView
            transcript={session.interimTranscript || session.finalTranscript}
            language={session.parsedIntent?.language}
          />
        </div>

        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void handleFinalTranscript(manualText);
            setManualText("");
          }}
        >
          <label htmlFor="manual-command" className="sr-only">
            Type a command instead
          </label>
          <input
            id="manual-command"
            type="text"
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Or type a command..."
            className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
          <Button type="submit" variant="secondary" disabled={!manualText.trim() || isBusy}>
            Send
          </Button>
        </form>
      </Card>

      {isBusy && (
        <Card>
          <p className="text-sm text-slate-500">Understanding your command...</p>
        </Card>
      )}

      {session.parsedIntent && session.parsedIntent.missingFields.length > 0 && (
        <Card title="Needs more information">
          {session.parsedIntent.ambiguousSymbolCandidates &&
          session.parsedIntent.ambiguousSymbolCandidates.length > 0 ? (
            <div>
              <p className="text-sm text-slate-600">
                More than one company matches. Which one did you mean?
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {session.parsedIntent.ambiguousSymbolCandidates.map((candidate) => {
                  const [symbol] = candidate.split(" - ");
                  return (
                    <button
                      key={candidate}
                      type="button"
                      className="rounded-full bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 ring-1 ring-brand-200"
                      onClick={() => {
                        const quantity = session.parsedIntent?.quantity;
                        const orderType = session.parsedIntent?.orderType ?? "MARKET";
                        const side = session.parsedIntent?.side;
                        if (!quantity || !side) return;
                        void previewOrder
                          .mutateAsync({
                            exchange: "NSE",
                            symbol,
                            side,
                            quantity,
                            orderType,
                            limitPrice: session.parsedIntent?.limitPrice,
                            product: "DELIVERY",
                            validity: "DAY",
                          })
                          .then((preview) => {
                            session.setOrderPreview(preview);
                            void voiceService.speak(buildSpokenSummary(preview), recognitionLanguage);
                          });
                      }}
                    >
                      {candidate}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-600">
              Missing: {session.parsedIntent.missingFields.join(", ")}. Please try again with the full
              detail, e.g. "Reliance ke 10 shares 2950 limit price par buy karo."
            </p>
          )}
        </Card>
      )}

      {session.orderPreview && session.status === "awaiting_confirmation" && (
        <OrderSummaryCard
          preview={session.orderPreview}
          onConfirm={handleConfirm}
          onCancel={handleCancelPreview}
          isConfirming={confirmOrder.isPending}
        />
      )}

      {session.status === "placed" && session.lastOrder && (
        <Card title="Order status">
          <p className="text-lg font-semibold">
            {session.lastOrder.status} -- {session.lastOrder.side} {session.lastOrder.quantity}{" "}
            {session.lastOrder.symbol}
          </p>
          {session.lastOrder.rejectionReason && (
            <p className="mt-1 text-sm text-loss">{session.lastOrder.rejectionReason}</p>
          )}
          <Button variant="secondary" className="mt-3" onClick={() => session.reset()}>
            Place another order
          </Button>
        </Card>
      )}

      {session.status === "error" && session.errorMessage && (
        <Card>
          <p className="text-sm text-loss">{session.errorMessage}</p>
          <Button variant="secondary" className="mt-3" onClick={() => session.reset()}>
            Try again
          </Button>
        </Card>
      )}
    </AppShell>
  );
}
