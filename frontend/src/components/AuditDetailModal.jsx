/**
 * AuditDetailModal — Accessible modal displaying complete forensic audit event details.
 */

import { useState } from "react";
import AuditEventBadge from "./AuditEventBadge";
import AuditStatusBadge from "./AuditStatusBadge";

export function AuditDetailModal({ isOpen, onClose, log }) {
  const [copiedField, setCopiedField] = useState(null);

  if (!isOpen || !log) return null;

  const handleCopy = (text, fieldName) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => {
      setCopiedField(null);
    }, 2000);
  };

  const formattedDateLocal = new Date(log.timestamp).toLocaleString();
  const formattedDateUtc = new Date(log.timestamp).toUTCString();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="audit-detail-title"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl rounded-3xl border border-gray-800 bg-gray-950 p-6 sm:p-8 text-left shadow-2xl space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-gray-800/80">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xl">🛡️</span>
              <h2 id="audit-detail-title" className="text-lg font-bold text-white tracking-tight">
                Audit Event Record
              </h2>
              <AuditStatusBadge status={log.status} />
            </div>
            <p className="text-xs text-gray-400">
              Immutable forensic log entry recorded in PostgreSQL
            </p>
          </div>

          <button
            onClick={onClose}
            className="rounded-xl border border-gray-800 bg-gray-900 p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition cursor-pointer"
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Primary Event Overview */}
        <div className="rounded-2xl border border-gray-800/80 bg-gray-900/40 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-gray-400">Action Type</span>
            <AuditEventBadge action={log.action} />
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-[10px] uppercase font-bold text-gray-400">Event UUID</span>
            <div className="flex items-center gap-2">
              <span className="font-mono text-gray-300 text-[11px] select-all">{log.id}</span>
              <button
                onClick={() => handleCopy(log.id, "id")}
                className="text-[10px] rounded px-1.5 py-0.5 bg-gray-800 text-gray-300 hover:bg-gray-700"
                title="Copy Event ID"
              >
                {copiedField === "id" ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-[10px] uppercase font-bold text-gray-400">Timestamp</span>
            <div className="text-right">
              <div className="text-gray-200 font-medium">{formattedDateLocal}</div>
              <div className="text-[10px] text-gray-500 font-mono">{formattedDateUtc}</div>
            </div>
          </div>
        </div>

        {/* Actor & Resource Context */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Actor */}
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4 space-y-2">
            <div className="text-[10px] uppercase font-bold text-gray-400 flex items-center gap-1.5">
              <span>👤</span> Actor Identity
            </div>
            {log.user_id ? (
              <div className="space-y-1 text-xs">
                <div className="font-semibold text-white">
                  {log.user_name || "Authenticated User"}
                </div>
                {log.user_email && (
                  <div className="text-gray-300 font-mono text-[11px] truncate">{log.user_email}</div>
                )}
                <div className="text-[10px] text-gray-500 font-mono truncate">
                  UUID: {log.user_id}
                </div>
              </div>
            ) : (
              <div className="text-xs text-amber-400/90 font-medium">
                Anonymous / Pre-Authentication
              </div>
            )}
          </div>

          {/* Target Resource */}
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4 space-y-2">
            <div className="text-[10px] uppercase font-bold text-gray-400 flex items-center gap-1.5">
              <span>🎯</span> Target Resource
            </div>
            <div className="space-y-1 text-xs">
              <div>
                <span className="text-gray-500 text-[10px] uppercase">Type: </span>
                <span className="font-semibold text-white">{log.resource_type || "N/A"}</span>
              </div>
              <div>
                <span className="text-gray-500 text-[10px] uppercase">ID / Key: </span>
                <span className="font-mono text-gray-300 text-[11px] break-all">
                  {log.resource_id || "N/A"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Network & Client Forensics */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-4 space-y-3 text-xs">
          <div className="text-[10px] uppercase font-bold text-gray-400 flex items-center gap-1.5">
            <span>🌐</span> Client Forensics & Network Metadata
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <div className="text-[10px] text-gray-500 uppercase">Client IP Address</div>
              <div className="font-mono text-gray-300 text-xs mt-0.5">
                {log.ip_address || "Unavailable"}
              </div>
            </div>

            <div>
              <div className="text-[10px] text-gray-500 uppercase">Outcome Status</div>
              <div className="mt-0.5">
                <AuditStatusBadge status={log.status} />
              </div>
            </div>
          </div>

          <div>
            <div className="text-[10px] text-gray-500 uppercase">User-Agent</div>
            <div className="mt-1 rounded-xl bg-gray-950 p-2.5 font-mono text-[11px] text-gray-400 break-all border border-gray-800/80">
              {log.user_agent || "Not provided"}
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="rounded-xl bg-gray-800 px-5 py-2.5 text-xs font-semibold text-gray-200 hover:bg-gray-700 transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default AuditDetailModal;
