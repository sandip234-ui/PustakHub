/**
 * BorrowingDetailsPage — Single Circulation Transaction Record View.
 *
 * Displays complete bibliographic loan details, borrower identity, due dates,
 * overdue state, fine calculations, and return actions.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import Toast from "../components/Toast";
import usePermissions from "../hooks/usePermissions";
import circulationService from "../services/circulation.service";

export function BorrowingDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { canReturnBook } = usePermissions();

  const [borrow, setBorrow] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Return Dialog State
  const [showReturnDialog, setShowReturnDialog] = useState(false);
  const [isReturning, setIsReturning] = useState(false);
  const [returnError, setReturnError] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const refreshBorrowing = useCallback(async () => {
    try {
      const data = await circulationService.getBorrowingById(id);
      setBorrow(data);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to refresh borrowing record.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  }, [id]);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await circulationService.getBorrowingById(id);
        if (isMounted) {
          setBorrow(data);
        }
      } catch (err) {
        if (isMounted) {
          const msg =
            err.response?.data?.detail ||
            err.response?.data?.message ||
            err.message ||
            "Failed to load borrowing record.";
          setError(typeof msg === "string" ? msg : JSON.stringify(msg));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    init();
    return () => {
      isMounted = false;
    };
  }, [id]);

  const handleConfirmReturn = async () => {
    setIsReturning(true);
    setReturnError(null);
    try {
      const result = await circulationService.returnBook(borrow.id);
      if (result.is_overdue && result.fine_amount) {
        showToast(
          `Book returned. An overdue fine of $${Number(result.fine_amount).toFixed(2)} was assessed.`,
          "warning"
        );
      } else {
        showToast(`Book copy returned successfully.`);
      }
      setShowReturnDialog(false);
      refreshBorrowing();
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

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto"></div>
        <p className="mt-4 text-xs text-gray-400">Loading loan transaction details...</p>
      </div>
    );
  }

  if (error || !borrow) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <div className="rounded-2xl border border-red-500/30 bg-red-950/30 p-8">
          <div className="text-4xl mb-3">⚠️</div>
          <h2 className="text-lg font-bold text-white mb-2">Borrowing Record Not Found</h2>
          <p className="text-xs text-gray-300 mb-6">
            {error || "The requested borrowing record does not exist or you lack permission to inspect it."}
          </p>
          <button
            onClick={() => navigate("/borrowings")}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
          >
            ← Back to Borrowings
          </button>
        </div>
      </div>
    );
  }

  const isLoanActive = borrow.status === "ACTIVE" || borrow.status === "OVERDUE";

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 text-left">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Navigation Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-6">
        <Link to="/borrowings" className="hover:text-indigo-400 transition">
          Circulation & Borrowings
        </Link>
        <span>/</span>
        <span className="font-mono text-gray-300 truncate max-w-xs">{borrow.id}</span>
      </div>

      {/* Main Loan Header */}
      <div className="rounded-3xl border border-gray-800 bg-gray-900/60 p-6 sm:p-8 backdrop-blur-xl mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-gray-800">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                Loan Transaction Reference
              </span>
              <span className="font-mono text-xs text-gray-500">#{borrow.id.slice(0, 8)}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {borrow.book_title || "Library Book Holding"}
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Physical Barcode: <span className="font-mono font-bold text-gray-200">{borrow.copy_identifier || "—"}</span>
            </p>
          </div>

          <div className="flex flex-col sm:items-end gap-2">
            <div>
              {borrow.status === "RETURNED" ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 border border-gray-700 px-3 py-1 text-xs font-semibold text-gray-300">
                  <span className="h-2 w-2 rounded-full bg-gray-400"></span>
                  Returned
                </span>
              ) : borrow.is_overdue || borrow.status === "OVERDUE" ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-red-950/80 border border-red-500/40 px-3 py-1 text-xs font-semibold text-red-400 animate-pulse">
                  <span className="h-2 w-2 rounded-full bg-red-400"></span>
                  Overdue ({borrow.overdue_days || 1} Days)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 px-3 py-1 text-xs font-semibold text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                  Active Loan
                </span>
              )}
            </div>

            {isLoanActive && canReturnBook && (
              <button
                onClick={() => {
                  setReturnError(null);
                  setShowReturnDialog(true);
                }}
                className="mt-2 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer"
              >
                <span>📥</span> Process Book Return
              </button>
            )}
          </div>
        </div>

        {/* Timeline & Metadata Grid */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
            <span className="text-[10px] uppercase font-bold text-gray-500 block">Issued On</span>
            <span className="text-sm font-semibold text-white mt-1 block">
              📅 {new Date(borrow.issued_at).toLocaleDateString()}
            </span>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
            <span className="text-[10px] uppercase font-bold text-gray-500 block">Due Date</span>
            <span
              className={`text-sm font-semibold mt-1 block ${
                borrow.is_overdue ? "text-red-400" : "text-white"
              }`}
            >
              ⏰ {new Date(borrow.due_at).toLocaleDateString()}
            </span>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
            <span className="text-[10px] uppercase font-bold text-gray-500 block">Returned On</span>
            <span className="text-sm font-semibold text-gray-300 mt-1 block">
              {borrow.returned_at
                ? `✅ ${new Date(borrow.returned_at).toLocaleDateString()}`
                : "⏳ Not returned yet"}
            </span>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
            <span className="text-[10px] uppercase font-bold text-gray-500 block">Borrower Member</span>
            <span className="text-sm font-semibold text-indigo-300 mt-1 block truncate">
              👤 {borrow.user_name || "Library Member"}
            </span>
            <span className="text-[10px] text-gray-500 truncate block">
              {borrow.user_email || borrow.user_id}
            </span>
          </div>
        </div>
      </div>

      {/* Associated Fine Assessment Card */}
      {((borrow.fine_amount && Number(borrow.fine_amount) > 0) || borrow.is_overdue) && (
        <div className="rounded-3xl border border-red-500/30 bg-red-950/20 p-6 sm:p-8 backdrop-blur-xl mb-6">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">💵</span>
            <h2 className="text-lg font-bold text-red-300">Overdue Fine Assessment</h2>
          </div>
          <p className="text-xs text-gray-300 mb-4 leading-relaxed">
            This borrowing transaction has accumulated an overdue fine in accordance with the library fine policy.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-2xl bg-gray-900/80 p-4 border border-red-500/20">
              <span className="text-[10px] uppercase font-bold text-gray-400 block">Fine Amount</span>
              <span className="text-xl font-extrabold text-red-400 mt-1 block">
                ${borrow.fine_amount ? Number(borrow.fine_amount).toFixed(2) : "0.00"}
              </span>
            </div>

            <div className="rounded-2xl bg-gray-900/80 p-4 border border-red-500/20">
              <span className="text-[10px] uppercase font-bold text-gray-400 block">Payment Status</span>
              <span className="text-sm font-bold text-amber-400 mt-1 block">
                ● {borrow.fine_status || "PENDING"}
              </span>
            </div>

            <div className="rounded-2xl bg-gray-900/80 p-4 border border-red-500/20">
              <span className="text-[10px] uppercase font-bold text-gray-400 block">Overdue Duration</span>
              <span className="text-sm font-bold text-white mt-1 block">
                {borrow.overdue_days || 1} day(s)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Actions and Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-800">
        <Link
          to="/borrowings"
          className="rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-xs font-semibold text-gray-300 hover:bg-gray-700 transition"
        >
          ← Back to Loans
        </Link>

        {borrow.book_id && (
          <Link
            to={`/books/${borrow.book_id}`}
            className="rounded-xl bg-gray-800 px-4 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-600 hover:text-white transition"
          >
            View Book Bibliographic Record →
          </Link>
        )}
      </div>

      {/* Return Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showReturnDialog}
        title="Confirm Book Return"
        message="Checking in this book copy will update its inventory status to AVAILABLE and calculate any overdue penalty fees."
        itemName={borrow.book_title}
        confirmText="Check-in & Return"
        isDanger={false}
        isLoading={isReturning}
        error={returnError}
        onConfirm={handleConfirmReturn}
        onCancel={() => {
          setShowReturnDialog(false);
          setReturnError(null);
        }}
      />
    </div>
  );
}

export default BorrowingDetailsPage;
