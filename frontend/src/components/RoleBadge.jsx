/**
 * RoleBadge — Visual badge for assigned RBAC roles.
 * Theme-aware using design tokens and semantic classes.
 */

const ROLE_CLASSES = {
  ADMIN: "badge-role-admin",
  LIBRARIAN: "badge-role-librarian",
  STUDENT: "badge-role-student",
  GUEST: "badge-role-guest",
};

export function RoleBadge({ role, size = "sm" }) {
  const normalized = (role || "").toUpperCase();
  const roleClass = ROLE_CLASSES[normalized] || "badge-role-guest";
  const sizeClass = size === "md" ? "px-2.5 py-1 text-xs" : "px-2 py-0.5 text-[11px]";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-lg border font-bold uppercase tracking-wider transition-colors ${sizeClass} ${roleClass}`}
      title={`Role: ${normalized || "GUEST"}`}
    >
      {normalized || "GUEST"}
    </span>
  );
}

export default RoleBadge;

