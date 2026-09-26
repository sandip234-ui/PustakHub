/**
 * AuthCard — Shared wrapper for all authentication pages.
 * Theme-aware with hero-grid + radial-glow background.
 */

import { AlertTriangle, CheckCircle } from "lucide-react";

export function AuthCard({ icon: Icon, title, subtitle, children }) {
  return (
    <div
      className="relative flex min-h-[calc(100vh-56px)] items-center justify-center px-4 py-12"
      style={{ backgroundColor: "var(--bg)" }}
    >
      <div className="hero-grid pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="radial-glow pointer-events-none absolute inset-0" aria-hidden="true" />

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          {Icon && (
            <div
              className="inline-flex h-14 w-14 items-center justify-center rounded-2xl border mb-4 shadow-lg"
              style={{
                backgroundColor: "var(--primary-soft)",
                borderColor: "rgba(99,102,241,0.25)",
                boxShadow: "0 8px 24px var(--primary-glow)",
              }}
            >
              <Icon size={26} style={{ color: "var(--primary)" }} />
            </div>
          )}
          <h1
            className="text-2xl font-black tracking-tight sm:text-3xl"
            style={{ color: "var(--text-primary)" }}
          >
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>
              {subtitle}
            </p>
          )}
        </div>

        <div
          className="rounded-2xl border p-6 sm:p-8"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderColor: "var(--border)",
            boxShadow: "var(--shadow-lg)",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

export function AuthError({ message }) {
  if (!message) return null;
  return (
    <div
      className="mb-5 rounded-xl border px-4 py-3 flex items-start gap-2.5 text-sm"
      style={{
        borderColor: "rgba(244,63,94,0.3)",
        backgroundColor: "var(--danger-bg)",
        color: "var(--danger-text)",
      }}
      role="alert"
    >
      <AlertTriangle size={15} className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export function AuthSuccess({ message }) {
  if (!message) return null;
  return (
    <div
      className="mb-5 rounded-xl border px-4 py-3 flex items-start gap-2.5 text-sm"
      style={{
        borderColor: "rgba(16,185,129,0.3)",
        backgroundColor: "var(--success-bg)",
        color: "var(--success-text)",
      }}
      role="status"
    >
      <CheckCircle size={15} className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export function AuthLabel({ htmlFor, children }) {
  return (
    <label
      htmlFor={htmlFor}
      className="block text-xs font-semibold uppercase tracking-wider mb-1.5"
      style={{ color: "var(--text-muted)" }}
    >
      {children}
    </label>
  );
}

export function AuthDivider({ children }) {
  return (
    <div
      className="mt-6 text-center text-sm border-t pt-5"
      style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
    >
      {children}
    </div>
  );
}

export function AuthLink({ to, children }) {
  return (
    <a
      href={to}
      className="font-semibold transition"
      style={{ color: "var(--primary)" }}
    >
      {children}
    </a>
  );
}

export default AuthCard;
