/**
 * PermissionGate — Declarative UI visibility wrapper.
 *
 * Conditionally renders children if the authenticated user possesses the
 * required permission(s) or role(s).
 */

import usePermissions from "../hooks/usePermissions";

export function PermissionGate({
  permission,
  permissions = [],
  mode = "any", // "any" | "all"
  role,
  roles = [],
  fallback = null,
  children,
}) {
  const {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
  } = usePermissions();

  // Role checks
  if (role && !hasRole(role)) {
    return fallback;
  }

  if (roles.length > 0 && !hasAnyRole(roles)) {
    return fallback;
  }

  // Single permission check
  if (permission && !hasPermission(permission)) {
    return fallback;
  }

  // Multiple permission check
  if (permissions.length > 0) {
    const isGranted =
      mode === "all"
        ? hasAllPermissions(permissions)
        : hasAnyPermission(permissions);

    if (!isGranted) {
      return fallback;
    }
  }

  return children;
}

export default PermissionGate;
