/**
 * AuditStatusBadge — Semantic badge for audit event outcome status.
 */

export function AuditStatusBadge({ status }) {
  const stat = (status || "SUCCESS").toUpperCase();

  switch (stat) {
    case "SUCCESS":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/70 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
          <span className="text-[8px]">●</span> SUCCESS
        </span>
      );
    case "FAILURE":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-950/70 border border-red-500/40 px-2 py-0.5 text-[10px] font-bold text-red-300">
          <span className="text-[8px]">✕</span> FAILURE
        </span>
      );
    case "PARTIAL":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-950/70 border border-amber-500/40 px-2 py-0.5 text-[10px] font-bold text-amber-300">
          <span className="text-[8px]">▲</span> PARTIAL
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-full bg-gray-800 border border-gray-700 px-2 py-0.5 text-[10px] font-semibold text-gray-300">
          {stat}
        </span>
      );
  }
}

export default AuditStatusBadge;
