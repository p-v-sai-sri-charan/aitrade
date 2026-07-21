import type { PropsWithChildren } from "react";

interface CardProps {
  className?: string;
  title?: string;
  subtitle?: string;
}

export function Card({ className = "", title, subtitle, children }: PropsWithChildren<CardProps>) {
  return (
    <section className={`rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200 ${className}`}>
      {title && <h3 className="text-sm font-medium text-slate-500">{title}</h3>}
      {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
      <div className={title ? "mt-2" : ""}>{children}</div>
    </section>
  );
}
