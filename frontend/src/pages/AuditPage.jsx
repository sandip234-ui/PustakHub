/**
 * AuditPage — Security & Operational Audit Log Console.
 *
 * Implements Phase 16:
 *   - Dedicated READ-ONLY audit trail explorer
 *   - Server-side multi-parameter filtering & search
 *   - Forensic event detail inspection modal
 *   - Server-side pagination and responsive table/cards
 */

import { useCallback, useEffect, useState } from "react";
import AuditDetailModal from "../components/AuditDetailModal";
import AuditEventBadge from "../components/AuditEventBadge";
import AuditFilters from "../components/AuditFilters";
import AuditStatusBadge from "../components/AuditStatusBadge";
import Toast from "../components/Toast";
import useRealtime from "../hooks/useRealtime";
import { RealtimeEventType } from "../services/realtime.service";
import auditService from "../services/audit.service";

export function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Available metadata for dropdowns
  const [availableActions, setAvailableActions] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);

  // Active filters
  const [filters, setFilters] = useState({
    search: "",
    action: "",
    status: "",
    resource_type: "",
    start_time: "",
    end_time: "",
  });

  // Selected event for detail inspection modal
  const [selectedLog, setSelectedLog] = useState(null);
  const [newEventsCount, setNewEventsCount] = useState(0);

  const { subscribe } = useRealtime();

  // Subscribe to realtime audit events
  useEffect(() => {
    const unsubscribe = subscribe(RealtimeEventType.AUDIT_EVENT_CREATED, () => {
      setNewEventsCount((prev) => prev + 1);
    });
    return () => unsubscribe();
  }, [subscribe]);

  // Fetch available action metadata
  useEffect(() => {
    async function loadActionMetadata() {
      try {
        const data = await auditService.getAuditActions();
        setAvailableActions(data.actions || []);
        setAvailableCategories(data.categories || []);
      } catch {
        // Non-blocking fallback
      }
    }
    loadActionMetadata();
  }, []);

  // Fetch audit logs from server
  const fetchAuditLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
      };

      if (filters.search) params.search = filters.search.trim();
      if (filters.action) params.action = filters.action;
      if (filters.status) params.status = filters.status;
      if (filters.resource_type) params.resource_type = filters.resource_type;
      if (filters.start_time) params.start_time = new Date(filters.start_time).toISOString();
      if (filters.end_time) params.end_time = new Date(filters.end_time).toISOString();

      const res = await auditService.getAuditLogs(params);
      setLogs(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      const msg =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        "Failed to load system audit trails.";
      setError(msg);
      setToast({ type: "error", message: msg });
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, filters]);

  const handleViewLatest = () => {
    setNewEventsCount(0);
    setPage(1);
    fetchAuditLogs();
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchAuditLogs();
    }, 10);
    return () => clearTimeout(timer);
  }, [fetchAuditLogs]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilters({
      search: "",
      action: "",
      status: "",
      resource_type: "",
      start_time: "",
      end_time: "",
    });
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-left space-y-6 animate-fadeIn">
      {/* Toast Feedback */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-3xl border border-gray-800 bg-gray-900/60 p-6 sm:p-8 backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-indigo-950/80 border border-indigo-500/40 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-indigo-300">
              Security Console
            </span>
            <span className="inline-flex items-center rounded-full bg-emerald-950/70 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">
              ● Immutable Ledger
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Security & Operational Audit Trails
          </h1>
          <p className="text-sm text-gray-400">
            Immutable forensic activity logs, authentication records, IAM mutations, and circulation history.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAuditLogs}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800 px-4 py-2.5 text-xs font-semibold text-gray-200 hover:bg-gray-700 transition cursor-pointer disabled:opacity-50"
          >
            <span>🔄</span> Refresh
          </button>
        </div>
      </div>

      {/* Real-time New Activity Banner */}
      {newEventsCount > 0 && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl border border-indigo-500/40 bg-indigo-950/60 p-4 shadow-lg shadow-indigo-950/30 animate-fadeIn">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/30 text-indigo-300 font-bold text-base shadow-sm">
              ⚡
            </span>
            <div>
              <p className="text-sm font-semibold text-white">
                {newEventsCount} new audit {newEventsCount === 1 ? "event" : "events"} recorded in real-time
              </p>
              <p className="text-xs text-indigo-300">
                New activity occurred on the server. Your current investigation table view was preserved.
              </p>
            </div>
          </div>
          <button
            onClick={handleViewLatest}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition cursor-pointer shadow whitespace-nowrap"
          >
            View Latest ({newEventsCount})
          </button>
        </div>
      )}

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4">
          <div className="text-[10px] uppercase font-bold text-gray-400">Matching Audit Records</div>
          <div className="text-2xl font-bold text-white mt-1">
            {isLoading ? "..." : total.toLocaleString()}
          </div>
          <div className="text-[11px] text-gray-500 mt-0.5">Events matching active filters</div>
        </div>

        <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4">
          <div className="text-[10px] uppercase font-bold text-gray-400">Active Page</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1 font-mono">
            {page} / {totalPages}
          </div>
          <div className="text-[11px] text-gray-500 mt-0.5">
            Displaying {logs.length} entries per page
          </div>
        </div>

        <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4">
          <div className="text-[10px] uppercase font-bold text-gray-400">Ledger Immutability</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 flex items-center gap-2">
            <span>🛡️</span> Append-Only
          </div>
          <div className="text-[11px] text-gray-500 mt-0.5">
            Strict read-only forensic guarantee
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <AuditFilters
        filters={filters}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
        availableActions={availableActions}
        availableCategories={availableCategories}
      />

      {/* Audit Logs Table / Mobile List */}
      <div className="rounded-3xl border border-gray-800 bg-gray-900/50 backdrop-blur-xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 w-full bg-gray-800/40 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="p-12 text-center space-y-3">
            <span className="text-3xl">⚠️</span>
            <p className="text-sm font-semibold text-red-400">{error}</p>
            <button
              onClick={fetchAuditLogs}
              className="rounded-xl bg-gray-800 px-4 py-2 text-xs font-semibold text-gray-200 hover:bg-gray-700 transition"
            >
              Retry
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <span className="text-3xl">🔍</span>
            <p className="text-sm font-semibold text-gray-300">No Audit Events Found</p>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              No audit log records match the current filter criteria or search query.
            </p>
            <button
              onClick={handleResetFilters}
              className="mt-2 rounded-xl bg-indigo-600/30 border border-indigo-500/40 px-3.5 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600/50 transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <>
            {/* Desktop / Tablet Table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-800 bg-gray-950/60 text-[10px] uppercase tracking-wider text-gray-400">
                    <th className="px-6 py-3.5">Timestamp</th>
                    <th className="px-6 py-3.5">Action Event</th>
                    <th className="px-6 py-3.5">Actor</th>
                    <th className="px-6 py-3.5">Target Resource</th>
                    <th className="px-6 py-3.5">Outcome</th>
                    <th className="px-6 py-3.5">Client IP</th>
                    <th className="px-6 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {logs.map((log) => (
                    <tr
                      key={log.id}
                      onClick={() => setSelectedLog(log)}
                      className="hover:bg-gray-800/40 transition cursor-pointer group"
                    >
                      <td className="px-6 py-3.5 whitespace-nowrap text-gray-400 font-mono text-[11px]">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>

                      <td className="px-6 py-3.5 whitespace-nowrap">
                        <AuditEventBadge action={log.action} />
                      </td>

                      <td className="px-6 py-3.5 text-gray-200">
                        {log.user_id ? (
                          <div className="truncate max-w-[160px]">
                            <div className="font-semibold text-white truncate">
                              {log.user_name || "User"}
                            </div>
                            <div className="text-[10px] text-gray-400 font-mono truncate">
                              {log.user_email || log.user_id}
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-500 italic text-[11px]">Anonymous</span>
                        )}
                      </td>

                      <td className="px-6 py-3.5 text-gray-300">
                        {log.resource_type ? (
                          <div className="truncate max-w-[180px]">
                            <span className="font-semibold text-indigo-300 text-[11px]">
                              {log.resource_type}
                            </span>
                            {log.resource_id && (
                              <span className="text-gray-400 font-mono text-[10px] block truncate">
                                {log.resource_id}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>

                      <td className="px-6 py-3.5 whitespace-nowrap">
                        <AuditStatusBadge status={log.status} />
                      </td>

                      <td className="px-6 py-3.5 whitespace-nowrap text-gray-400 font-mono text-[11px]">
                        {log.ip_address || "—"}
                      </td>

                      <td className="px-6 py-3.5 whitespace-nowrap text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedLog(log);
                          }}
                          className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1 text-[11px] font-semibold text-gray-300 group-hover:border-indigo-500/50 group-hover:text-white transition"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card List */}
            <div className="md:hidden divide-y divide-gray-800/60">
              {logs.map((log) => (
                <div
                  key={log.id}
                  onClick={() => setSelectedLog(log)}
                  className="p-4 space-y-2 hover:bg-gray-800/30 transition cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <AuditEventBadge action={log.action} />
                    <AuditStatusBadge status={log.status} />
                  </div>

                  <div className="text-xs">
                    <div className="text-white font-semibold">
                      {log.user_name || log.user_email || "Anonymous Event"}
                    </div>
                    {log.resource_type && (
                      <div className="text-gray-400 text-[11px] truncate">
                        Resource: {log.resource_type} {log.resource_id ? `(${log.resource_id})` : ""}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono pt-1">
                    <span>{new Date(log.timestamp).toLocaleString()}</span>
                    <span>{log.ip_address || "No IP"}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 border-t border-gray-800 bg-gray-950/40 text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span>Page Size:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="rounded-lg border border-gray-800 bg-gray-900 px-2 py-1 text-xs text-white"
                >
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <span className="hidden sm:inline">
                  Showing {logs.length} of {total.toLocaleString()} records
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || isLoading}
                  className="rounded-lg border border-gray-800 bg-gray-900 px-3 py-1.5 font-semibold text-gray-300 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
                >
                  ← Previous
                </button>

                <span className="font-mono text-gray-300 px-2">
                  {page} / {totalPages}
                </span>

                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || isLoading}
                  className="rounded-lg border border-gray-800 bg-gray-900 px-3 py-1.5 font-semibold text-gray-300 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Event Detail Inspection Modal */}
      {selectedLog && (
        <AuditDetailModal
          isOpen={Boolean(selectedLog)}
          onClose={() => setSelectedLog(null)}
          log={selectedLog}
        />
      )}
    </div>
  );
}

export default AuditPage;
