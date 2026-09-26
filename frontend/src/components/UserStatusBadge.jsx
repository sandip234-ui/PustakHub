/**
 * UserStatusBadge — Semantic badge for account lifecycle state.
 */

export function UserStatusBadge({ status }) {
  const normalized = (status || "ACTIVE").toUpperCase();

  const configs = {
    ACTIVE: {
      bg: "bg-emerald-950/70",
      border: "border-emerald-500/40",
      text: "text-emerald-400",
      icon: "●",
      label: "Active",
    },
    SUSPENDED: {
      bg: "bg-amber-950/70",
      border: "border-amber-500/40",
      text: "text-amber-400",
      icon: "⏸",
      label: "Suspended",
    },
    DEACTIVATED: {
      bg: "bg-rose-950/70",
      border: "border-rose-500/40",
      text: "text-rose-400",
      icon: "⊘",
      label: "Deactivated",
    },
    PENDING_VERIFICATION: {
      bg: "bg-blue-950/70",
      border: "border-blue-500/40",
      text: "text-blue-400",
      icon: "⏳",
      label: "Pending Verification",
    },
  };

  const config = configs[normalized] || configs.ACTIVE;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${config.bg} border ${config.border} px-2.5 py-0.5 text-xs font-semibold ${config.text}`}
      title={`Account Status: ${config.label}`}
    >
      <span className="text-[10px]">{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
}

export default UserStatusBadge;
