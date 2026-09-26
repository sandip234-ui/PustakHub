/**
 * IssueBookModal — Modal dialog for issuing a physical book copy to a borrower.
 *
 * Supports staff user/borrower search, copy selection, and loan period configuration.
 */

import { useEffect, useState } from "react";
import circulationService from "../services/circulation.service";

export function IssueBookModal({
  isOpen,
  book = null,
  copy = null,
  availableCopies = [],
  onClose,
  onSuccess,
}) {
  if (!isOpen) return null;

  return (
    <IssueBookModalContent
      key={copy ? copy.id : book ? book.id : "new-issue"}
      book={book}
      copy={copy}
      availableCopies={availableCopies}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}

function IssueBookModalContent({
  book,
  copy,
  availableCopies = [],
  onClose,
  onSuccess,
}) {
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState("");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedCopyId, setSelectedCopyId] = useState(() => copy?.id || (availableCopies[0]?.id || ""));
  const [loanPeriodDays, setLoanPeriodDays] = useState(14);

  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    let isMounted = true;
    async function initUsers() {
      setIsLoadingUsers(true);
      try {
        const data = await circulationService.getUsers();
        if (isMounted) {
          setUsers(Array.isArray(data) ? data : data.items || []);
        }
      } catch {
        if (isMounted) {
          setUsers([]);
        }
      } finally {
        if (isMounted) {
          setIsLoadingUsers(false);
        }
      }
    }

    initUsers();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredUsers = users.filter((u) => {
    if (!userSearch.trim()) return true;
    const query = userSearch.toLowerCase();
    return (
      (u.full_name && u.full_name.toLowerCase().includes(query)) ||
      (u.email && u.email.toLowerCase().includes(query)) ||
      (u.id && u.id.toLowerCase().includes(query))
    );
  });

  const validate = () => {
    const errs = {};
    if (!selectedUserId) {
      errs.user_id = "Please select or specify a borrower.";
    }
    if (!selectedCopyId) {
      errs.copy_id = "Please select an available physical copy.";
    }
    if (!loanPeriodDays || loanPeriodDays < 1 || loanPeriodDays > 90) {
      errs.loan_period_days = "Loan period must be between 1 and 90 days.";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const calculateDueDate = () => {
    const due = new Date();
    due.setDate(due.getDate() + Number(loanPeriodDays || 14));
    return due.toLocaleDateString(undefined, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError(null);

    const payload = {
      user_id: selectedUserId,
      book_copy_id: selectedCopyId,
      loan_period_days: Number(loanPeriodDays),
    };

    try {
      const result = await circulationService.issueBook(payload);
      onSuccess(result);
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to issue book copy.";
      setApiError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-lg rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="issue-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">📤</span>
            <div>
              <h3 id="issue-modal-title" className="text-lg font-bold text-white">
                Issue Book Loan
              </h3>
              {book && (
                <p className="text-xs text-indigo-400 truncate max-w-xs">{book.title}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-800 hover:text-white transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* API Error Box */}
        {apiError && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-xs text-red-300">
            <strong>Circulation Error:</strong> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Borrower Selector */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Select Borrower (Library Member) <span className="text-red-400">*</span>
            </label>

            {users.length > 0 ? (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Type name or email to filter members..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                />
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full rounded-xl border border-gray-700 bg-gray-800/90 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
                  required
                >
                  <option value="">-- Choose Member ({filteredUsers.length} available) --</option>
                  {filteredUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.email}) — [{u.roles?.join(", ") || "STUDENT"}]
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <input
                  type="text"
                  placeholder="Enter User UUID (e.g. 550e8400-e29b-41d4-a716-446655440000)"
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3 py-2 text-xs text-white font-mono placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                  required
                />
                {isLoadingUsers && (
                  <p className="mt-1 text-[11px] text-gray-400">Loading library members...</p>
                )}
              </div>
            )}
            {errors.user_id && (
              <p className="mt-1 text-xs text-red-400">{errors.user_id}</p>
            )}
          </div>

          {/* Physical Copy Selection */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Physical Copy Barcode <span className="text-red-400">*</span>
            </label>

            {copy ? (
              <div className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-800/60 p-3">
                <div>
                  <span className="font-mono text-sm font-bold text-white">
                    {copy.copy_identifier}
                  </span>
                  <p className="text-[11px] text-gray-400">
                    Location: {copy.shelf_location || "Standard Stacks"}
                  </p>
                </div>
                <span className="inline-flex items-center rounded-full bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
                  Available
                </span>
              </div>
            ) : availableCopies.length > 0 ? (
              <select
                value={selectedCopyId}
                onChange={(e) => setSelectedCopyId(e.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-gray-800/90 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer font-mono"
                required
              >
                <option value="">-- Choose Available Copy --</option>
                {availableCopies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.copy_identifier} ({c.shelf_location || "No Shelf"})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="Enter Physical Copy UUID"
                value={selectedCopyId}
                onChange={(e) => setSelectedCopyId(e.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3 py-2 text-xs text-white font-mono focus:border-indigo-500 focus:outline-none"
                required
              />
            )}
            {errors.copy_id && (
              <p className="mt-1 text-xs text-red-400">{errors.copy_id}</p>
            )}
          </div>

          {/* Loan Duration Configuration */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                Loan Duration (Days)
              </label>
              <select
                value={loanPeriodDays}
                onChange={(e) => setLoanPeriodDays(Number(e.target.value))}
                className="w-full rounded-xl border border-gray-700 bg-gray-800/90 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value={7}>7 Days (1 Week)</option>
                <option value={14}>14 Days (2 Weeks - Standard)</option>
                <option value={21}>21 Days (3 Weeks)</option>
                <option value={30}>30 Days (1 Month)</option>
                <option value={60}>60 Days (Semester Extended)</option>
              </select>
              {errors.loan_period_days && (
                <p className="mt-1 text-xs text-red-400">{errors.loan_period_days}</p>
              )}
            </div>

            {/* Calculated Due Date */}
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">
                Calculated Due Date
              </label>
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-2 text-xs font-semibold text-indigo-300">
                📅 {calculateDueDate()}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
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
              disabled={isSubmitting}
              className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? "Issuing Loan..." : "Confirm & Issue Copy"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default IssueBookModal;
