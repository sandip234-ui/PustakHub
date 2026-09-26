/**
 * UsersPage — Admin User & IAM Administration Dashboard.
 *
 * Implements Phase 15:
 *   - Search by name or email
 *   - Filter by AccountStatus (ACTIVE, SUSPENDED, DEACTIVATED)
 *   - Filter by Role (ADMIN, LIBRARIAN, STUDENT, GUEST)
 *   - Metrics overview (Total Users, Active, Suspended, Admins)
 *   - User list with role badges, status indicators, MFA states, and action links
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RoleBadge from "../components/RoleBadge";
import UserStatusBadge from "../components/UserStatusBadge";
import Toast from "../components/Toast";
import userService from "../services/user.service";

export function UsersPage() {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Filters & Search
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [roleFilter, setRoleFilter] = useState("ALL");

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (statusFilter !== "ALL") params.status = statusFilter;
      if (roleFilter !== "ALL") params.role = roleFilter;

      const data = await userService.getUsers(params);
      setUsers(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to load user accounts.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [search, statusFilter, roleFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadUsers();
    }, 150);

    return () => {
      clearTimeout(timer);
    };
  }, [loadUsers]);

  // Aggregate Metrics
  const totalCount = users.length;
  const activeCount = users.filter((u) => u.account_status === "ACTIVE").length;
  const suspendedCount = users.filter(
    (u) => u.account_status === "SUSPENDED" || u.account_status === "DEACTIVATED"
  ).length;
  const adminCount = users.filter((u) =>
    u.roles && u.roles.some((r) => r.toUpperCase() === "ADMIN")
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-left space-y-8 animate-fadeIn">
      {/* Toast Notification */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 rounded-3xl border border-gray-800 bg-gray-900/60 p-6 sm:p-8 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-purple-950/80 border border-purple-500/40 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-purple-300">
              IAM Administration
            </span>
            <span className="inline-flex items-center rounded-full bg-emerald-950/70 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">
              ● Authoritative RBAC
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-1">
            User Accounts & Access Management
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Inspect library patrons, manage role assignments, audit permissions, and control account lifecycles.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-xl border border-gray-700 bg-gray-800 px-4 py-2.5 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition cursor-pointer"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5 backdrop-blur-xl">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Total Users
          </span>
          <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-white">
            {isLoading ? "..." : totalCount}
          </div>
          <p className="mt-1 text-xs text-gray-400">Registered member profiles</p>
        </div>

        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 backdrop-blur-xl">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Active Accounts
          </span>
          <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-emerald-400">
            {isLoading ? "..." : activeCount}
          </div>
          <p className="mt-1 text-xs text-gray-400">Permitted to authenticate</p>
        </div>

        <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-5 backdrop-blur-xl">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Suspended / Inactive
          </span>
          <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-rose-400">
            {isLoading ? "..." : suspendedCount}
          </div>
          <p className="mt-1 text-xs text-gray-400">Access restricted by staff</p>
        </div>

        <div className="rounded-2xl border border-purple-500/30 bg-purple-950/20 p-5 backdrop-blur-xl">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Administrators
          </span>
          <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-purple-300">
            {isLoading ? "..." : adminCount}
          </div>
          <p className="mt-1 text-xs text-gray-400">Privileged IAM operators</p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Keyword Search */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">
              Search by Name or Email
            </label>
            <input
              type="text"
              placeholder="Type user name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">
              Account Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Account Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="DEACTIVATED">DEACTIVATED</option>
            </select>
          </div>

          {/* Role Filter */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">
              Filter by Role
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Roles</option>
              <option value="ADMIN">ADMIN</option>
              <option value="LIBRARIAN">LIBRARIAN</option>
              <option value="STUDENT">STUDENT</option>
              <option value="GUEST">GUEST</option>
            </select>
          </div>
        </div>
      </div>

      {/* User Accounts Table */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">👥</span>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Registered Users Ledger
            </h2>
          </div>
          <span className="text-xs text-gray-400">
            Showing <strong className="text-white">{users.length}</strong> matching accounts
          </span>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 animate-pulse rounded-xl bg-gray-800/60" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-xl border border-red-500/40 bg-red-950/40 p-6 text-center text-xs text-red-300">
            <p className="font-semibold">Error Loading Users</p>
            <p className="mt-1 text-gray-400">{error}</p>
            <button
              onClick={loadUsers}
              className="mt-3 rounded-xl bg-gray-800 px-4 py-2 font-semibold text-white hover:bg-gray-700"
            >
              Retry
            </button>
          </div>
        ) : users.length === 0 ? (
          <div className="rounded-xl border border-gray-800/80 bg-gray-950/40 p-8 text-center">
            <span className="text-3xl">🔍</span>
            <p className="mt-2 text-sm font-semibold text-gray-300">No Users Found</p>
            <p className="text-xs text-gray-500 mt-1">
              No registered user accounts match the current filter or search criteria.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-800 text-[11px] uppercase tracking-wider text-gray-400">
                  <th className="pb-3 font-semibold">User Identity</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Assigned Roles</th>
                  <th className="pb-3 font-semibold">MFA</th>
                  <th className="pb-3 font-semibold">Registered</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-800/30 transition">
                    {/* User Identity */}
                    <td className="py-3.5 pr-4">
                      <div className="font-bold text-white text-sm">{u.full_name}</div>
                      <div className="text-gray-400 font-mono text-[11px] mt-0.5">{u.email}</div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3.5 pr-4">
                      <UserStatusBadge status={u.account_status} />
                    </td>

                    {/* Roles */}
                    <td className="py-3.5 pr-4">
                      <div className="flex flex-wrap gap-1">
                        {u.roles && u.roles.length > 0 ? (
                          u.roles.map((role) => <RoleBadge key={role} role={role} />)
                        ) : (
                          <span className="text-gray-500 text-[11px]">None</span>
                        )}
                      </div>
                    </td>

                    {/* MFA Status */}
                    <td className="py-3.5 pr-4">
                      {u.is_mfa_enabled ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                          🛡️ Enabled
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-md bg-gray-800/60 border border-gray-700/40 px-2 py-0.5 text-[10px] text-gray-400">
                          Disabled
                        </span>
                      )}
                    </td>

                    {/* Registered Date */}
                    <td className="py-3.5 pr-4 text-gray-400 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>

                    {/* Action Buttons */}
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <Link
                        to={`/users/${u.id}`}
                        className="inline-flex items-center gap-1 rounded-xl bg-indigo-600/20 border border-indigo-500/30 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/40 hover:border-indigo-500/60 transition"
                      >
                        Manage →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default UsersPage;
