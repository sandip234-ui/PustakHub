/**
 * RoleAssignmentModal — Modal dialog for granting system roles to a user.
 */

import { useEffect, useState } from "react";
import userService from "../services/user.service";

export function RoleAssignmentModal({
  isOpen,
  user,
  userId,
  userName,
  existingRoles,
  currentRoles,
  onClose,
  onSuccess,
}) {
  const resolvedUser =
    user ||
    (userId
      ? {
          id: userId,
          full_name: userName || "User",
          email: typeof userName === "string" && userName.includes("@") ? userName : "",
        }
      : null);
  const resolvedRoles = existingRoles || currentRoles || [];

  if (!isOpen || !resolvedUser) return null;

  return (
    <RoleAssignmentModalContent
      key={resolvedUser.id}
      user={resolvedUser}
      existingRoles={resolvedRoles}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}

const SUPPORTED_ASSIGNABLE_ROLES = ["ADMIN", "LIBRARIAN", "STUDENT"];

const FALLBACK_ASSIGNABLE_ROLES = [
  { id: "admin", name: "ADMIN", description: "Full system administration and IAM controls" },
  { id: "librarian", name: "LIBRARIAN", description: "Catalog and circulation management" },
  { id: "student", name: "STUDENT", description: "Standard patron book borrowing" },
];

function RoleAssignmentModalContent({
  user,
  existingRoles = [],
  onClose,
  onSuccess,
}) {
  const [availableRoles, setAvailableRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadRoles() {
      setIsLoading(true);
      try {
        const roles = await userService.getRoles({ assignable_only: true });
        if (isMounted) {
          const roleList = Array.isArray(roles) ? roles : [];
          const filtered = roleList.filter((r) =>
            SUPPORTED_ASSIGNABLE_ROLES.includes((r.name || "").toUpperCase())
          );
          setAvailableRoles(filtered.length > 0 ? filtered : FALLBACK_ASSIGNABLE_ROLES);
        }
      } catch {
        if (isMounted) {
          // Fallback to standard assignable application roles if API query fails
          setAvailableRoles(FALLBACK_ASSIGNABLE_ROLES);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadRoles();
    return () => {
      isMounted = false;
    };
  }, []);

  const existingRoleNames = (existingRoles || []).map((r) =>
    typeof r === "string" ? r.toUpperCase() : r?.name?.toUpperCase() || ""
  );

  const assignableRoles = availableRoles.filter(
    (r) =>
      SUPPORTED_ASSIGNABLE_ROLES.includes((r.name || "").toUpperCase()) &&
      !existingRoleNames.includes((r.name || "").toUpperCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedRole) {
      setError("Please select a role to assign.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const updatedUser = await userService.assignRole(user.id, selectedRole);
      onSuccess(selectedRole, updatedUser);
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to assign role to user.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="assign-role-title"
      >
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">🛡️</span>
            <div>
              <h3 id="assign-role-title" className="text-base font-bold text-white">
                Assign Role to User
              </h3>
              <p className="text-xs text-indigo-400 truncate max-w-xs">
                {user.full_name} ({user.email})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-800 hover:text-white transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-xs text-red-300">
            <strong>Role Assignment Error:</strong> {error}
          </div>
        )}

        {selectedRole === "ADMIN" && (
          <div className="mt-4 rounded-xl border border-purple-500/40 bg-purple-950/40 p-3 text-xs text-purple-200 flex items-start gap-2">
            <span className="text-base">⚠️</span>
            <div>
              <strong className="block font-semibold">Elevated Administrative Privilege</strong>
              Assigning the <span className="font-bold">ADMIN</span> role grants broad control over catalog items, user accounts, security settings, and audit logs.
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Select Role to Grant <span className="text-red-400">*</span>
            </label>

            {isLoading ? (
              <div className="h-10 animate-pulse rounded-xl bg-gray-800" />
            ) : assignableRoles.length === 0 ? (
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-3 text-xs text-gray-400">
                User already possesses all available system roles.
              </div>
            ) : (
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
                required
              >
                <option value="">-- Choose Role to Assign --</option>
                {assignableRoles.map((r) => (
                  <option key={r.id || r.name} value={r.name}>
                    {r.name} — {r.description || "System Role"}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || assignableRoles.length === 0 || !selectedRole}
              className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? "Granting Role..." : "Confirm & Grant Role"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RoleAssignmentModal;
