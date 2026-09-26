/**
 * ConfirmDialog — Accessible modal dialog for destructive/confirmation actions.
 * Theme-aware with CSS design tokens.
 */

import { AlertTriangle, HelpCircle, X } from "lucide-react";
import { useEffect } from "react";

export function ConfirmDialog({
  isOpen,
  title = "Are you sure?",
  message = "This action cannot be undone.",
  itemName = "",
  confirmText = "Delete",
  cancelText = "Cancel",
  isDanger = true,
  isLoading = false,
  error = null,
  onConfirm,
  onCancel,
}) {
  // Escape key support
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === "Escape" && onCancel) onCancel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const Icon = isDanger ? AlertTriangle : HelpCircle;

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onCancel?.()}
    >
      <div
        className="modal-content w-full max-w-md p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="flex items-start gap-4 mb-4">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border"
            style={{
              borderColor: isDanger
                ? "rgba(244,63,94,0.3)"
                : "rgba(245,158,11,0.3)",
              backgroundColor: isDanger
                ? "rgba(244,63,94,0.1)"
                : "rgba(245,158,11,0.1)",
            }}
          >
            <Icon
              size={18}
              style={{ color: isDanger ? "#fb7185" : "#fbbf24" }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <h3
              id="confirm-dialog-title"
              className="text-base font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              {title}
            </h3>
            {itemName && (
              <p
                className="text-xs mt-0.5 truncate font-medium"
                style={{ color: "var(--primary)" }}
              >
                &ldquo;{itemName}&rdquo;
              </p>
            )}
          </div>
          <button
            onClick={onCancel}
            className="flex h-7 w-7 items-center justify-center rounded-lg transition"
            style={{ color: "var(--text-muted)" }}
            aria-label="Close dialog"
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <X size={15} />
          </button>
        </div>

        <p
          className="text-sm mb-5"
          style={{ color: "var(--text-secondary)" }}
        >
          {message}
        </p>

        {error && (
          <div
            className="mb-4 rounded-xl border px-3 py-2.5 text-xs"
            style={{
              borderColor: "rgba(244,63,94,0.3)",
              backgroundColor: "var(--danger-bg)",
              color: "var(--danger-text)",
            }}
          >
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="btn btn-secondary btn-sm"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`btn btn-sm ${isDanger ? "btn-danger" : "btn-primary"}`}
          >
            {isLoading ? "Processing…" : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
