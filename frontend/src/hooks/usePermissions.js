/**
 * usePermissions hook — Role and Permission resolution utility for UI rendering.
 *
 * NOTE: Frontend permission checks are for User Experience (conditional rendering,
 * button visibility, navigation options). Backend API authorization remains the
 * authoritative security boundary.
 */

import { useCallback, useMemo } from "react";
import useAuth from "./useAuth";

// Default standard role-permission mappings matching backend AppRole and AppPermission
const ROLE_PERMISSIONS = {
  ADMIN: [
    "book:view",
    "book:create",
    "book:update",
    "book:delete",
    "book:issue",
    "book:return",
    "user:view",
    "user:create",
    "user:update",
    "user:delete",
    "role:view",
    "role:create",
    "role:update",
    "role:delete",
    "permission:view",
    "permission:assign",
    "audit_log:view",
  ],
  LIBRARIAN: [
    "book:view",
    "book:create",
    "book:update",
    "book:delete",
    "book:issue",
    "book:return",
    "user:view",
    "audit_log:view",
  ],
  STUDENT: ["book:view"],
  GUEST: ["book:view"],
};

// UI Display Precedence: ADMIN > LIBRARIAN > STUDENT > GUEST
const ROLE_DISPLAY_PRECEDENCE = ["ADMIN", "LIBRARIAN", "STUDENT", "GUEST"];

export function usePermissions() {
  const { user, isAuthenticated } = useAuth();

  const userRoles = useMemo(() => {
    if (!user || !user.roles) return [];
    return Array.isArray(user.roles) ? user.roles : [user.roles];
  }, [user]);

  const userPermissions = useMemo(() => {
    // If user object contains resolved permissions list from backend, use it
    if (user && Array.isArray(user.permissions) && user.permissions.length > 0) {
      return new Set(user.permissions);
    }

    // Otherwise derive from assigned roles
    const perms = new Set();
    userRoles.forEach((role) => {
      const roleUpper = (role || "").toUpperCase();
      const mapped = ROLE_PERMISSIONS[roleUpper] || [];
      mapped.forEach((p) => perms.add(p));
    });

    // Public / unauthenticated visitors can view catalog if guest permission allowed
    if (!isAuthenticated) {
      ROLE_PERMISSIONS.GUEST.forEach((p) => perms.add(p));
    }

    return perms;
  }, [user, userRoles, isAuthenticated]);

  const hasPermission = (permission) => {
    if (!permission) return true;
    return userPermissions.has(permission.toLowerCase());
  };

  const hasAnyPermission = (permissions = []) => {
    if (!permissions || permissions.length === 0) return true;
    return permissions.some((p) => userPermissions.has(p.toLowerCase()));
  };

  const hasAllPermissions = (permissions = []) => {
    if (!permissions || permissions.length === 0) return true;
    return permissions.every((p) => userPermissions.has(p.toLowerCase()));
  };

  const hasRole = useCallback(
    (role) => {
      if (!role) return true;
      const roleUpper = role.toUpperCase();
      return userRoles.some((r) => (r || "").toUpperCase() === roleUpper);
    },
    [userRoles]
  );

  const hasAnyRole = (roles = []) => {
    if (!roles || roles.length === 0) return true;
    const upperRoles = roles.map((r) => r.toUpperCase());
    return userRoles.some((r) => upperRoles.includes((r || "").toUpperCase()));
  };

  const isAdmin = hasRole("ADMIN");
  const isLibrarian = hasRole("LIBRARIAN");
  const isStudent = hasRole("STUDENT");
  const isStaff = isAdmin || isLibrarian;

  const canManageCatalog = hasAnyPermission(["book:create", "book:update", "book:delete"]);
  const canCreateBook = hasPermission("book:create");
  const canUpdateBook = hasPermission("book:update");
  const canDeleteBook = hasPermission("book:delete");
  const canViewCatalog = hasPermission("book:view");
  const canIssueBook = hasPermission("book:issue");
  const canReturnBook = hasPermission("book:return");

  const permissionsList = useMemo(() => {
    return Array.from(userPermissions);
  }, [userPermissions]);

  const primaryRole = useMemo(() => {
    if (!isAuthenticated) return "GUEST";
    for (const role of ROLE_DISPLAY_PRECEDENCE) {
      if (hasRole(role)) return role;
    }
    return userRoles[0] || "MEMBER";
  }, [userRoles, hasRole, isAuthenticated]);

  return {
    roles: userRoles,
    primaryRole,
    permissions: permissionsList,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    isAdmin,
    isLibrarian,
    isStudent,
    isStaff,
    canManageCatalog,
    canCreateBook,
    canUpdateBook,
    canDeleteBook,
    canViewCatalog,
    canIssueBook,
    canReturnBook,
  };
}

export default usePermissions;
