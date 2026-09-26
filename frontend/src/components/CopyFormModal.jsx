/**
 * CopyFormModal — Modal for adding and editing physical BookCopy items.
 */

import { useState } from "react";
import catalogService from "../services/catalog.service";

const COPY_STATUSES = [
  { value: "AVAILABLE", label: "Available", color: "text-emerald-400" },
  { value: "BORROWED", label: "Borrowed", color: "text-blue-400" },
  { value: "MAINTENANCE", label: "Maintenance", color: "text-amber-400" },
  { value: "LOST", label: "Lost", color: "text-red-400" },
];

export function CopyFormModal({
  isOpen,
  bookId,
  bookTitle = "",
  copy = null, // null for create, copy object for edit
  onClose,
  onSuccess,
}) {
  if (!isOpen) return null;

  return (
    <CopyFormModalContent
      key={copy ? copy.id : "new-copy"}
      bookId={bookId}
      bookTitle={bookTitle}
      copy={copy}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}

function CopyFormModalContent({
  bookId,
  bookTitle,
  copy,
  onClose,
  onSuccess,
}) {
  const isEdit = Boolean(copy && copy.id);

  const [formData, setFormData] = useState(() => ({
    copy_identifier: copy?.copy_identifier || "",
    shelf_location: copy?.shelf_location || (isEdit ? "" : "Floor 1 - Section A"),
    status: copy?.status || "AVAILABLE",
  }));

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const errs = {};
    if (!formData.copy_identifier.trim()) {
      errs.copy_identifier = "Copy barcode / identifier is required.";
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
      copy_identifier: formData.copy_identifier.trim(),
      shelf_location: formData.shelf_location.trim() || null,
      status: formData.status,
    };

    try {
      let result;
      if (isEdit) {
        result = await catalogService.updateCopy(copy.id, payload);
      } else {
        result = await catalogService.createBookCopy(bookId, payload);
      }
      onSuccess(result, isEdit ? "updated" : "created");
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to save physical copy.";
      setApiError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl text-left"
        role="dialog"
        aria-modal="true"
        aria-labelledby="copy-modal-title"
      >
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">🏷️</span>
            <div>
              <h3 id="copy-modal-title" className="text-lg font-bold text-white">
                {isEdit ? "Edit Physical Copy" : "Add Physical Copy"}
              </h3>
              {bookTitle && (
                <p className="text-xs text-indigo-400 truncate max-w-xs">{bookTitle}</p>
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

        {apiError && (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-950/40 p-3 text-xs text-red-300">
            <strong>Error:</strong> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Barcode / Copy Identifier <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={formData.copy_identifier}
              onChange={(e) =>
                setFormData({ ...formData, copy_identifier: e.target.value })
              }
              placeholder="e.g. BC-9780100000010-1"
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none font-mono"
              required
            />
            {errors.copy_identifier && (
              <p className="mt-1 text-xs text-red-400">{errors.copy_identifier}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Shelf Location
            </label>
            <input
              type="text"
              value={formData.shelf_location}
              onChange={(e) =>
                setFormData({ ...formData, shelf_location: e.target.value })
              }
              placeholder="e.g. Floor 2 - Section C - Shelf 4"
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Availability Status
            </label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none cursor-pointer"
            >
              {COPY_STATUSES.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
            {isEdit && copy?.status === "BORROWED" && formData.status !== "BORROWED" && (
              <p className="mt-1.5 text-xs text-amber-400/90">
                ⚠️ Note: Changing a currently borrowed copy&apos;s status manually does not process its circulation return transaction.
              </p>
            )}
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
              {isSubmitting ? "Saving..." : isEdit ? "Update Copy" : "Add Copy"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CopyFormModal;
