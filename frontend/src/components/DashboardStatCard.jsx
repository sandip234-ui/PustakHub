/**
 * DashboardStatCard — Premium metric card with skeleton loading,
 * semantic icon support (Lucide), theme-aware design, and subtle hover effects.
 *
 * Props:
 *   title     — Label
 *   value     — Primary metric value
 *   subtitle  — Contextual description (no fabricated trends)
 *   icon      — Lucide icon component (not emoji)
 *   color     — Accent color variant
 *   loading   — Skeleton state
 *   error     — Error state
 *   to        — Optional link target
 */

import { Link } from "react-router-dom";

const COLOR_MAP = {
  indigo: {
    iconBg: "rgba(99,102,241,0.1)",
    iconColor: "#818cf8",
    accent: "rgba(99,102,241,0.15)",
    hoverBorder: "rgba(99,102,241,0.4)",
  },
  emerald: {
    iconBg: "rgba(16,185,129,0.1)",
    iconColor: "#34d399",
    accent: "rgba(16,185,129,0.15)",
    hoverBorder: "rgba(16,185,129,0.4)",
  },
  amber: {
    iconBg: "rgba(245,158,11,0.1)",
    iconColor: "#fbbf24",
    accent: "rgba(245,158,11,0.15)",
    hoverBorder: "rgba(245,158,11,0.4)",
  },
  rose: {
    iconBg: "rgba(244,63,94,0.1)",
    iconColor: "#fb7185",
    accent: "rgba(244,63,94,0.15)",
    hoverBorder: "rgba(244,63,94,0.4)",
  },
  blue: {
    iconBg: "rgba(59,130,246,0.1)",
    iconColor: "#60a5fa",
    accent: "rgba(59,130,246,0.15)",
    hoverBorder: "rgba(59,130,246,0.4)",
  },
  purple: {
    iconBg: "rgba(168,85,247,0.1)",
    iconColor: "#c084fc",
    accent: "rgba(168,85,247,0.15)",
    hoverBorder: "rgba(168,85,247,0.4)",
  },
  slate: {
    iconBg: "rgba(148,163,184,0.1)",
    iconColor: "#94a3b8",
    accent: "rgba(148,163,184,0.15)",
    hoverBorder: "rgba(148,163,184,0.4)",
  },
};

export function DashboardStatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "indigo",
  loading = false,
  error = null,
  to,
}) {
  const c = COLOR_MAP[color] || COLOR_MAP.indigo;

  const content = (
    <div
      className="stat-card group relative overflow-hidden"
      style={{
        "--hover-border": c.hoverBorder,
      }}
    >
      {/* Subtle accent top-bar */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px] rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        style={{ backgroundColor: c.iconColor }}
        aria-hidden="true"
      />

      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p
            className="text-[11px] font-semibold uppercase tracking-wider truncate"
            style={{ color: "var(--text-muted)" }}
          >
            {title}
          </p>

          <div className="mt-2">
            {loading ? (
              <div className="space-y-1.5">
                <div className="skeleton h-8 w-20" />
                <div className="skeleton h-3 w-32" />
              </div>
            ) : error ? (
              <span className="text-sm font-semibold" style={{ color: "var(--danger-text)" }}>
                Unavailable
              </span>
            ) : (
              <>
                <p
                  className="text-2xl sm:text-3xl font-black tracking-tight"
                  style={{ color: "var(--text-primary)" }}
                >
                  {value ?? "—"}
                </p>
                {subtitle && (
                  <p
                    className="mt-0.5 text-xs truncate"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {subtitle}
                  </p>
                )}
              </>
            )}
          </div>
        </div>

        {Icon && (
          <div
            className="ml-3 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-110"
            style={{ backgroundColor: c.iconBg }}
          >
            <Icon size={18} style={{ color: c.iconColor }} />
          </div>
        )}
      </div>

      {to && !loading && !error && (
        <div
          className="mt-3 flex items-center gap-1 text-[11px] font-semibold transition-colors duration-150"
          style={{ color: "var(--text-muted)" }}
        >
          View details →
        </div>
      )}
    </div>
  );

  if (to) {
    return (
      <Link to={to} className="block">
        {content}
      </Link>
    );
  }

  return content;
}

export default DashboardStatCard;
