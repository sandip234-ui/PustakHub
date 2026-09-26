/**
 * AuditFilters — Filter controls for the administrative audit ledger.
 */

import { useEffect, useState } from "react";

export function AuditFilters({
  filters,
  onChange,
  onReset,
  availableActions = [],
}) {
  const [localSearch, setLocalSearch] = useState(filters.search || "");

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== (filters.search || "")) {
        onChange({ ...filters, search: localSearch, page: 1 });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch, filters, onChange]);

  const handleFieldChange = (field, value) => {
    onChange({
      ...filters,
      [field]: value || undefined,
      page: 1,
    });
  };

  const handleReset = () => {
    setLocalSearch("");
    onReset();
  };

  const isFiltered =
    Boolean(filters.search) ||
    Boolean(filters.action) ||
    Boolean(filters.status) ||
    Boolean(filters.resource_type) ||
    Boolean(filters.start_time) ||
    Boolean(filters.end_time);

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4 sm:p-5 space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search input */}
        <div className="lg:col-span-2">
          <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
            Search Audit Trails
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm">
              🔍
            </span>
            <input
              type="text"
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              placeholder="Search by actor email, IP address, resource ID..."
              className="w-full rounded-xl border border-gray-800 bg-gray-950/80 pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>
        </div>

        {/* Action Type Dropdown */}
        <div>
          <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
            Action Event
          </label>
          <select
            value={filters.action || ""}
            onChange={(e) => handleFieldChange("action", e.target.value)}
            className="w-full rounded-xl border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition cursor-pointer"
          >
            <option value="">All Action Events</option>
            {availableActions.map((act) => (
              <option key={act.action} value={act.action}>
                {act.action} ({act.category})
              </option>
            ))}
          </select>
        </div>

        {/* Outcome Status Dropdown */}
        <div>
          <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
            Outcome Status
          </label>
          <select
            value={filters.status || ""}
            onChange={(e) => handleFieldChange("status", e.target.value)}
            className="w-full rounded-xl border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition cursor-pointer"
          >
            <option value="">All Outcomes</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILURE">FAILURE</option>
            <option value="PARTIAL">PARTIAL</option>
          </select>
        </div>
      </div>

      {/* Date Ranges & Resource Type Sub-row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-gray-800/80">
        {/* Resource Type */}
        <div>
          <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
            Resource Type
          </label>
          <select
            value={filters.resource_type || ""}
            onChange={(e) => handleFieldChange("resource_type", e.target.value)}
            className="w-full rounded-xl border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition cursor-pointer"
          >
            <option value="">All Resource Types</option>
            <option value="User">User</option>
            <option value="Role">Role</option>
            <option value="Book">Book</option>
            <option value="BookCopy">BookCopy</option>
            <option value="BorrowRecord">BorrowRecord</option>
            <option value="Fine">Fine</option>
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
            From Date (UTC)
          </label>
          <input
            type="datetime-local"
            value={filters.start_time || ""}
            onChange={(e) => handleFieldChange("start_time", e.target.value)}
            className="w-full rounded-xl border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
          />
        </div>

        {/* End Date & Reset Action */}
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <label className="block text-[10px] uppercase font-bold text-gray-400 mb-1">
              To Date (UTC)
            </label>
            <input
              type="datetime-local"
              value={filters.end_time || ""}
              onChange={(e) => handleFieldChange("end_time", e.target.value)}
              className="w-full rounded-xl border border-gray-800 bg-gray-950/80 px-3 py-2 text-xs text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          {isFiltered && (
            <button
              onClick={handleReset}
              className="rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-semibold text-gray-300 hover:bg-gray-700 hover:text-white transition cursor-pointer whitespace-nowrap"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default AuditFilters;
