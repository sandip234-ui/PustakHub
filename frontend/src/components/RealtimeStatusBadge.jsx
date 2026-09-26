/**
 * RealtimeStatusBadge — Compact WebSocket connection state indicator.
 * Theme-aware with CSS design tokens.
 */

import useRealtime from "../hooks/useRealtime";
import { ConnectionStatus } from "../services/realtime.service";

export function RealtimeStatusBadge() {
  const { status, reconnect } = useRealtime();

  if (status === ConnectionStatus.CONNECTED) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium"
        style={{
          borderColor: "rgba(16,185,129,0.3)",
          backgroundColor: "rgba(16,185,129,0.08)",
          color: "#34d399",
        }}
        title="Live WebSocket updates active"
        aria-live="polite"
      >
        <span
          className="h-1.5 w-1.5 rounded-full bg-emerald-400"
          style={{ animation: "pulse-glow 2s ease-in-out infinite" }}
        />
        Live
      </span>
    );
  }

  if (status === ConnectionStatus.RECONNECTING) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium"
        style={{
          borderColor: "rgba(245,158,11,0.3)",
          backgroundColor: "rgba(245,158,11,0.08)",
          color: "#fbbf24",
        }}
        title="Reconnecting to real-time update stream…"
        aria-live="polite"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
        Reconnecting…
      </span>
    );
  }

  if (status === ConnectionStatus.CONNECTING) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium"
        style={{
          borderColor: "rgba(59,130,246,0.3)",
          backgroundColor: "rgba(59,130,246,0.08)",
          color: "#60a5fa",
        }}
        title="Establishing real-time connection…"
        aria-live="polite"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
        Connecting…
      </span>
    );
  }

  return (
    <button
      onClick={reconnect}
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition cursor-pointer"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--bg-elevated)",
        color: "var(--text-muted)",
      }}
      title="Real-time disconnected. Click to reconnect."
      aria-live="polite"
      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: "var(--text-muted)" }} />
      Offline
    </button>
  );
}

export default RealtimeStatusBadge;
