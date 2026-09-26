/**
 * ProtectedRoute component.
 *
 * Restricts access to authenticated users and optionally checks for
 * required roles or permissions.
 */

import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import usePermissions from "../hooks/usePermissions";

export function ProtectedRoute({
  allowedRoles = [],
  requiredPermissions = [],
  requiredPermission = null,
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const { hasAnyRole, hasPermission, hasAllPermissions } = usePermissions();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role checks if specified
  if (allowedRoles.length > 0 && !hasAnyRole(allowedRoles)) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4 py-12">
        <div className="max-w-md w-full rounded-2xl border border-red-500/30 bg-gray-900/80 p-8 text-center backdrop-blur-xl">
          <div className="text-4xl mb-4">⛔</div>
          <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
          <p className="text-sm text-gray-400 mb-6">
            You do not have permission to access this management area. This section requires one of the following roles:{" "}
            <span className="font-semibold text-indigo-400">{allowedRoles.join(", ")}</span>.
          </p>
          <div className="flex justify-center gap-3">
            <Link
              to="/dashboard"
              className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
            >
              Back to Dashboard
            </Link>
            <Link
              to="/catalog"
              className="rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-sm font-semibold text-gray-300 hover:bg-gray-700 transition cursor-pointer"
            >
              Browse Catalog
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Permission checks if specified
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4 py-12">
        <div className="max-w-md w-full rounded-2xl border border-red-500/30 bg-gray-900/80 p-8 text-center backdrop-blur-xl">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-white mb-2">Permission Required</h2>
          <p className="text-sm text-gray-400 mb-6">
            Your account lacks the <code className="text-indigo-400 font-mono text-xs">{requiredPermission}</code> permission needed for this view.
          </p>
          <Link
            to="/catalog"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
          >
            Browse Catalog
          </Link>
        </div>
      </div>
    );
  }

  if (requiredPermissions.length > 0 && !hasAllPermissions(requiredPermissions)) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4 py-12">
        <div className="max-w-md w-full rounded-2xl border border-red-500/30 bg-gray-900/80 p-8 text-center backdrop-blur-xl">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-white mb-2">Permissions Required</h2>
          <p className="text-sm text-gray-400 mb-6">
            Your account lacks the necessary permissions to access this page.
          </p>
          <Link
            to="/catalog"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
          >
            Browse Catalog
          </Link>
        </div>
      </div>
    );
  }

  return <Outlet />;
}

export default ProtectedRoute;
