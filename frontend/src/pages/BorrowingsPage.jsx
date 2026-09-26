/**
 * BorrowingsPage — Member & Staff Circulation Management Dashboard.
 *
 * Provides real-time tracking of active loans, due dates, overdue statuses,
 * return workflows, and loan history.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import IssueBookModal from "../components/IssueBookModal";
import PermissionGate from "../components/PermissionGate";
import Toast from "../components/Toast";
import usePermissions from "../hooks/usePermissions";
import useRealtime from "../hooks/useRealtime";
import { RealtimeEventType } from "../services/realtime.service";
import circulationService from "../services/circulation.service";

export function BorrowingsPage() {
  const { isStaff, canReturnBook } = usePermissions();

  const [borrowings, setBorrowings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);

  const [activeTab, setActiveTab] = useState("ALL"); // ALL, ACTIVE, OVERDUE, RETURNED
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Return Book State
  const [borrowToReturn, setBorrowToReturn] = useState(null);
  const [isReturning, setIsReturning] = useState(false);
  const [returnError, setReturnError] = useState(null);

  // Issue Modal State (for staff)
  const [isIssueModalOpen, setIsIssueModalOpen] = useState(false);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadBorrowings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (activeTab !== "ALL") {
        params.status = activeTab;
      }

      const data = await circulationService.getBorrowings(params);
      setBorrowings(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.pages || 1);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to load borrowing records.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, activeTab]);

  const { subscribeMany } = useRealtime();

  useEffect(() => {
    const handler = setTimeout(() => {
      loadBorrowings();
    }, 150);

    const unsubscribe = subscribeMany(
      [
        RealtimeEventType.COPY_ISSUED,
        RealtimeEventType.COPY_RETURNED,
        RealtimeEventType.FINE_ISSUED,
        RealtimeEventType.SYSTEM_RECONNECTED,
      ],
      () => {
        loadBorrowings();
      }
    );

    return () => {
      clearTimeout(handler);
      unsubscribe();
    };
  }, [loadBorrowings, subscribeMany]);

  const handleReturnPrompt = (record, e) => {
    e.preventDefault();
    e.stopPropagation();
    setBorrowToReturn(record);
    setReturnError(null);
  };

  const handleConfirmReturn = async () => {
    if (!borrowToReturn) return;
    setIsReturning(true);
    setReturnError(null);

    try {
      const result = await circulationService.returnBook(borrowToReturn.id);
      if (result.is_overdue && result.fine_amount) {
        showToast(
          `Book returned. An overdue fine of $${Number(result.fine_amount).toFixed(2)} was assessed.`,
          "warning"
        );
      } else {
        showToast(`Book "${borrowToReturn.book_title || "copy"}" returned successfully.`);
      }
      setBorrowToReturn(null);
      loadBorrowings();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to process return.";
      setReturnError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsReturning(false);
    }
  };

  const getStatusBadge = (borrow) => {
    if (borrow.status === "RETURNED") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 border border-gray-700 px-2.5 py-0.5 text-xs font-semibold text-gray-300">
          <span className="h-1.5 w-1.5 rounded-full bg-gray-400"></span>
          Returned
        </span>
      );
    }
    if (borrow.is_overdue || borrow.status === "OVERDUE") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-950/80 border border-red-500/40 px-2.5 py-0.5 text-xs font-semibold text-red-400 animate-pulse">
          <span className="h-1.5 w-1.5 rounded-full bg-red-400"></span>
          Overdue ({borrow.overdue_days || 1}d)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
        Active Loan
      </span>
    );
  };

  const activeCount = borrowings.filter((b) => b.status === "ACTIVE" && !b.is_overdue).length;
  const overdueCount = borrowings.filter((b) => b.is_overdue || b.status === "OVERDUE").length;
  const returnedCount = borrowings.filter((b) => b.status === "RETURNED").length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-left">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📖</span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Circulation & Borrowings
            </h1>
          </div>
          <p className="mt-1 text-sm text-gray-400">
            {isStaff
              ? "Manage library circulation checkouts, returns, and overdue loan records"
              : "Track your active loans, due dates, and return history"}
          </p>
        </div>

        <PermissionGate permission="book:issue">
          <button
            onClick={() => setIsIssueModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer"
          >
            <span>📤</span> Issue New Loan
          </button>
        </PermissionGate>
      </div>

      {/* Stats Summary */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
          <span className="text-xs font-semibold text-gray-400 uppercase">Total Records</span>
          <p className="text-2xl font-bold text-white mt-1">{total}</p>
        </div>
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-4">
          <span className="text-xs font-semibold text-emerald-400 uppercase">Active Loans</span>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{activeCount}</p>
        </div>
        <div className="rounded-2xl border border-red-500/30 bg-red-950/20 p-4">
          <span className="text-xs font-semibold text-red-400 uppercase">Overdue Loans</span>
          <p className="text-2xl font-bold text-red-400 mt-1">{overdueCount}</p>
        </div>
        <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
          <span className="text-xs font-semibold text-gray-400 uppercase">Returned</span>
          <p className="text-2xl font-bold text-gray-300 mt-1">{returnedCount}</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-800 bg-gray-900/60 p-3 backdrop-blur-xl">
        <div className="flex items-center gap-1.5">
          {["ALL", "ACTIVE", "OVERDUE", "RETURNED"].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                setPage(1);
              }}
              className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                activeTab === tab
                  ? "bg-indigo-600 text-white shadow"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`}
            >
              {tab === "ALL"
                ? "All Loans"
                : tab.charAt(0) + tab.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-400">
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="rounded-xl border border-gray-700 bg-gray-800/90 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
          >
            <option value={10}>10 / page</option>
            <option value={20}>20 / page</option>
            <option value={50}>50 / page</option>
          </select>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-950/30 p-4 text-sm text-red-300">
          ❌ {error}
        </div>
      )}

      {/* Borrowings Table / Cards */}
      <div className="mt-6 rounded-2xl border border-gray-800 bg-gray-900/50 backdrop-blur-xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto"></div>
            <p className="mt-4 text-xs text-gray-400">Loading circulation records...</p>
          </div>
        ) : borrowings.length === 0 ? (
          <div className="py-16 text-center max-w-sm mx-auto">
            <div className="text-4xl mb-3">📚</div>
            <h3 className="text-base font-bold text-white mb-1">No Borrowings Found</h3>
            <p className="text-xs text-gray-400 mb-6">
              {activeTab === "ALL"
                ? "There are no circulation loan transactions recorded yet."
                : `No records found under status "${activeTab}".`}
            </p>
            <Link
              to="/catalog"
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
            >
              Browse Catalog Titles
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-950/60 text-[11px] uppercase font-semibold text-gray-400">
                <tr>
                  <th scope="col" className="py-3.5 pl-6 pr-3">
                    Book Title & Copy
                  </th>
                  {isStaff && (
                    <th scope="col" className="px-3 py-3.5">
                      Borrower
                    </th>
                  )}
                  <th scope="col" className="px-3 py-3.5">
                    Issued Date
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Due Date
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center">
                    Fine
                  </th>
                  <th scope="col" className="py-3.5 pl-3 pr-6 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {borrowings.map((borrow) => {
                  const isLoanActive = borrow.status === "ACTIVE" || borrow.status === "OVERDUE";

                  return (
                    <tr key={borrow.id} className="hover:bg-gray-800/30 transition">
                      {/* Book & Copy */}
                      <td className="py-4 pl-6 pr-3">
                        <Link
                          to={`/borrowings/${borrow.id}`}
                          className="font-bold text-white hover:text-indigo-400 transition block truncate max-w-xs"
                          title={borrow.book_title || "Book Title"}
                        >
                          {borrow.book_title || "Library Title"}
                        </Link>
                        <span className="font-mono text-[11px] text-gray-400">
                          Barcode: {borrow.copy_identifier || "—"}
                        </span>
                      </td>

                      {/* Borrower (Staff view) */}
                      {isStaff && (
                        <td className="px-3 py-4">
                          <span className="font-medium text-gray-200 block">
                            {borrow.user_name || "Member"}
                          </span>
                          <span className="text-[11px] text-gray-400 truncate max-w-[150px] block">
                            {borrow.user_email || borrow.user_id}
                          </span>
                        </td>
                      )}

                      {/* Issue Date */}
                      <td className="px-3 py-4 text-gray-300">
                        {new Date(borrow.issued_at).toLocaleDateString()}
                      </td>

                      {/* Due Date */}
                      <td className="px-3 py-4">
                        <span
                          className={
                            borrow.is_overdue
                              ? "font-semibold text-red-400"
                              : "text-gray-300"
                          }
                        >
                          {new Date(borrow.due_at).toLocaleDateString()}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-3 py-4">{getStatusBadge(borrow)}</td>

                      {/* Fine */}
                      <td className="px-3 py-4 text-center">
                        {borrow.fine_amount && Number(borrow.fine_amount) > 0 ? (
                          <span className="inline-flex items-center rounded-md bg-red-950/70 border border-red-500/30 px-2 py-0.5 text-[11px] font-semibold text-red-300">
                            ${Number(borrow.fine_amount).toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-[11px]">—</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-4 pl-3 pr-6 text-right space-x-2">
                        {isLoanActive && canReturnBook && (
                          <button
                            onClick={(e) => handleReturnPrompt(borrow, e)}
                            className="rounded-lg border border-indigo-500/40 bg-indigo-950/40 px-2.5 py-1 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/60 transition cursor-pointer"
                          >
                            Return
                          </button>
                        )}
                        <Link
                          to={`/borrowings/${borrow.id}`}
                          className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition"
                        >
                          Details →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-gray-800 pt-6">
          <div className="text-xs text-gray-400">
            Page <strong className="text-white">{page}</strong> of{" "}
            <strong className="text-white">{totalPages}</strong> ({total} transactions)
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-xl border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition cursor-pointer disabled:opacity-40"
            >
              ← Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="rounded-xl border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition cursor-pointer disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Issue Modal */}
      <IssueBookModal
        isOpen={isIssueModalOpen}
        onClose={() => setIsIssueModalOpen(false)}
        onSuccess={(issued) => {
          showToast(`Book loan issued to ${issued.user_name || "member"} successfully.`);
          loadBorrowings();
        }}
      />

      {/* Return Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(borrowToReturn)}
        title="Process Book Return?"
        message="Are you sure you want to check in this borrowed book copy? The system will calculate any applicable overdue fines upon check-in."
        itemName={borrowToReturn?.book_title}
        confirmText="Confirm Return"
        isDanger={false}
        isLoading={isReturning}
        error={returnError}
        onConfirm={handleConfirmReturn}
        onCancel={() => {
          setBorrowToReturn(null);
          setReturnError(null);
        }}
      />
    </div>
  );
}

export default BorrowingsPage;
