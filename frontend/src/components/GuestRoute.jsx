/**
 * GuestRoute component.
 *
 * Restricts access to non-authenticated visitors (guests) only.
 * Redirects authenticated users to /dashboard.
 */

import { Navigate, Outlet } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export function GuestRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default GuestRoute;
