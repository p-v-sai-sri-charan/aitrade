import type { PropsWithChildren } from "react";
import { PaperTradingBadge } from "../ui/PaperTradingBadge";
import { BottomNav } from "./BottomNav";

export function AppShell({ children, title }: PropsWithChildren<{ title: string }>) {
  return (
    <div className="min-h-full pb-24">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
        <h1 className="text-lg font-bold text-slate-900">{title}</h1>
        <PaperTradingBadge />
      </header>
      <main className="mx-auto max-w-xl space-y-4 p-4">{children}</main>
      <BottomNav />
    </div>
  );
}
