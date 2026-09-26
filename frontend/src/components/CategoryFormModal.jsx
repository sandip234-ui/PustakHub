/**
 * CategoryFormModal — Modal for creating and editing Categories.
 */

import { useState } from "react";
import catalogService from "../services/catalog.service";

export function CategoryFormModal({
  isOpen,
  category = null, // null for create, category object for edit
  onClose,
  onSuccess,
}) {
  if (!isOpen) return null;

  return (
    <CategoryFormModalContent
      key={category ? category.id : "new-category"}
      category={category}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}

function CategoryFormModalContent({ category, onClose, onSuccess }) {
  const isEdit = Boolean(category && category.id);

  const [formData, setFormData] = useState(() => ({
    name: category?.name || "",
    description: category?.description || "",
  }));

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const errs = {};
    if (!formData.name.trim()) {
      errs.name = "Category name is required.";
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
      name: formData.name.trim(),
      description: formData.description.trim() || null,
    };

    try {
      let result;
      if (isEdit) {
        result = await catalogService.updateCategory(category.id, payload);
      } else {
        result = await catalogService.createCategory(payload);
      }
      onSuccess(result, isEdit ? "updated" : "created");
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to save category.";
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
        aria-labelledby="category-modal-title"
      >
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">🗂️</span>
            <h3 id="category-modal-title" className="text-lg font-bold text-white">
              {isEdit ? "Edit Category" : "Add New Category"}
            </h3>
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
              Category Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Distributed Systems"
              className="w-full rounded-xl border border-gray-700 bg-gray-800/80 px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
              required
            />
            {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
              Description
            </label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Detailed description of books included in this discipline..."
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
              {isSubmitting ? "Saving..." : isEdit ? "Update Category" : "Create Category"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CategoryFormModal;
