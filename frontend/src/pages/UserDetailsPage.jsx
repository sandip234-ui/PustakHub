/**
 * UserDetailsPage — User Profile & IAM Administration View.
 *
 * Implements Phase 15:
 *   - Identity Profile (UUID, Full Name, Email, Status, MFA, Verification)
 *   - Account Status Transition Controls (Activate, Suspend, Deactivate) with ConfirmDialog
 *   - Role Assignment & Revocation with elevated privilege warnings & self-lockout defense
 *   - Effective Permissions Panel (Role-derived dynamic permissions)
 *   - Patron Borrowing Activity Summary
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import EffectivePermissionsPanel from "../components/EffectivePermissionsPanel";
import RoleAssignmentModal from "../components/RoleAssignmentModal";
import RoleBadge from "../components/RoleBadge";
import Toast from "../components/Toast";
import UserStatusBadge from "../components/UserStatusBadge";
import useAuth from "../hooks/useAuth";
import usePermissions from "../hooks/usePermissions";
import circulationService from "../services/circulation.service";
import userService from "../services/user.service";

export function UserDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const { hasRole } = usePermissions();
  const isAdmin = hasRole("ADMIN");

  const isSelf = currentUser?.id === id;

  // State
  const [user, setUser] = useState(null);
  const [effectivePermissions, setEffectivePermissions] = useState([]);
  const [borrowings, setBorrowings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [permissionsLoading, setPermissionsLoading] = useState(true);
  const [borrowingsLoading, setBorrowingsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Modals & Action States
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [roleToRevoke, setRoleToRevoke] = useState(null);
  const [statusToChange, setStatusToChange] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Load User Data
  const loadUserData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await userService.getUserById(id);
      setUser(data);
    } catch (err) {
      const msg = err?.response?.data?.message || err?.message || "Failed to load user profile.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Load Effective Permissions
  const loadPermissions = useCallback(async () => {
    setPermissionsLoading(true);
    try {
      const res = await userService.getUserEffectivePermissions(id);
      setEffectivePermissions(res?.permissions || []);
    } catch {
      setEffectivePermissions([]);
    } finally {
      setPermissionsLoading(false);
    }
  }, [id]);

  // Load Borrowings Summary
  const loadBorrowings = useCallback(async () => {
    setBorrowingsLoading(true);
    try {
      const res = await circulationService.getBorrowings({ user_id: id, page: 1, page_size: 5 });
      setBorrowings(res?.items || []);
    } catch {
      setBorrowings([]);
    } finally {
      setBorrowingsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadUserData();
      loadPermissions();
      loadBorrowings();
    }, 10);

    return () => {
      clearTimeout(timer);
    };
  }, [loadUserData, loadPermissions, loadBorrowings]);

  // Status Change Handler
  const handleConfirmStatusChange = async () => {
    if (!statusToChange) return;

    if (isSelf && statusToChange !== "ACTIVE") {
      setToast({
        type: "error",
        message: "Self-protection: You cannot deactivate or suspend your own active administrator account.",
      });
      setStatusToChange(null);
      return;
    }

    setIsProcessing(true);
    try {
      const updated = await userService.updateUserStatus(id, statusToChange);
      setUser(updated);
      setToast({
        type: "success",
        message: `Account status updated to ${statusToChange} successfully.`,
      });
      setStatusToChange(null);
    } catch (err) {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || "Failed to update account status.";
      setToast({ type: "error", message: msg });
    } finally {
      setIsProcessing(false);
    }
  };

  // Role Revocation Handler
  const handleConfirmRoleRevoke = async () => {
    if (!roleToRevoke) return;

    if (isSelf && roleToRevoke.toUpperCase() === "ADMIN") {
      setToast({
        type: "error",
        message: "Self-protection: You cannot revoke your own ADMIN role.",
      });
      setRoleToRevoke(null);
      return;
    }

    setIsProcessing(true);
    try {
      await userService.revokeRole(id, roleToRevoke);
      setToast({
        type: "success",
        message: `Role "${roleToRevoke}" revoked successfully.`,
      });
      setRoleToRevoke(null);
      await loadUserData();
      await loadPermissions();
    } catch (err) {
      const msg = err?.response?.data?.message || err?.response?.data?.detail || "Failed to revoke role.";
      setToast({ type: "error", message: msg });
    } finally {
      setIsProcessing(false);
    }
  };

  // Role Grant Success
  const handleRoleGranted = async (assignedRoleOrUser, maybeRoleName) => {
    const roleName = typeof assignedRoleOrUser === "string" ? assignedRoleOrUser : maybeRoleName || "Role";
    setToast({
      type: "success",
      message: `Role "${roleName}" granted successfully.`,
    });
    await loadUserData();
    await loadPermissions();
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="h-8 w-48 bg-gray-800 animate-pulse rounded-lg" />
        <div className="h-48 bg-gray-900/60 border border-gray-800 rounded-3xl animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 bg-gray-900/60 border border-gray-800 rounded-2xl animate-pulse" />
          <div className="h-64 bg-gray-900/60 border border-gray-800 rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center space-y-4">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-red-950/40 border border-red-500/30 text-3xl">
          ⚠️
        </div>
        <h1 className="text-xl font-bold text-white">User Record Not Available</h1>
        <p className="text-sm text-gray-400 max-w-md mx-auto">{error || "The requested user record could not be found."}</p>
        <div className="pt-2">
          <Link
            to="/users"
            className="inline-flex items-center gap-2 rounded-xl bg-gray-800 px-4 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-700 transition"
          >
            ← Return to Users Ledger
          </Link>
        </div>
      </div>
    );
  }

  const assignedRoles = user.roles || [];
  const currentStatus = (user.account_status || "ACTIVE").toUpperCase();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 text-left space-y-8 animate-fadeIn">
      {/* Toast feedback */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Link to="/users" className="hover:text-indigo-400 transition">
            Users & IAM
          </Link>
          <span>/</span>
          <span className="text-gray-200 font-mono truncate max-w-xs">{user.full_name || user.email}</span>
        </div>
        <button
          onClick={() => navigate("/users")}
          className="inline-flex items-center gap-1.5 rounded-xl border border-gray-800 bg-gray-900/60 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 transition"
        >
          <span>←</span> Back to Users
        </button>
      </div>

      {/* Top Profile & Header Card */}
      <div className="rounded-3xl border border-gray-800 bg-gray-900/60 p-6 sm:p-8 backdrop-blur-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 text-2xl font-bold shadow-lg shadow-indigo-600/10">
              {user.full_name ? user.full_name[0].toUpperCase() : user.email[0].toUpperCase()}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  {user.full_name || "Unnamed User"}
                </h1>
                <UserStatusBadge status={user.account_status} />
                {isSelf && (
                  <span className="inline-flex items-center rounded-full bg-purple-950/70 border border-purple-500/40 px-2 py-0.5 text-[10px] font-bold text-purple-300">
                    Current Authenticated User
                  </span>
                )}
              </div>
              <p className="text-sm font-mono text-gray-300">{user.email}</p>
              <div className="flex items-center gap-2 text-[11px] text-gray-500 pt-1">
                <span>UUID:</span>
                <span className="font-mono text-gray-400 select-all">{user.id}</span>
              </div>
            </div>
          </div>

          {/* Account Status Transition Controls */}
          {isAdmin && (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              {currentStatus !== "ACTIVE" && (
                <button
                  onClick={() => setStatusToChange("ACTIVE")}
                  className="rounded-xl border border-emerald-500/30 bg-emerald-950/40 px-3.5 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/60 transition cursor-pointer"
                >
                  ✓ Activate Account
                </button>
              )}

              {currentStatus === "ACTIVE" && (
                <button
                  onClick={() => setStatusToChange("SUSPENDED")}
                  disabled={isSelf}
                  title={isSelf ? "You cannot suspend your own active account" : "Temporarily suspend user access"}
                  className="rounded-xl border border-amber-500/30 bg-amber-950/40 px-3.5 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-900/60 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ⏸ Suspend
                </button>
              )}

              {currentStatus !== "DEACTIVATED" && (
                <button
                  onClick={() => setStatusToChange("DEACTIVATED")}
                  disabled={isSelf}
                  title={isSelf ? "You cannot deactivate your own active account" : "Revoke authentication and deactivate account"}
                  className="rounded-xl border border-red-500/30 bg-red-950/40 px-3.5 py-2 text-xs font-semibold text-red-300 hover:bg-red-900/60 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ✕ Deactivate
                </button>
              )}
            </div>
          )}
        </div>

        {/* Self-Protection Banner */}
        {isSelf && (
          <div className="rounded-2xl border border-purple-500/30 bg-purple-950/30 p-4 text-xs text-purple-200 flex items-start gap-3">
            <span className="text-base">🛡️</span>
            <div>
              <p className="font-bold">Self-Lockout Protection Active</p>
              <p className="text-purple-300/80 text-[11px] mt-0.5">
                This is your currently authenticated session. Account deactivation and revocation of your own ADMIN role are defensively blocked both in the UI and enforced server-side.
              </p>
            </div>
          </div>
        )}

        {/* Security & Lifecycle Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-gray-800/80">
          <div>
            <div className="text-[10px] uppercase font-bold text-gray-500">MFA Status</div>
            <div className="mt-1 flex items-center gap-1.5 text-xs font-semibold">
              {user.is_mfa_enabled ? (
                <span className="inline-flex items-center gap-1 text-emerald-400">
                  <span>🔒</span> Enrolled (TOTP)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-gray-400">
                  <span>🔓</span> Disabled
                </span>
              )}
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-gray-500">Email Verification</div>
            <div className="mt-1 flex items-center gap-1.5 text-xs font-semibold">
              {(user.is_verified ?? (user.account_status !== "PENDING_VERIFICATION")) ? (
                <span className="text-emerald-400">● Verified</span>
              ) : (
                <span className="text-amber-400">○ Pending OTP</span>
              )}
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-gray-500">Member Since</div>
            <div className="mt-1 text-xs text-gray-300">
              {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-gray-500">Last Profile Update</div>
            <div className="mt-1 text-xs text-gray-300">
              {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : "—"}
            </div>
          </div>
        </div>
      </div>

      {/* IAM Authorization Grid: Assigned Roles & Effective Permissions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Assigned Roles Card */}
        <div className="lg:col-span-1 rounded-2xl border border-gray-800 bg-gray-900/40 p-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">🛡️</span>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Assigned Roles
                </h3>
              </div>
              <span className="text-xs font-mono text-gray-400">({assignedRoles.length})</span>
            </div>

            <p className="text-xs text-gray-400">
              Roles represent coarse-grained identity bundles. Granular permissions are dynamically resolved from assigned roles.
            </p>

            <div className="space-y-2 pt-2">
              {assignedRoles.length === 0 ? (
                <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4 text-center text-xs text-gray-400">
                  No roles currently assigned. User holds default GUEST capabilities.
                </div>
              ) : (
                assignedRoles.map((role) => {
                  const isRoleAdmin = role.toUpperCase() === "ADMIN";
                  const cannotRevoke = isSelf && isRoleAdmin;

                  return (
                    <div
                      key={role}
                      className="flex items-center justify-between rounded-xl border border-gray-800 bg-gray-900/80 p-3"
                    >
                      <RoleBadge role={role} size="md" />

                      {isAdmin && (
                        <button
                          onClick={() => setRoleToRevoke(role)}
                          disabled={cannotRevoke}
                          title={cannotRevoke ? "Self-protection: Cannot revoke your own ADMIN role" : `Revoke ${role} role`}
                          className="rounded-lg border border-red-500/30 bg-red-950/20 px-2.5 py-1 text-[11px] font-semibold text-red-400 hover:bg-red-900/40 transition cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {isAdmin && (
            <div className="pt-6 mt-4 border-t border-gray-800/80">
              <button
                onClick={() => setIsRoleModalOpen(true)}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 transition cursor-pointer"
              >
                <span>➕</span> Grant Additional Role
              </button>
            </div>
          )}
        </div>

        {/* Right: Effective Permissions Panel */}
        <div className="lg:col-span-2">
          <EffectivePermissionsPanel
            permissions={effectivePermissions}
            loading={permissionsLoading}
          />
        </div>
      </div>

      {/* Linked Patron Borrowing Activity */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-base">📖</span>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Patron Circulation Activity
            </h3>
          </div>
          <span className="text-xs text-gray-400">Recent checkouts</span>
        </div>

        {borrowingsLoading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-12 bg-gray-800/50 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : borrowings.length === 0 ? (
          <div className="rounded-xl border border-gray-800/80 bg-gray-950/40 p-6 text-center text-xs text-gray-400">
            No circulation records found for this patron.
          </div>
        ) : (
          <div className="space-y-2">
            {borrowings.map((b) => (
              <div
                key={b.id}
                className="flex items-center justify-between rounded-xl border border-gray-800 bg-gray-900/60 p-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-white">{b.book_title || "Library Book"}</div>
                  <div className="text-[11px] text-gray-400 font-mono">Copy: {b.copy_identifier}</div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${
                      b.status === "ACTIVE"
                        ? "bg-blue-950/80 border border-blue-500/40 text-blue-400"
                        : b.status === "OVERDUE"
                        ? "bg-red-950/80 border border-red-500/40 text-red-400"
                        : "bg-emerald-950/80 border border-emerald-500/40 text-emerald-400"
                    }`}
                  >
                    {b.status}
                  </span>
                  <div className="text-[10px] text-gray-500 mt-0.5">
                    Due: {new Date(b.due_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Role Assignment Modal */}
      {isRoleModalOpen && (
        <RoleAssignmentModal
          isOpen={isRoleModalOpen}
          onClose={() => setIsRoleModalOpen(false)}
          user={user}
          userId={user.id}
          userName={user.full_name || user.email}
          existingRoles={assignedRoles}
          currentRoles={assignedRoles}
          onSuccess={handleRoleGranted}
        />
      )}

      {/* Role Revoke Confirmation */}
      {roleToRevoke && (
        <ConfirmDialog
          isOpen={Boolean(roleToRevoke)}
          title={`Revoke Role: ${roleToRevoke}`}
          message={`Are you sure you want to revoke the "${roleToRevoke}" role from ${user.full_name || user.email}? The user will immediately lose all permissions derived from this role upon next token issuance or request.`}
          confirmLabel={isProcessing ? "Revoking..." : "Confirm Revoke"}
          confirmVariant="danger"
          onConfirm={handleConfirmRoleRevoke}
          onCancel={() => setRoleToRevoke(null)}
          loading={isProcessing}
        />
      )}

      {/* Status Transition Confirmation */}
      {statusToChange && (
        <ConfirmDialog
          isOpen={Boolean(statusToChange)}
          title={`Update Account Status to ${statusToChange}`}
          message={
            statusToChange === "DEACTIVATED"
              ? `Deactivating ${user.full_name || user.email} will immediately invalidate active sessions and prevent the user from authenticating. Are you sure?`
              : statusToChange === "SUSPENDED"
              ? `Suspending ${user.full_name || user.email} will temporarily block borrowing and authenticated actions. Are you sure?`
              : `Activating ${user.full_name || user.email} will restore normal access privileges.`
          }
          confirmLabel={isProcessing ? "Updating..." : `Confirm ${statusToChange}`}
          confirmVariant={statusToChange === "ACTIVE" ? "primary" : "danger"}
          onConfirm={handleConfirmStatusChange}
          onCancel={() => setStatusToChange(null)}
          loading={isProcessing}
        />
      )}
    </div>
  );
}

export default UserDetailsPage;
