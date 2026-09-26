/**
 * CategoriesPage — Category Taxonomy Management for ADMIN and LIBRARIAN staff.
 *
 * Allows viewing, creating, updating, and deleting book categories.
 */

import { useCallback, useEffect, useState } from "react";
import CategoryFormModal from "../components/CategoryFormModal";
import ConfirmDialog from "../components/ConfirmDialog";
import PermissionGate from "../components/PermissionGate";
import Toast from "../components/Toast";
import usePermissions from "../hooks/usePermissions";
import catalogService from "../services/catalog.service";

export function CategoriesPage() {
  const { canUpdateBook, canDeleteBook } = usePermissions();

  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Modals
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [selectedCategoryForEdit, setSelectedCategoryForEdit] = useState(null);

  const [categoryToDelete, setCategoryToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadCategories = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = { page_size: 100 };
      if (search.trim()) params.search = search.trim();

      const data = await catalogService.getCategories(params);
      setCategories(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to load categories.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const handler = setTimeout(() => {
      loadCategories();
    }, 200);
    return () => clearTimeout(handler);
  }, [loadCategories]);

  const handleAddCategory = () => {
    setSelectedCategoryForEdit(null);
    setIsCategoryModalOpen(true);
  };

  const handleEditCategory = (cat) => {
    setSelectedCategoryForEdit(cat);
    setIsCategoryModalOpen(true);
  };

  const handleDeletePrompt = (cat) => {
    setCategoryToDelete(cat);
    setDeleteError(null);
  };

  const handleConfirmDelete = async () => {
    if (!categoryToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await catalogService.deleteCategory(categoryToDelete.id);
      showToast(`Category "${categoryToDelete.name}" deleted successfully.`);
      setCategoryToDelete(null);
      loadCategories();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to delete category.";
      setDeleteError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 text-left">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🗂️</span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Category Taxonomy
            </h1>
          </div>
          <p className="mt-1 text-sm text-gray-400">
            Manage academic genres, disciplines, and book taxonomy groupings
          </p>
        </div>

        <PermissionGate permission="book:create">
          <button
            onClick={handleAddCategory}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition cursor-pointer"
          >
            <span>➕</span> Add New Category
          </button>
        </PermissionGate>
      </div>

      {/* Search Bar */}
      <div className="mt-6 flex items-center justify-between gap-4 rounded-2xl border border-gray-800 bg-gray-900/60 p-4 backdrop-blur-xl">
        <div className="relative w-full sm:w-80">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 pointer-events-none text-xs">
            🔍
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter categories by name..."
            className="w-full rounded-xl border border-gray-700 bg-gray-800/90 pl-8 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <span className="text-xs text-gray-400">
          Total Categories: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-950/30 p-4 text-sm text-red-300">
          ❌ {error}
        </div>
      )}

      {/* Table of Categories */}
      <div className="mt-6 rounded-2xl border border-gray-800 bg-gray-900/50 backdrop-blur-xl overflow-hidden">
        {isLoading ? (
          <div className="py-12 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mx-auto"></div>
            <p className="mt-3 text-xs text-gray-400">Loading taxonomy categories...</p>
          </div>
        ) : categories.length === 0 ? (
          <div className="py-12 text-center">
            <div className="text-4xl mb-3">🗂️</div>
            <h4 className="text-sm font-bold text-white mb-1">No Categories Found</h4>
            <p className="text-xs text-gray-400 mb-4">
              {search ? "No categories match your search." : "No categories created yet."}
            </p>
            <PermissionGate permission="book:create">
              <button
                onClick={handleAddCategory}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-indigo-500 transition cursor-pointer"
              >
                Create Category
              </button>
            </PermissionGate>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="border-b border-gray-800 bg-gray-950/60 text-[11px] uppercase font-semibold text-gray-400">
                <tr>
                  <th scope="col" className="py-3.5 pl-6 pr-3">
                    Category Name
                  </th>
                  <th scope="col" className="px-3 py-3.5">
                    Description
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center">
                    Books Categorized
                  </th>
                  <th scope="col" className="px-3 py-3.5 hidden sm:table-cell">
                    Created
                  </th>
                  <PermissionGate permissions={["book:update", "book:delete"]}>
                    <th scope="col" className="py-3.5 pl-3 pr-6 text-right">
                      Actions
                    </th>
                  </PermissionGate>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {categories.map((cat) => (
                  <tr key={cat.id} className="hover:bg-gray-800/30 transition">
                    <td className="py-3.5 pl-6 pr-3 font-semibold text-white">
                      {cat.name}
                    </td>
                    <td className="px-3 py-3.5 text-gray-400 max-w-xs truncate">
                      {cat.description || "—"}
                    </td>
                    <td className="px-3 py-3.5 text-center">
                      <span className="inline-flex items-center rounded-full bg-indigo-950/70 border border-indigo-500/30 px-2.5 py-0.5 text-xs font-semibold text-indigo-300">
                        {cat.book_count || 0} books
                      </span>
                    </td>
                    <td className="px-3 py-3.5 text-gray-500 hidden sm:table-cell">
                      {new Date(cat.created_at).toLocaleDateString()}
                    </td>
                    <PermissionGate permissions={["book:update", "book:delete"]}>
                      <td className="py-3.5 pl-3 pr-6 text-right space-x-2">
                        {canUpdateBook && (
                          <button
                            onClick={() => handleEditCategory(cat)}
                            className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition cursor-pointer"
                          >
                            Edit
                          </button>
                        )}
                        {canDeleteBook && (
                          <button
                            onClick={() => handleDeletePrompt(cat)}
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

      {/* Category Create/Edit Modal */}
      <CategoryFormModal
        isOpen={isCategoryModalOpen}
        category={selectedCategoryForEdit}
        onClose={() => setIsCategoryModalOpen(false)}
        onSuccess={(savedCat, action) => {
          showToast(
            `Category "${savedCat.name}" was ${action === "created" ? "created" : "updated"} successfully.`
          );
          loadCategories();
        }}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(categoryToDelete)}
        title="Delete Category?"
        message="Are you sure you want to remove this category? Deletion will fail if books are currently assigned to this category."
        itemName={categoryToDelete?.name}
        confirmText="Delete Category"
        isDanger={true}
        isLoading={isDeleting}
        error={deleteError}
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setCategoryToDelete(null);
          setDeleteError(null);
        }}
      />
    </div>
  );
}

export default CategoriesPage;
