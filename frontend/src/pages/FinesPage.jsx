/**
 * FinesPage — Library Fines and Fee Accounts Dashboard.
 *
 * Displays assessed fines, overdue penalty fee records, payment statuses,
 * and associated borrowing links.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import usePermissions from "../hooks/usePermissions";
import useRealtime from "../hooks/useRealtime";
import { RealtimeEventType } from "../services/realtime.service";
import circulationService from "../services/circulation.service";

export function FinesPage() {
  const { isStaff } = usePermissions();

  const [fines, setFines] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);

  const [activeTab, setActiveTab] = useState("ALL"); // ALL, PENDING, PAID, WAIVED
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadFines = useCallback(async () => {
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

      const data = await circulationService.getFines(params);
      setFines(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.pages || 1);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to load fine records.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, activeTab]);

  const { subscribeMany } = useRealtime();

  useEffect(() => {
    const handler = setTimeout(() => {
      loadFines();
    }, 150);

    const unsubscribe = subscribeMany(
      [
        RealtimeEventType.FINE_ISSUED,
        RealtimeEventType.FINE_PAID,
        RealtimeEventType.FINE_WAIVED,
        RealtimeEventType.COPY_RETURNED,
        RealtimeEventType.SYSTEM_RECONNECTED,
      ],
      () => {
        loadFines();
      }
    );

    return () => {
      clearTimeout(handler);
      unsubscribe();
    };
  }, [loadFines, subscribeMany]);

  const getStatusBadge = (status) => {
    switch ((status || "").toUpperCase()) {
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-950/80 border border-amber-500/40 px-2.5 py-0.5 text-xs font-semibold text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
            Pending
          </span>
        );
      case "PAID":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            Paid
          </span>
        );
      case "WAIVED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-950/80 border border-blue-500/40 px-2.5 py-0.5 text-xs font-semibold text-blue-400">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400"></span>
            Waived
          </span>
        );
      default:
        return (
          <span className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs text-gray-400">
            {status}
          </span>
        );
    }
  };

  const getReasonBadge = (reason) => {
    switch ((reason || "").toUpperCase()) {
      case "OVERDUE":
        return (
          <span className="inline-flex items-center rounded-md bg-red-950/60 border border-red-500/30 px-2 py-0.5 text-[10px] font-semibold text-red-300">
            ⏰ Overdue Return
          </span>
        );
      case "LOST":
        return (
          <span className="inline-flex items-center rounded-md bg-purple-950/60 border border-purple-500/30 px-2 py-0.5 text-[10px] font-semibold text-purple-300">
            📦 Lost Item
          </span>
        );
      case "DAMAGED":
        return (
          <span className="inline-flex items-center rounded-md bg-amber-950/60 border border-amber-500/30 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
            ⚠️ Damaged
          </span>
        );
      default:
        return <span className="text-gray-400 text-xs">{reason || "Standard Fine"}</span>;
    }
  };

  const totalPendingAmount = fines
    .filter((f) => f.status === "PENDING")
    .reduce((sum, f) => sum + Number(f.amount || 0), 0);

  const totalPaidAmount = fines
    .filter((f) => f.status === "PAID")
    .reduce((sum, f) => sum + Number(f.amount || 0), 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-left">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">💵</span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Fines & Financial Accounts
            </h1>
          </div>
          <p className="mt-1 text-sm text-gray-400">
            {isStaff
              ? "Inspect assessed library penalty fees, lost copy assessments, and settlement logs"
              : "Review your library fines, overdue assessments, and account balance"}
          </p>
        </div>

        <Link
          to="/borrowings"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gray-800 px-4 py-2.5 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition"
        >
          <span>📖</span> View Borrowings
        </Link>
      </div>

      {/* Stats Summary Cards */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
          <span className="text-xs font-semibold text-gray-400 uppercase">Assessed Records</span>
          <p className="text-2xl font-bold text-white mt-1">{total}</p>
        </div>

        <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-4">
          <span className="text-xs font-semibold text-amber-400 uppercase">
            Pending Balance (Page)
          </span>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            ${totalPendingAmount.toFixed(2)}
          </p>
        </div>

        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-4">
          <span className="text-xs font-semibold text-emerald-400 uppercase">
            Paid Settlement (Page)
          </span>
          <p className="text-2xl font-bold text-emerald-400 mt-1">
            ${totalPaidAmount.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Tab Filters */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-800 bg-gray-900/60 p-3 backdrop-blur-xl">
        <div className="flex items-center gap-1.5">
          {["ALL", "PENDING", "PAID", "WAIVED"].map((tab) => (
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
                ? "All Fines"
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

      {/* Fines Table */}
      <div className="mt-6 rounded-2xl border border-gray-800 bg-gray-900/50 backdrop-blur-xl overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto"></div>
            <p className="mt-4 text-xs text-gray-400">Loading fine ledger records...</p>
          </div>
        ) : fines.length === 0 ? (
          <div className="py-16 text-center max-w-sm mx-auto">
            <div className="text-4xl mb-3">🎉</div>
            <h3 className="text-base font-bold text-white mb-1">No Fines Found</h3>
            <p className="text-xs text-gray-400 mb-6">
              {activeTab === "ALL"
                ? "No outstanding penalty fines or charges are recorded on file."
                : `No fines found under status "${activeTab}".`}
            </p>
            <Link
              to="/catalog"
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
            >
              Browse Catalog
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-950/60 text-[11px] uppercase font-semibold text-gray-400">
                <tr>
                  <th scope="col" className="py-3.5 pl-6 pr-3">
                    Fine Reference
                  </th>
                  {isStaff && (
                    <th scope="col" className="px-3 py-3.5">
                      Borrower
                    </th>
                  )}
                  <th scope="col" className="px-3 py-3.5">
                    Reason
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Amount
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Assessed Date
                  </th>
                  <th scope="col" className="py-3.5 pl-3 pr-6 text-right">
                    Borrowing Link
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {fines.map((fine) => (
                  <tr key={fine.id} className="hover:bg-gray-800/30 transition">
                    {/* Fine Reference */}
                    <td className="py-4 pl-6 pr-3 font-mono font-semibold text-white">
                      #{fine.id.slice(0, 8)}
                    </td>

                    {/* Borrower (Staff only) */}
                    {isStaff && (
                      <td className="px-3 py-4">
                        <span className="font-medium text-gray-200 block">
                          {fine.user_name || "Member"}
                        </span>
                        <span className="text-[11px] text-gray-400 truncate max-w-[150px] block">
                          {fine.user_email || fine.user_id}
                        </span>
                      </td>
                    )}

                    {/* Reason */}
                    <td className="px-3 py-4">{getReasonBadge(fine.reason)}</td>

                    {/* Amount */}
                    <td className="px-3 py-4 font-bold text-sm text-white">
                      ${Number(fine.amount || 0).toFixed(2)}
                    </td>

                    {/* Status */}
                    <td className="px-3 py-4">{getStatusBadge(fine.status)}</td>

                    {/* Assessed Date */}
                    <td className="px-3 py-4 text-gray-400">
                      {new Date(fine.created_at).toLocaleDateString()}
                    </td>

                    {/* Action / Link */}
                    <td className="py-4 pl-3 pr-6 text-right">
                      {fine.borrow_record_id ? (
                        <Link
                          to={`/borrowings/${fine.borrow_record_id}`}
                          className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1 text-xs font-medium text-indigo-300 hover:bg-indigo-600 hover:text-white transition"
                        >
                          View Loan →
                        </Link>
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
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
            <strong className="text-white">{totalPages}</strong> ({total} fines)
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
    </div>
  );
}

export default FinesPage;
