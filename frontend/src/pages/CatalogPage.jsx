/**
 * CatalogPage — Main Library Catalog Explorer.
 *
 * Provides server-side search, category filtering, pagination,
 * book details links, and staff CRUD workflows.
 * Fully theme-aware using CSS tokens and Lucide icons.
 */

import {
  AlertTriangle,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Plus,
  RotateCcw,
  Search,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import BookCard from "../components/BookCard";
import BookFormModal from "../components/BookFormModal";
import ConfirmDialog from "../components/ConfirmDialog";
import PermissionGate from "../components/PermissionGate";
import Toast from "../components/Toast";
import usePermissions from "../hooks/usePermissions";
import useRealtime from "../hooks/useRealtime";
import catalogService from "../services/catalog.service";
import { RealtimeEventType } from "../services/realtime.service";

export function CatalogPage() {
  const { canUpdateBook, canDeleteBook } = usePermissions();

  // State
  const [books, setBooks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedYear, setSelectedYear] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Modals state
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [selectedBookForEdit, setSelectedBookForEdit] = useState(null);

  const [bookToDelete, setBookToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  // Load Categories on mount
  useEffect(() => {
    async function loadCategories() {
      try {
        const data = await catalogService.getCategories({ page_size: 100 });
        setCategories(data.items || []);
      } catch (err) {
        console.error("Failed to load categories", err);
      }
    }
    loadCategories();
  }, []);

  // Fetch books from server
  const fetchBooks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (selectedCategory) params.category_id = selectedCategory;
      if (selectedYear) params.publication_year = parseInt(selectedYear, 10);

      const data = await catalogService.getBooks(params);
      setBooks(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.pages || 1);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to load catalog books.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, searchQuery, selectedCategory, selectedYear]);

  const { subscribeMany } = useRealtime();

  // Trigger search with debounce & listen to real-time events
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchBooks();
    }, 250);

    const unsubscribe = subscribeMany(
      [
        RealtimeEventType.BOOK_CREATED,
        RealtimeEventType.BOOK_UPDATED,
        RealtimeEventType.BOOK_DELETED,
        RealtimeEventType.COPY_CREATED,
        RealtimeEventType.COPY_UPDATED,
        RealtimeEventType.COPY_DELETED,
        RealtimeEventType.SYSTEM_RECONNECTED,
      ],
      () => {
        fetchBooks();
      }
    );

    return () => {
      clearTimeout(handler);
      unsubscribe();
    };
  }, [fetchBooks, subscribeMany]);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleCreateBook = () => {
    setSelectedBookForEdit(null);
    setIsBookModalOpen(true);
  };

  const handleEditBook = (book, e) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedBookForEdit(book);
    setIsBookModalOpen(true);
  };

  const handleDeletePrompt = (book, e) => {
    e.preventDefault();
    e.stopPropagation();
    setBookToDelete(book);
    setDeleteError(null);
  };

  const handleConfirmDelete = async () => {
    if (!bookToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await catalogService.deleteBook(bookToDelete.id);
      showToast(`Book "${bookToDelete.title}" deleted successfully.`);
      setBookToDelete(null);
      fetchBooks();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to delete book.";
      setDeleteError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleBookSaved = (savedBook, action) => {
    showToast(
      `Book "${savedBook.title}" was ${action === "created" ? "added" : "updated"} successfully.`
    );
    fetchBooks();
  };

  const resetFilters = () => {
    setSearchQuery("");
    setSelectedCategory("");
    setSelectedYear("");
    setPage(1);
  };

  return (
    <div
      className="min-h-[calc(100vh-56px)] py-8"
      style={{ backgroundColor: "var(--bg)" }}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Header Banner */}
        <div
          className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <div>
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-xl border"
                style={{
                  backgroundColor: "var(--primary-soft)",
                  borderColor: "rgba(99,102,241,0.25)",
                }}
              >
                <BookOpen size={18} style={{ color: "var(--primary)" }} />
              </div>
              <h1
                className="text-2xl sm:text-3xl font-black tracking-tight"
                style={{ color: "var(--text-primary)" }}
              >
                Library Catalog
              </h1>
            </div>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Explore academic textbooks, technical monographs, and digital library holdings
            </p>
          </div>

          <PermissionGate permission="book:create">
            <button
              onClick={handleCreateBook}
              className="btn btn-primary"
            >
              <Plus size={15} />
              Add New Book
            </button>
          </PermissionGate>
        </div>

        {/* Search and Filters Bar */}
        <div
          className="mt-6 rounded-2xl border p-4 shadow-sm"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3 items-center">
            {/* Search Box */}
            <div className="lg:col-span-6 relative">
              <span
                className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none"
                style={{ color: "var(--text-muted)" }}
              >
                <Search size={16} />
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                placeholder="Search by title, author, ISBN, or publisher..."
                className="input"
                style={{ paddingLeft: "2.75rem", paddingRight: "2.75rem" }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute inset-y-0 right-0 flex items-center pr-3.5 transition"
                  style={{ color: "var(--text-muted)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                  aria-label="Clear search"
                >
                  <X size={15} />
                </button>
              )}
            </div>

            {/* Category Dropdown */}
            <div className="lg:col-span-3">
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setPage(1);
                }}
                className="input cursor-pointer"
              >
                <option value="">All Categories ({categories.length})</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name} {cat.book_count > 0 ? `(${cat.book_count})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {/* Page Size & Reset Filter */}
            <div className="lg:col-span-3 flex items-center gap-2">
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="input cursor-pointer"
                title="Items per page"
              >
                <option value={12}>12 / page</option>
                <option value={20}>20 / page</option>
                <option value={50}>50 / page</option>
                <option value={100}>100 / page</option>
              </select>

              {(searchQuery || selectedCategory || selectedYear) && (
                <button
                  onClick={resetFilters}
                  className="btn btn-secondary btn-sm flex items-center gap-1.5 shrink-0"
                >
                  <RotateCcw size={12} />
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Results count stats */}
          <div
            className="mt-3 flex items-center justify-between text-xs pt-3 border-t"
            style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
          >
            <span>
              Showing{" "}
              <strong style={{ color: "var(--text-primary)" }}>{books.length}</strong> of{" "}
              <strong style={{ color: "var(--text-primary)" }}>{total}</strong> total titles
            </span>
            {total > 0 && (
              <span>
                Page <strong style={{ color: "var(--text-primary)" }}>{page}</strong> of{" "}
                <strong style={{ color: "var(--text-primary)" }}>{totalPages}</strong>
              </span>
            )}
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div
            className="mt-6 rounded-2xl border p-4 text-sm flex items-start gap-2.5"
            style={{
              borderColor: "rgba(244,63,94,0.3)",
              backgroundColor: "var(--danger-bg)",
              color: "var(--danger-text)",
            }}
            role="alert"
          >
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Skeletons */}
        {isLoading && (
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="flex flex-col justify-between rounded-2xl border p-5 animate-pulse min-h-72.5"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
              >
                <div>
                  {/* Icon & Badge Header Placeholder */}
                  <div className="flex items-center justify-between gap-3 mb-3.5">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="h-11 w-11 rounded-xl shrink-0"
                        style={{ backgroundColor: "var(--bg-elevated)" }}
                      />
                      <div
                        className="h-5 w-24 rounded-md"
                        style={{ backgroundColor: "var(--bg-elevated)" }}
                      />
                    </div>
                    <div
                      className="h-4 w-10 rounded"
                      style={{ backgroundColor: "var(--bg-elevated)" }}
                    />
                  </div>

                  {/* Title & Author Placeholder */}
                  <div
                    className="h-5 rounded-md w-4/5 mb-2"
                    style={{ backgroundColor: "var(--bg-elevated)" }}
                  />
                  <div
                    className="h-3.5 rounded w-1/2 mb-3"
                    style={{ backgroundColor: "var(--bg-elevated)" }}
                  />

                  {/* Description Placeholder */}
                  <div
                    className="h-9 rounded-md w-full mb-3"
                    style={{ backgroundColor: "var(--bg-elevated)" }}
                  />

                  {/* Metadata Divider */}
                  <div
                    className="pt-2.5 border-t space-y-1.5"
                    style={{ borderColor: "var(--border)" }}
                  >
                    <div
                      className="h-3 rounded w-2/3"
                      style={{ backgroundColor: "var(--bg-elevated)" }}
                    />
                    <div
                      className="h-3 rounded w-1/2"
                      style={{ backgroundColor: "var(--bg-elevated)" }}
                    />
                  </div>
                </div>

                {/* Bottom Action Row Placeholder */}
                <div
                  className="mt-4 pt-3 border-t flex items-center justify-between gap-2"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div
                    className="h-6 w-20 rounded-full"
                    style={{ backgroundColor: "var(--bg-elevated)" }}
                  />
                  <div
                    className="h-7 w-24 rounded-lg"
                    style={{ backgroundColor: "var(--bg-elevated)" }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && books.length === 0 && (
          <div
            className="mt-12 rounded-3xl border p-12 text-center max-w-lg mx-auto"
            style={{
              backgroundColor: "var(--bg-surface)",
              borderColor: "var(--border)",
            }}
          >
            <div
              className="flex h-14 w-14 items-center justify-center rounded-2xl border mx-auto mb-4"
              style={{
                backgroundColor: "var(--bg-elevated)",
                borderColor: "var(--border)",
              }}
            >
              <BookOpen size={24} style={{ color: "var(--text-muted)" }} />
            </div>
            <h3
              className="text-lg font-bold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              No Books Found
            </h3>
            <p
              className="text-sm mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              We couldn&apos;t find any books matching your search query or selected filter criteria.
            </p>
            <button
              onClick={resetFilters}
              className="btn btn-primary btn-sm mx-auto"
            >
              <RotateCcw size={13} />
              Reset All Filters
            </button>
          </div>
        )}

        {/* Books Grid */}
        {!isLoading && books.length > 0 && (
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                canUpdate={canUpdateBook}
                canDelete={canDeleteBook}
                onEdit={handleEditBook}
                onDelete={handleDeletePrompt}
              />
            ))}
          </div>
        )}

        {/* Pagination Controls */}
        {!isLoading && totalPages > 1 && (
          <div
            className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 border-t pt-6"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>
              Page <strong style={{ color: "var(--text-primary)" }}>{page}</strong> of{" "}
              <strong style={{ color: "var(--text-primary)" }}>{totalPages}</strong> ({total} books)
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn btn-secondary btn-sm flex items-center gap-1"
              >
                <ChevronLeft size={14} />
                Previous
              </button>

              {/* Smart page numbers */}
              <div className="hidden sm:flex items-center gap-1">
                {[...Array(totalPages)].map((_, i) => {
                  const pageNum = i + 1;
                  if (
                    pageNum === 1 ||
                    pageNum === totalPages ||
                    (pageNum >= page - 2 && pageNum <= page + 2)
                  ) {
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`h-8 w-8 rounded-xl text-xs font-semibold transition ${
                          page === pageNum
                            ? "bg-indigo-600 text-white shadow"
                            : "border text-(--text-secondary) hover:bg-(--bg-elevated) hover:text-(--text-primary)"
                        }`}
                        style={
                          page !== pageNum
                            ? {
                                borderColor: "var(--border)",
                                backgroundColor: "var(--bg-surface)",
                              }
                            : {}
                        }
                      >
                        {pageNum}
                      </button>
                    );
                  }
                  if (pageNum === page - 3 || pageNum === page + 3) {
                    return (
                      <span
                        key={pageNum}
                        className="text-xs px-1"
                        style={{ color: "var(--text-muted)" }}
                      >
                        ...
                      </span>
                    );
                  }
                  return null;
                })}
              </div>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="btn btn-secondary btn-sm flex items-center gap-1"
              >
                Next
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Book Create/Edit Modal */}
        <BookFormModal
          isOpen={isBookModalOpen}
          book={selectedBookForEdit}
          categories={categories}
          onClose={() => setIsBookModalOpen(false)}
          onSuccess={handleBookSaved}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={Boolean(bookToDelete)}
          title="Delete Book Title?"
          message="Are you sure you want to remove this book from the catalog? This action will fail if physical copies currently exist for this title."
          itemName={bookToDelete?.title}
          confirmText="Delete Book"
          isDanger={true}
          isLoading={isDeleting}
          error={deleteError}
          onConfirm={handleConfirmDelete}
          onCancel={() => {
            setBookToDelete(null);
            setDeleteError(null);
          }}
        />
      </div>
    </div>
  );
}

export default CatalogPage;
