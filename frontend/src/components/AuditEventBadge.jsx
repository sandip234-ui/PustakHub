/**
 * AuditEventBadge — Visual badge for canonical audit action types.
 */

export function AuditEventBadge({ action }) {
  const act = (action || "UNKNOWN").toUpperCase();

  const getStyle = () => {
    // Authentication
    if (act.startsWith("LOGIN") || act.startsWith("LOGOUT") || act.startsWith("TOKEN") || act.startsWith("PASSWORD") || act.startsWith("ACCOUNT")) {
      return act.includes("FAILURE") || act.includes("LOCKED")
        ? "bg-rose-950/70 text-rose-300 border-rose-500/40"
        : "bg-blue-950/70 text-blue-300 border-blue-500/40";
    }

    // MFA
    if (act.startsWith("MFA")) {
      return act.includes("FAILED")
        ? "bg-rose-950/70 text-rose-300 border-rose-500/40"
        : "bg-purple-950/70 text-purple-300 border-purple-500/40";
    }

    // IAM / User Management
    if (act.startsWith("USER_") || act.startsWith("ROLE_") || act.startsWith("PERMISSION_")) {
      return act.includes("DEACTIVATED") || act.includes("REVOKED") || act.includes("SUSPENDED")
        ? "bg-amber-950/70 text-amber-300 border-amber-500/40"
        : "bg-fuchsia-950/70 text-fuchsia-300 border-fuchsia-500/40";
    }

    // Catalog
    if (act.startsWith("BOOK_") || act.startsWith("CATEGORY_")) {
      return "bg-emerald-950/70 text-emerald-300 border-emerald-500/40";
    }

    // Circulation & Fines
    if (act.startsWith("COPY_") || act.startsWith("FINE_") || act.startsWith("BORROW_")) {
      return "bg-cyan-950/70 text-cyan-300 border-cyan-500/40";
    }

    return "bg-gray-800/80 text-gray-300 border-gray-700";
  };

  return (
    <span
      className={`inline-flex items-center rounded-lg border px-2 py-0.5 text-[11px] font-mono font-semibold tracking-wide ${getStyle()}`}
    >
      {act}
    </span>
  );
}

export default AuditEventBadge;
