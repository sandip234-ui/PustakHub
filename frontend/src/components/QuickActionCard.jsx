/**
 * QuickActionCard — Premium action shortcut for role-based tasks.
 * Uses Lucide icon, CSS design tokens, and theme-aware styling.
 */

import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const COLOR_MAP = {
  indigo: { iconColor: "#818cf8", iconBg: "rgba(99,102,241,0.1)", hoverBorder: "rgba(99,102,241,0.35)" },
  emerald: { iconColor: "#34d399", iconBg: "rgba(16,185,129,0.1)", hoverBorder: "rgba(16,185,129,0.35)" },
  amber: { iconColor: "#fbbf24", iconBg: "rgba(245,158,11,0.1)", hoverBorder: "rgba(245,158,11,0.35)" },
  purple: { iconColor: "#c084fc", iconBg: "rgba(168,85,247,0.1)", hoverBorder: "rgba(168,85,247,0.35)" },
  blue: { iconColor: "#60a5fa", iconBg: "rgba(59,130,246,0.1)", hoverBorder: "rgba(59,130,246,0.35)" },
  rose: { iconColor: "#fb7185", iconBg: "rgba(244,63,94,0.1)", hoverBorder: "rgba(244,63,94,0.35)" },
};

export function QuickActionCard({
  title,
  description,
  icon: Icon,
  to,
  onClick,
  color = "indigo",
  badge,
}) {
  const c = COLOR_MAP[color] || COLOR_MAP.indigo;

  const cardContent = (
    <div className="action-card group flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-110"
            style={{ backgroundColor: c.iconBg }}
          >
            {Icon && <Icon size={18} style={{ color: c.iconColor }} />}
          </div>
          {badge && (
            <span
              className="rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
              style={{
                borderColor: "rgba(99,102,241,0.3)",
                backgroundColor: "rgba(99,102,241,0.08)",
                color: "var(--primary)",
              }}
            >
              {badge}
            </span>
          )}
        </div>

        <h3
          className="text-sm font-bold leading-snug"
          style={{ color: "var(--text-primary)" }}
        >
          {title}
        </h3>
        {description && (
          <p
            className="mt-1 text-xs leading-relaxed line-clamp-2"
            style={{ color: "var(--text-secondary)" }}
          >
            {description}
          </p>
        )}
      </div>

      <div
        className="mt-4 flex items-center gap-1 text-xs font-semibold transition-colors duration-150"
        style={{ color: "var(--text-muted)" }}
      >
        <span>Proceed</span>
        <ArrowRight
          size={12}
          className="transition-transform duration-200 group-hover:translate-x-1"
        />
      </div>
    </div>
  );

  if (to) {
    return (
      <Link to={to} className="block h-full">
        {cardContent}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button
        onClick={onClick}
        type="button"
        className="block w-full h-full text-left"
      >
        {cardContent}
      </button>
    );
  }

  return cardContent;
}

export default QuickActionCard;
