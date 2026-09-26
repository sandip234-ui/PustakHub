/**
 * BookFormModal — Modal form for creating and editing Book records.
 */

import { useState } from "react";
import catalogService from "../services/catalog.service";

export function BookFormModal({
  isOpen,
  book = null, // null for create, book object for edit
  categories = [],
  onClose,
  onSuccess,
}) {
  if (!isOpen) return null;

  return (
    <BookFormModalContent
      key={book ? book.id : "new-book"}
      book={book}
      categories={categories}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}

function BookFormModalContent({ book, categories, onClose, onSuccess }) {
  const isEdit = Boolean(book && book.id);

  const [formData, setFormData] = useState(() => ({
    title: book?.title || "",
    author: book?.author || "",
    isbn: book?.isbn || "",
    category_id: book?.category_id || (categories.length > 0 ? categories[0].id : ""),
    publisher: book?.publisher || "",
    publication_year: book?.publication_year ? String(book.publication_year) : new Date().getFullYear().toString(),
    description: book?.description || "",
  }));

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const errs = {};
    if (!formData.title.trim()) {
      errs.title = "Book title is required.";
    }
    if (!formData.author.trim()) {
      errs.author = "Author name is required.";
    }
    if (formData.publication_year) {
      const year = parseInt(formData.publication_year, 10);
      if (isNaN(year) || year < 1000 || year > 2100) {
        errs.publication_year = "Publication year must be between 1000 and 2100.";
      }
    }
    if (formData.isbn && formData.isbn.trim()) {
      const cleanIsbn = formData.isbn.trim().replace(/[-\s]/g, "");
      if (cleanIsbn.length !== 10 && cleanIsbn.length !== 13) {
        errs.isbn = "ISBN should typically be 10 or 13 digits.";
      }
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError(null);

    const payload = {
      title: formData.title.trim(),
      author: formData.author.trim(),
      isbn: formData.isbn.trim() || null,
      publisher: formData.publisher.trim() || null,
      publication_year: formData.publication_year
        ? parseInt(formData.publication_year, 10)
        : null,
      description: formData.description.trim() || null,
      category_id: formData.category_id || null,
    };

    try {
      let result;
      if (isEdit) {
        result = await catalogService.updateBook(book.id, payload);
      } else {
        result = await catalogService.createBook(payload);
      }
      onSuccess(result, isEdit ? "updated" : "created");
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to save book record.";
      setApiError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-xl rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="book-modal-title"
      >
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">📖</span>
            <h3 id="book-modal-title" className="text-lg font-bold text-white">
              {isEdit ? "Edit Book Metadata" : "Add New Book to Catalog"}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-800 hover:text-white transition"
          >
            ✕
          </button>
        </div>

        {apiError && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-xs text-red-300">
            <strong>Error:</strong> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. Designing Data-Intensive Applications"
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
              required
            />
            {errors.title && <p className="mt-1 text-xs text-red-400">{errors.title}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                Author(s) <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                placeholder="e.g. Martin Kleppmann"
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                required
              />
              {errors.author && <p className="mt-1 text-xs text-red-400">{errors.author}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                Category
              </label>
              <select
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value="">-- No Category --</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                ISBN-10 / ISBN-13
              </label>
              <input
                type="text"
                value={formData.isbn}
                onChange={(e) => setFormData({ ...formData, isbn: e.target.value })}
                placeholder="9780100000010"
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none font-mono text-xs"
              />
              {errors.isbn && <p className="mt-1 text-xs text-red-400">{errors.isbn}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                Publisher
              </label>
              <input
                type="text"
                value={formData.publisher}
                onChange={(e) => setFormData({ ...formData, publisher: e.target.value })}
                placeholder="O'Reilly Media"
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                Pub Year
              </label>
              <input
                type="number"
                value={formData.publication_year}
                onChange={(e) =>
                  setFormData({ ...formData, publication_year: e.target.value })
                }
                placeholder="2024"
                min="1000"
                max="2100"
                className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
              />
              {errors.publication_year && (
                <p className="mt-1 text-xs text-red-400">{errors.publication_year}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Description / Abstract
            </label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Detailed synopsis of the title..."
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
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
              className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? "Saving..." : isEdit ? "Update Book" : "Create Book"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BookFormModal;
