/**
 * BookCard.jsx — Enhanced Academic Library Book Card.
 *
 * Implements the PustakHub V2 book-card visual hierarchy:
 * - Domain-specific Tabler category icon & subtle category badge
 * - Publication year display
 * - Prominent, high-contrast book title with link
 * - Bibliographic author and description lines
 * - Publisher and ISBN metadata divider
 * - Physical copy availability badge
 * - Accessible Lucide action buttons (Edit, Delete, Details)
 *
 * Fully supports Light/Dark mode via theme tokens and responsive layouts.
 */

import { ArrowRight, Edit3, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { getCategoryStyle } from "../utils/categoryIcons";
import CategoryIcon from "./CategoryIcon";

export function BookCard({
  book,
  canUpdate = false,
  canDelete = false,
  onEdit,
  onDelete,
}) {
  if (!book) return null;

  const totalCopies = book.total_copies || 0;
  const availableCopies = book.available_copies || 0;
  const borrowedCopies = totalCopies - availableCopies;
  const hasAvailable = availableCopies > 0;

  const categoryName = book.category_name || "General";
  const categoryStyle = getCategoryStyle(categoryName);

  return (
    <div
      className="group relative flex flex-col justify-between rounded-2xl border p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg text-left"
      style={{
        backgroundColor: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--border-strong)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      <div>
        {/* Top Header Row: Category Icon + Badge + Year */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            {/* Category Icon */}
            <CategoryIcon categoryName={categoryName} size="md" />

            {/* Category Badge */}
            <span
              className="inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold truncate max-w-37.5 sm:max-w-42.5"
              style={{
                backgroundColor: categoryStyle.badgeBg,
                borderColor: categoryStyle.badgeBorder,
                color: categoryStyle.badgeText,
              }}
              title={categoryName}
            >
              {categoryName}
            </span>
          </div>

          {/* Publication Year */}
          {book.publication_year && (
            <span
              className="text-xs font-medium shrink-0 pt-1"
              style={{ color: "var(--text-muted)" }}
            >
              {book.publication_year}
            </span>
          )}
        </div>

        {/* Title */}
        <Link
          to={`/books/${book.id}`}
          className="mt-3.5 block text-base font-bold sm:text-[17px] leading-snug transition line-clamp-2"
          style={{ color: "var(--text-primary)" }}
          title={book.title}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--primary)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
        >
          {book.title}
        </Link>

        {/* Author */}
        {book.author && (
          <p
            className="mt-1.5 text-xs line-clamp-1"
            style={{ color: "var(--text-secondary)" }}
          >
            by{" "}
            <span className="font-medium" style={{ color: "var(--text-primary)" }}>
              {book.author}
            </span>
          </p>
        )}

        {/* Description Preview */}
        {book.description && (
          <p
            className="mt-2.5 text-xs line-clamp-2 leading-relaxed"
            style={{ color: "var(--text-secondary)" }}
          >
            {book.description}
          </p>
        )}

        {/* Publisher & ISBN Metadata Divider */}
        {(book.publisher || book.isbn) && (
          <div
            className="mt-3 pt-2.5 border-t space-y-1 text-[11px]"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-muted)",
            }}
          >
            {book.publisher && (
              <div className="truncate">
                <span style={{ color: "var(--text-muted)" }}>Pub:</span>{" "}
                <span style={{ color: "var(--text-secondary)" }}>{book.publisher}</span>
              </div>
            )}
            {book.isbn && (
              <div className="font-mono text-[10px] truncate">
                <span style={{ color: "var(--text-muted)" }}>ISBN:</span>{" "}
                <span style={{ color: "var(--text-secondary)" }}>{book.isbn}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Inventory Availability & Action Controls */}
      <div
        className="mt-4 pt-3 border-t flex items-center justify-between gap-2"
        style={{ borderColor: "var(--border)" }}
      >
        {/* Inventory Availability Badge */}
        <div className="flex items-center gap-1.5 text-xs">
          {totalCopies === 0 ? (
            <span
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{
                backgroundColor: "var(--bg-elevated)",
                color: "var(--text-muted)",
              }}
            >
              No Copies
            </span>
          ) : hasAvailable ? (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] sm:text-[11px] font-semibold"
              style={{
                backgroundColor: "var(--success-bg)",
                borderColor: "rgba(16,185,129,0.3)",
                color: "var(--success-text)",
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
              <span>
                {availableCopies} {availableCopies === 1 ? "Available" : "Available"}
              </span>
            </span>
          ) : (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] sm:text-[11px] font-semibold"
              style={{
                backgroundColor: "var(--warning-bg)",
                borderColor: "rgba(245,158,11,0.3)",
                color: "var(--warning-text)",
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
              <span>{borrowedCopies} Out</span>
            </span>
          )}
        </div>

        {/* Action Buttons (Lucide icons) */}
        <div className="flex items-center gap-1.5 shrink-0">
          {canUpdate && onEdit && (
            <button
              onClick={(e) => onEdit(book, e)}
              className="rounded-lg border p-1.5 text-xs transition focus-visible:outline-none"
              style={{
                borderColor: "var(--border)",
                backgroundColor: "var(--bg-elevated)",
                color: "var(--text-secondary)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--text-primary)";
                e.currentTarget.style.borderColor = "var(--border-strong)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--text-secondary)";
                e.currentTarget.style.borderColor = "var(--border)";
              }}
              aria-label={`Edit ${book.title}`}
              title="Edit book metadata"
            >
              <Edit3 size={13} />
            </button>
          )}

          {canDelete && onDelete && (
            <button
              onClick={(e) => onDelete(book, e)}
              className="rounded-lg border p-1.5 text-xs transition focus-visible:outline-none"
              style={{
                borderColor: "rgba(244,63,94,0.3)",
                backgroundColor: "var(--danger-bg)",
                color: "var(--danger-text)",
              }}
              aria-label={`Delete ${book.title}`}
              title="Delete book title"
            >
              <Trash2 size={13} />
            </button>
          )}

          <Link
            to={`/books/${book.id}`}
            className="btn btn-secondary btn-sm flex items-center gap-1 shrink-0"
            style={{ padding: "4px 10px", fontSize: "11px" }}
            aria-label={`View details for ${book.title}`}
          >
            <span>Details</span>
            <ArrowRight size={12} />
          </Link>
        </div>
      </div>
    </div>
  );
}

export default BookCard;
