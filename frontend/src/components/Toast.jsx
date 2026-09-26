/**
 * Toast — Lightweight floating notification with theme-aware design.
 */

import { useEffect } from "react";
import { AlertTriangle, CheckCircle, Info, X } from "lucide-react";

export function Toast({ message, type = "success", onClose, duration = 4000 }) {
  if (!message) return null;

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (!onClose) return;
    const t = setTimeout(onClose, duration);
    return () => clearTimeout(t);
  }, [onClose, duration]);

  const config = {
    success: {
      Icon: CheckCircle,
      borderColor: "rgba(16,185,129,0.3)",
      bgColor: "rgba(16,185,129,0.08)",
      textColor: "#34d399",
    },
    error: {
      Icon: AlertTriangle,
      borderColor: "rgba(244,63,94,0.3)",
      bgColor: "rgba(244,63,94,0.08)",
      textColor: "#fb7185",
    },
    info: {
      Icon: Info,
      borderColor: "rgba(99,102,241,0.3)",
      bgColor: "rgba(99,102,241,0.08)",
      textColor: "#818cf8",
    },
  };

  const { Icon, borderColor, textColor } = config[type] || config.info;

  return (
    <div
      className="toast flex items-start gap-3"
      style={{ borderColor, backgroundColor: "var(--bg-elevated)" }}
      role="alert"
      aria-live="polite"
    >
      <Icon
        size={16}
        className="mt-0.5 shrink-0"
        style={{ color: textColor }}
      />
      <p
        className="flex-1 text-sm font-medium"
        style={{ color: "var(--text-primary)" }}
      >
        {message}
      </p>
      {onClose && (
        <button
          onClick={onClose}
          className="rounded-lg p-0.5 transition"
          style={{ color: "var(--text-muted)" }}
          aria-label="Close notification"
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export default Toast;
