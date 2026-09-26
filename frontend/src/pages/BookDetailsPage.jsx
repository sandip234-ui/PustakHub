/**
 * BookDetailsPage — Detailed Book Metadata and Physical Copy Inventory.
 *
 * Displays bibliographic record, copy availability breakdown, and allows
 * authorized staff (ADMIN / LIBRARIAN) to manage physical copies.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import BookFormModal from "../components/BookFormModal";
import ConfirmDialog from "../components/ConfirmDialog";
import CopyFormModal from "../components/CopyFormModal";
import IssueBookModal from "../components/IssueBookModal";
import PermissionGate from "../components/PermissionGate";
import Toast from "../components/Toast";
import usePermissions from "../hooks/usePermissions";
import catalogService from "../services/catalog.service";

export function BookDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { canUpdateBook, canDeleteBook, canIssueBook } = usePermissions();

  const [book, setBook] = useState(null);
  const [copies, setCopies] = useState([]);
  const [categories, setCategories] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Book Edit/Delete Modals
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [isDeletingBook, setIsDeletingBook] = useState(false);
  const [deleteBookError, setDeleteBookError] = useState(null);
  const [showDeleteBookDialog, setShowDeleteBookDialog] = useState(false);

  // Copy Add/Edit/Delete Modals
  const [isCopyModalOpen, setIsCopyModalOpen] = useState(false);
  const [selectedCopyForEdit, setSelectedCopyForEdit] = useState(null);

  const [copyToDelete, setCopyToDelete] = useState(null);
  const [isDeletingCopy, setIsDeletingCopy] = useState(false);
  const [deleteCopyError, setDeleteCopyError] = useState(null);

  // Issue Loan Modal
  const [isIssueModalOpen, setIsIssueModalOpen] = useState(false);
  const [selectedCopyForIssue, setSelectedCopyForIssue] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const refreshBookData = useCallback(async () => {
    try {
      const [bookData, copyData] = await Promise.all([
        catalogService.getBookById(id),
        catalogService.getBookCopies(id, { page_size: 100 }),
      ]);
      setBook(bookData);
      setCopies(copyData.items || []);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to refresh book record.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  }, [id]);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      setIsLoading(true);
      setError(null);
      try {
        const [bookData, copyData, catData] = await Promise.all([
          catalogService.getBookById(id),
          catalogService.getBookCopies(id, { page_size: 100 }),
          catalogService.getCategories({ page_size: 100 }).catch(() => ({ items: [] })),
        ]);
        if (isMounted) {
          setBook(bookData);
          setCopies(copyData.items || []);
          setCategories(catData.items || []);
        }
      } catch (err) {
        if (isMounted) {
          const msg =
            err.response?.data?.detail ||
            err.response?.data?.message ||
            err.message ||
            "Failed to load book record.";
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

  // Book Delete Handler
  const handleConfirmDeleteBook = async () => {
    setIsDeletingBook(true);
    setDeleteBookError(null);
    try {
      await catalogService.deleteBook(book.id);
      showToast(`Book "${book.title}" deleted.`);
      setTimeout(() => navigate("/catalog"), 1000);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to delete book.";
      setDeleteBookError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsDeletingBook(false);
    }
  };

  // Copy Delete Handler
  const handleConfirmDeleteCopy = async () => {
    if (!copyToDelete) return;
    setIsDeletingCopy(true);
    setDeleteCopyError(null);
    try {
      await catalogService.deleteCopy(copyToDelete.id);
      showToast(`Copy "${copyToDelete.copy_identifier}" deleted.`);
      setCopyToDelete(null);
      refreshBookData();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to delete copy.";
      setDeleteCopyError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsDeletingCopy(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "AVAILABLE":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/70 border border-emerald-500/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            Available
          </span>
        );
      case "BORROWED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-950/70 border border-blue-500/40 px-2.5 py-0.5 text-xs font-semibold text-blue-400">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400"></span>
            Borrowed
          </span>
        );
      case "MAINTENANCE":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-950/70 border border-amber-500/40 px-2.5 py-0.5 text-xs font-semibold text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
            Maintenance
          </span>
        );
      case "LOST":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-950/70 border border-red-500/40 px-2.5 py-0.5 text-xs font-semibold text-red-400">
            <span className="h-1.5 w-1.5 rounded-full bg-red-400"></span>
            Lost
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

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12 text-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto"></div>
        <p className="mt-4 text-sm text-gray-400">Loading bibliographic details...</p>
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <div className="rounded-2xl border border-red-500/30 bg-red-950/30 p-8">
          <div className="text-4xl mb-3">⚠️</div>
          <h2 className="text-xl font-bold text-white mb-2">Book Not Found</h2>
          <p className="text-sm text-gray-300 mb-6">{error || "Requested book could not be found."}</p>
          <Link
            to="/catalog"
            className="rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition"
          >
            ← Back to Catalog
          </Link>
        </div>
      </div>
    );
  }

  const availableCount = copies.filter((c) => c.status === "AVAILABLE").length;
  const borrowedCount = copies.filter((c) => c.status === "BORROWED").length;
  const maintenanceCount = copies.filter((c) => c.status === "MAINTENANCE").length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 text-left">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Navigation Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-6">
        <Link to="/catalog" className="hover:text-indigo-400 transition">
          Catalog
        </Link>
        <span>/</span>
        <span className="text-gray-200 font-medium truncate max-w-sm">{book.title}</span>
      </div>

      {/* Main Bibliographic Card */}
      <div className="rounded-3xl border border-gray-800 bg-gray-900/60 p-6 sm:p-8 backdrop-blur-xl mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center rounded-lg bg-indigo-950/80 border border-indigo-500/30 px-3 py-1 text-xs font-semibold text-indigo-300">
                {book.category_name || "General"}
              </span>
              {book.publication_year && (
                <span className="rounded-lg border border-gray-800 bg-gray-900 px-2.5 py-1 text-xs font-medium text-gray-400">
                  📅 {book.publication_year}
                </span>
              )}
              {book.isbn && (
                <span className="rounded-lg border border-gray-800 bg-gray-900 px-2.5 py-1 font-mono text-xs text-gray-400">
                  ISBN: {book.isbn}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
              {book.title}
            </h1>

            <p className="text-base text-gray-300 font-medium">
              By <span className="text-indigo-400">{book.author}</span>
            </p>

            {book.publisher && (
              <p className="text-xs text-gray-400">
                Published by <strong className="text-gray-200">{book.publisher}</strong>
              </p>
            )}

            {book.description && (
              <div className="mt-4 pt-4 border-t border-gray-800/80">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
                  Synopsis / Abstract
                </h3>
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                  {book.description}
                </p>
              </div>
            )}
          </div>

          {/* Right Summary & Staff Actions */}
          <div className="shrink-0 flex flex-col gap-4 w-full lg:w-72">
            {/* Inventory Quick Stats */}
            <div className="rounded-2xl border border-gray-800 bg-gray-950/70 p-5 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 pb-2 border-b border-gray-800">
                Inventory Availability
              </h3>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-xl bg-gray-900/80 p-2.5 border border-gray-800/80">
                  <span className="text-gray-500 block text-[10px] uppercase">Total Copies</span>
                  <span className="text-lg font-bold text-white">{copies.length}</span>
                </div>
                <div className="rounded-xl bg-emerald-950/30 p-2.5 border border-emerald-500/30">
                  <span className="text-emerald-400 block text-[10px] uppercase">Available</span>
                  <span className="text-lg font-bold text-emerald-400">{availableCount}</span>
                </div>
                <div className="rounded-xl bg-blue-950/30 p-2.5 border border-blue-500/30">
                  <span className="text-blue-400 block text-[10px] uppercase">Borrowed</span>
                  <span className="text-lg font-bold text-blue-400">{borrowedCount}</span>
                </div>
                <div className="rounded-xl bg-amber-950/30 p-2.5 border border-amber-500/30">
                  <span className="text-amber-400 block text-[10px] uppercase">Maintenance</span>
                  <span className="text-lg font-bold text-amber-400">{maintenanceCount}</span>
                </div>
              </div>
            </div>

            {/* Staff Management Action Buttons */}
            <PermissionGate permissions={["book:update", "book:delete", "book:issue"]}>
              <div className="flex flex-col gap-2">
                {canIssueBook && availableCount > 0 && (
                  <button
                    onClick={() => {
                      setSelectedCopyForIssue(null);
                      setIsIssueModalOpen(true);
                    }}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer"
                  >
                    <span>📤</span> Issue This Book
                  </button>
                )}

                {canUpdateBook && (
                  <button
                    onClick={() => setIsBookModalOpen(true)}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-indigo-500/40 bg-indigo-950/40 px-4 py-2.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/60 transition cursor-pointer"
                  >
                    <span>✏️</span> Edit Book Details
                  </button>
                )}

                {canDeleteBook && (
                  <button
                    onClick={() => {
                      setDeleteBookError(null);
                      setShowDeleteBookDialog(true);
                    }}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-red-500/30 bg-red-950/30 px-4 py-2.5 text-xs font-semibold text-red-300 hover:bg-red-900/50 transition cursor-pointer"
                  >
                    <span>🗑️</span> Delete Book Title
                  </button>
                )}
              </div>
            </PermissionGate>
          </div>
        </div>
      </div>

      {/* Physical Copies Section */}
      <div className="rounded-3xl border border-gray-800 bg-gray-900/50 p-6 sm:p-8 backdrop-blur-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-gray-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🏷️</span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Physical Inventory Copies
              </h2>
            </div>
            <p className="mt-0.5 text-xs text-gray-400">
              Individual barcode units and shelf positions tracked in circulation
            </p>
          </div>

          <PermissionGate permission="book:create">
            <button
              onClick={() => {
                setSelectedCopyForEdit(null);
                setIsCopyModalOpen(true);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
            >
              <span>➕</span> Add Physical Copy
            </button>
          </PermissionGate>
        </div>

        {/* Copies Table */}
        {copies.length === 0 ? (
          <div className="py-12 text-center">
            <div className="text-4xl mb-3">📦</div>
            <h4 className="text-sm font-bold text-white mb-1">No Physical Copies Registered</h4>
            <p className="text-xs text-gray-400 mb-4">
              This book record has no inventory units registered yet.
            </p>
            <PermissionGate permission="book:create">
              <button
                onClick={() => {
                  setSelectedCopyForEdit(null);
                  setIsCopyModalOpen(true);
                }}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
              >
                Register First Copy
              </button>
            </PermissionGate>
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-950/40 text-[11px] uppercase font-semibold text-gray-400">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3">
                    Barcode / Identifier
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Shelf Location
                  </th>
                  <th scope="col" className="px-3 py-3.5 hidden sm:table-cell">
                    Registered On
                  </th>
                  <PermissionGate permissions={["book:update", "book:delete", "book:issue"]}>
                    <th scope="col" className="py-3.5 pl-3 pr-4 text-right">
                      Actions
                    </th>
                  </PermissionGate>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {copies.map((copy) => (
                  <tr key={copy.id} className="hover:bg-gray-800/30 transition">
                    <td className="py-3.5 pl-4 pr-3 font-mono font-semibold text-white">
                      {copy.copy_identifier}
                    </td>
                    <td className="px-3 py-3.5">{getStatusBadge(copy.status)}</td>
                    <td className="px-3 py-3.5 text-gray-300">
                      {copy.shelf_location || "—"}
                    </td>
                    <td className="px-3 py-3.5 text-gray-500 hidden sm:table-cell">
                      {new Date(copy.created_at).toLocaleDateString()}
                    </td>
                    <PermissionGate permissions={["book:update", "book:delete", "book:issue"]}>
                      <td className="py-3.5 pl-3 pr-4 text-right space-x-2">
                        {canIssueBook && copy.status === "AVAILABLE" && (
                          <button
                            onClick={() => {
                              setSelectedCopyForIssue(copy);
                              setIsIssueModalOpen(true);
                            }}
                            className="rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-2.5 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/60 transition cursor-pointer"
                            title="Issue this specific copy"
                          >
                            Issue
                          </button>
                        )}
                        {canUpdateBook && (
                          <button
                            onClick={() => {
                              setSelectedCopyForEdit(copy);
                              setIsCopyModalOpen(true);
                            }}
                            className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition cursor-pointer"
                          >
                            Edit
                          </button>
                        )}
                        {canDeleteBook && (
                          <button
                            onClick={() => {
                              setCopyToDelete(copy);
                              setDeleteCopyError(null);
                            }}
                            className="rounded-lg border border-red-500/30 bg-red-950/30 px-2.5 py-1 text-xs font-medium text-red-300 hover:bg-red-900/50 transition cursor-pointer"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </PermissionGate>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Book Edit Modal */}
      <BookFormModal
        isOpen={isBookModalOpen}
        book={book}
        categories={categories}
        onClose={() => setIsBookModalOpen(false)}
        onSuccess={(updatedBook) => {
          setBook(updatedBook);
          showToast(`Book metadata updated successfully.`);
          refreshBookData();
        }}
      />

      {/* Copy Add/Edit Modal */}
      <CopyFormModal
        isOpen={isCopyModalOpen}
        bookId={book.id}
        bookTitle={book.title}
        copy={selectedCopyForEdit}
        onClose={() => setIsCopyModalOpen(false)}
        onSuccess={(savedCopy, action) => {
          showToast(
            `Copy "${savedCopy.copy_identifier}" was ${action === "created" ? "added" : "updated"} successfully.`
          );
          refreshBookData();
        }}
      />

      {/* Issue Book Modal */}
      <IssueBookModal
        isOpen={isIssueModalOpen}
        book={book}
        copy={selectedCopyForIssue}
        availableCopies={copies.filter((c) => c.status === "AVAILABLE")}
        onClose={() => {
          setIsIssueModalOpen(false);
          setSelectedCopyForIssue(null);
        }}
        onSuccess={(issued) => {
          showToast(`Copy "${issued.copy_identifier || "item"}" issued to ${issued.user_name || "member"} successfully.`);
          refreshBookData();
        }}
      />

      {/* Book Delete Dialog */}
      <ConfirmDialog
        isOpen={showDeleteBookDialog}
        title="Delete Entire Book Title?"
        message="Are you sure you want to delete this book? This will fail if physical copies exist."
        itemName={book.title}
        confirmText="Delete Book"
        isDanger={true}
        isLoading={isDeletingBook}
        error={deleteBookError}
        onConfirm={handleConfirmDeleteBook}
        onCancel={() => {
          setShowDeleteBookDialog(false);
          setDeleteBookError(null);
        }}
      />

      {/* Copy Delete Dialog */}
      <ConfirmDialog
        isOpen={Boolean(copyToDelete)}
        title="Delete Physical Copy?"
        message="Are you sure you want to delete this inventory copy barcode? This will fail if the copy is currently borrowed."
        itemName={copyToDelete?.copy_identifier}
        confirmText="Delete Copy"
        isDanger={true}
        isLoading={isDeletingCopy}
        error={deleteCopyError}
        onConfirm={handleConfirmDeleteCopy}
        onCancel={() => {
          setCopyToDelete(null);
          setDeleteCopyError(null);
        }}
      />
    </div>
  );
}

export default BookDetailsPage;
