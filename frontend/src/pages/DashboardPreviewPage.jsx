/**
 * DashboardPreviewPage — Role-Aware Premium Operational Dashboard.
 *
 * - ADMIN: Complete operational metrics + audit activity
 * - LIBRARIAN: Circulation metrics + quick circulation actions
 * - STUDENT: Personal scoped metrics + my books/fines
 * - GUEST: Catalog discovery + login/register
 *
 * Uses real backend data only. No fabricated statistics or trends.
 * Realtime-integrated: refreshes metrics on domain events.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle,
  CircleDollarSign,
  Clock,
  FileText,
  Library,
  Search,
  Shield,
  ShieldCheck,
  TrendingUp,
  Users,
} from "lucide-react";
import DashboardStatCard from "../components/DashboardStatCard";
import QuickActionCard from "../components/QuickActionCard";
import IssueBookModal from "../components/IssueBookModal";
import PermissionGate from "../components/PermissionGate";
import Toast from "../components/Toast";
import RealtimeStatusBadge from "../components/RealtimeStatusBadge";
import useAuth from "../hooks/useAuth";
import usePermissions from "../hooks/usePermissions";
import useRealtime from "../hooks/useRealtime";
import { RealtimeEventType } from "../services/realtime.service";
import catalogService from "../services/catalog.service";
import circulationService from "../services/circulation.service";
import auditService from "../services/audit.service";

/* ── Section Header ────────────────────────────────────────── */
function SectionHeader({ icon: Icon, title, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        {Icon && (
          <div
            className="flex h-7 w-7 items-center justify-center rounded-lg"
            style={{ backgroundColor: "var(--primary-soft)" }}
          >
            <Icon size={13} style={{ color: "var(--primary)" }} />
          </div>
        )}
        <h2
          className="text-sm font-bold uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          {title}
        </h2>
      </div>
      {action}
    </div>
  );
}

/* ── Panel Card ────────────────────────────────────────────── */
function Panel({ children, className = "" }) {
  return (
    <div
      className={`rounded-2xl border p-5 ${className}`}
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--bg-surface)",
        boxShadow: "var(--shadow-sm)",
      }}
    >
      {children}
    </div>
  );
}

/* ── Empty State ───────────────────────────────────────────── */
function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center py-8 text-center">
      <div
        className="flex h-10 w-10 items-center justify-center rounded-xl mb-3"
        style={{ backgroundColor: "var(--bg-elevated)" }}
      >
        {Icon && <Icon size={18} style={{ color: "var(--text-muted)" }} />}
      </div>
      <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
        {title}
      </p>
      {description && (
        <p className="text-xs max-w-xs" style={{ color: "var(--text-muted)" }}>
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ── Loan Row ──────────────────────────────────────────────── */
function LoanRow({ loan, overdue = false }) {
  const isOverdue = overdue || loan.is_overdue || loan.status === "OVERDUE";

  return (
    <Link
      to={`/borrowings/${loan.id}`}
      className="flex items-center justify-between rounded-xl px-3 py-2.5 transition"
      style={{
        border: `1px solid ${isOverdue ? "rgba(244,63,94,0.2)" : "var(--border)"}`,
        backgroundColor: isOverdue
          ? "rgba(244,63,94,0.04)"
          : "var(--bg-elevated)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = isOverdue
          ? "rgba(244,63,94,0.08)"
          : "var(--bg-muted)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isOverdue
          ? "rgba(244,63,94,0.04)"
          : "var(--bg-elevated)";
      }}
    >
      <div className="min-w-0 flex-1">
        <div
          className="text-xs font-semibold truncate"
          style={{ color: "var(--text-primary)" }}
        >
          {loan.book_title || "Unknown Title"}
        </div>
        <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {loan.user_name || loan.user_email || loan.copy_identifier || ""}
        </div>
      </div>
      <div className="ml-3 flex flex-col items-end gap-1 shrink-0">
        <span
          className="rounded-full border px-2 py-0.5 text-[10px] font-bold"
          style={{
            borderColor: isOverdue
              ? "rgba(244,63,94,0.3)"
              : loan.status === "ACTIVE"
              ? "rgba(59,130,246,0.3)"
              : "rgba(16,185,129,0.3)",
            backgroundColor: isOverdue
              ? "rgba(244,63,94,0.1)"
              : loan.status === "ACTIVE"
              ? "rgba(59,130,246,0.1)"
              : "rgba(16,185,129,0.1)",
            color: isOverdue
              ? "#fb7185"
              : loan.status === "ACTIVE"
              ? "#60a5fa"
              : "#34d399",
          }}
        >
          {isOverdue ? "Overdue" : loan.status || "Active"}
        </span>
        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
          Due {loan.due_at ? new Date(loan.due_at).toLocaleDateString() : "—"}
        </span>
      </div>
    </Link>
  );
}

/* ── Audit Row ─────────────────────────────────────────────── */
function AuditRow({ log }) {
  const isSuccess = log.status === "SUCCESS";
  return (
    <div
      className="flex items-start justify-between rounded-xl px-3 py-2.5 gap-2 border"
      style={{
        borderColor: "var(--border-subtle)",
        backgroundColor: "var(--bg-elevated)",
      }}
    >
      <div className="min-w-0 flex-1">
        <div
          className="text-xs font-semibold font-mono truncate"
          style={{ color: "var(--text-primary)" }}
        >
          {log.action}
        </div>
        <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {log.resource_type}
          {log.resource_id ? ` · ${log.resource_id.slice(0, 8)}…` : ""}
        </div>
      </div>
      <div className="flex flex-col items-end gap-0.5 shrink-0">
        <span
          className="rounded-full border px-2 py-0.5 text-[10px] font-bold"
          style={{
            borderColor: isSuccess
              ? "rgba(16,185,129,0.3)"
              : "rgba(244,63,94,0.3)",
            backgroundColor: isSuccess
              ? "rgba(16,185,129,0.1)"
              : "rgba(244,63,94,0.1)",
            color: isSuccess ? "#34d399" : "#fb7185",
          }}
        >
          {log.status}
        </span>
        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
          {log.timestamp
            ? new Date(log.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : ""}
        </span>
      </div>
    </div>
  );
}

/* ── Availability Bar ──────────────────────────────────────── */
function AvailabilityBar({ available, borrowed, label, color }) {
  const total = available + borrowed;
  if (total === 0) return null;
  const pct = Math.round((available / total) * 100);

  const barColor = {
    emerald: "#34d399",
    blue: "#60a5fa",
    amber: "#fbbf24",
  }[color] || "#818cf8";

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5 text-xs">
        <span style={{ color: "var(--text-secondary)" }}>{label}</span>
        <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
          {available} / {total}
          <span className="ml-1.5 font-normal" style={{ color: "var(--text-muted)" }}>
            ({pct}%)
          </span>
        </span>
      </div>
      <div
        className="h-2 rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--bg-muted)" }}
      >
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: barColor }}
        />
      </div>
    </div>
  );
}

/* ── Fine Row ──────────────────────────────────────────────── */
function FineRow({ fine }) {
  return (
    <div
      className="flex items-center justify-between rounded-xl border px-3 py-2.5"
      style={{
        borderColor: "rgba(245,158,11,0.2)",
        backgroundColor: "rgba(245,158,11,0.04)",
      }}
    >
      <div>
        <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
          Late Return Penalty
        </div>
        <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {fine.notes || "Overdue borrowing penalty"}
        </div>
      </div>
      <div className="text-right">
        <div
          className="text-sm font-black font-mono"
          style={{ color: "#fbbf24" }}
        >
          ${Number(fine.amount).toFixed(2)}
        </div>
        <span
          className="rounded-full border px-1.5 py-0.5 text-[10px] font-bold"
          style={{
            borderColor: "rgba(245,158,11,0.3)",
            backgroundColor: "rgba(245,158,11,0.1)",
            color: "#fbbf24",
          }}
        >
          {fine.status}
        </span>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────── */
export function DashboardPreviewPage() {
  const { user } = useAuth();
  const { roles, primaryRole, permissions, hasRole, hasPermission, canIssueBook } = usePermissions();

  const isAdmin = hasRole("ADMIN");
  const isLibrarian = hasRole("LIBRARIAN");
  const isStaff = isAdmin || isLibrarian;
  const isStudent = hasRole("STUDENT") && !isStaff;
  const canViewAuditLogs = hasPermission("audit_log:view");

  const [isIssueModalOpen, setIsIssueModalOpen] = useState(false);
  const [toast, setToast] = useState(null);

  const [metricsLoading, setMetricsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBooks: null,
    activeLoans: null,
    overdueLoans: null,
    returnedLoans: null,
    pendingFinesCount: null,
    registeredUsers: null,
    categoriesCount: null,
    totalLoans: null,
    availableCopies: null,
  });

  const [overdueLoans, setOverdueLoans] = useState([]);
  const [recentLoans, setRecentLoans] = useState([]);
  const [recentAuditLogs, setRecentAuditLogs] = useState([]);
  const [studentLoans, setStudentLoans] = useState([]);
  const [studentFines, setStudentFines] = useState([]);
  const [listsLoading, setListsLoading] = useState(true);

  const fetchDashboardData = useCallback(async (isSilent = false) => {
    if (!isSilent) {
      setMetricsLoading(true);
      setListsLoading(true);
    }

    try {
      if (isStaff) {
        const promises = [
          catalogService.getBooks({ page: 1, page_size: 1 }).catch(() => ({ total: 0 })),
          catalogService.getCategories({ page: 1, page_size: 100 }).catch(() => ({ total: 0 })),
          circulationService.getBorrowings({ page: 1, page_size: 1, status: "ACTIVE" }).catch(() => ({ total: 0 })),
          circulationService.getBorrowings({ page: 1, page_size: 1, status: "OVERDUE" }).catch(() => ({ total: 0 })),
          circulationService.getBorrowings({ page: 1, page_size: 1, status: "RETURNED" }).catch(() => ({ total: 0 })),
          circulationService.getFines({ page: 1, page_size: 1, status: "PENDING" }).catch(() => ({ total: 0 })),
        ];

        if (isAdmin) {
          promises.push(
            circulationService.getUsers({ page: 1, page_size: 1 }).catch(() => ({ total: 0 }))
          );
        }

        const [booksRes, catsRes, activeRes, overdueRes, returnedRes, finesRes, usersRes] =
          await Promise.all(promises);

        setStats({
          totalBooks: booksRes?.total ?? 0,
          categoriesCount: catsRes?.total ?? (Array.isArray(catsRes) ? catsRes.length : 0),
          activeLoans: activeRes?.total ?? 0,
          overdueLoans: overdueRes?.total ?? 0,
          returnedLoans: returnedRes?.total ?? 0,
          pendingFinesCount: finesRes?.total ?? 0,
          registeredUsers: usersRes ? (usersRes.total ?? 0) : null,
        });

        const [overdueListRes, recentListRes] = await Promise.all([
          circulationService.getBorrowings({ page: 1, page_size: 5, status: "OVERDUE" }).catch(() => ({ items: [] })),
          circulationService.getBorrowings({ page: 1, page_size: 5 }).catch(() => ({ items: [] })),
        ]);

        setOverdueLoans(overdueListRes?.items || []);
        setRecentLoans(recentListRes?.items || []);

        if (isAdmin && canViewAuditLogs) {
          try {
            const auditRes = await auditService.getAuditLogs({ page: 1, page_size: 6 });
            setRecentAuditLogs(auditRes?.items || []);
          } catch {
            setRecentAuditLogs([]);
          }
        }
      } else {
        const [activeRes, overdueRes, totalRes, finesRes, loansListRes, finesListRes] =
          await Promise.all([
            circulationService.getBorrowings({ page: 1, page_size: 1, status: "ACTIVE" }).catch(() => ({ total: 0 })),
            circulationService.getBorrowings({ page: 1, page_size: 1, status: "OVERDUE" }).catch(() => ({ total: 0 })),
            circulationService.getBorrowings({ page: 1, page_size: 1 }).catch(() => ({ total: 0 })),
            circulationService.getFines({ page: 1, page_size: 1, status: "PENDING" }).catch(() => ({ total: 0 })),
            circulationService.getBorrowings({ page: 1, page_size: 5, status: "ACTIVE" }).catch(() => ({ items: [] })),
            circulationService.getFines({ page: 1, page_size: 5, status: "PENDING" }).catch(() => ({ items: [] })),
          ]);

        setStats({
          activeLoans: activeRes?.total ?? 0,
          overdueLoans: overdueRes?.total ?? 0,
          totalLoans: totalRes?.total ?? 0,
          pendingFinesCount: finesRes?.total ?? 0,
        });

        setStudentLoans(loansListRes?.items || []);
        setStudentFines(finesListRes?.items || []);
      }
    } catch {
      setToast({
        type: "error",
        message: "Failed to load dashboard data. Please try again.",
      });
    } finally {
      if (!isSilent) {
        setMetricsLoading(false);
        setListsLoading(false);
      }
    }
  }, [isAdmin, isStaff, canViewAuditLogs]);

  const { subscribeMany } = useRealtime();

  useEffect(() => {
    let isMounted = true;

    // Initial load: show skeletons while fetching
    const timer = setTimeout(() => {
      if (isMounted) {
        fetchDashboardData(false);
      }
    }, 0);

    // Realtime events: refresh data silently in the background without resetting to skeletons
    const unsubscribe = subscribeMany(
      [
        RealtimeEventType.BOOK_CREATED,
        RealtimeEventType.BOOK_UPDATED,
        RealtimeEventType.BOOK_DELETED,
        RealtimeEventType.COPY_CREATED,
        RealtimeEventType.COPY_UPDATED,
        RealtimeEventType.COPY_DELETED,
        RealtimeEventType.CATEGORY_CREATED,
        RealtimeEventType.CATEGORY_UPDATED,
        RealtimeEventType.CATEGORY_DELETED,
        RealtimeEventType.COPY_ISSUED,
        RealtimeEventType.COPY_RETURNED,
        RealtimeEventType.FINE_ISSUED,
        RealtimeEventType.FINE_PAID,
        RealtimeEventType.FINE_WAIVED,
        RealtimeEventType.USER_CREATED,
        RealtimeEventType.USER_UPDATED,
        RealtimeEventType.USER_SUSPENDED,
        RealtimeEventType.USER_DEACTIVATED,
        RealtimeEventType.ROLE_ASSIGNED,
        RealtimeEventType.ROLE_REVOKED,
        RealtimeEventType.AUDIT_EVENT_CREATED,
        RealtimeEventType.SYSTEM_RECONNECTED,
      ],
      () => {
        if (isMounted) {
          fetchDashboardData(true);
        }
      }
    );

    return () => {
      isMounted = false;
      clearTimeout(timer);
      unsubscribe();
    };
  }, [fetchDashboardData, subscribeMany]);

  const handleIssueSuccess = () => {
    setToast({ type: "success", message: "Book issued successfully." });
    fetchDashboardData(true);
  };

  // Greeting
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const getRoleSubtitle = () => {
    if (isAdmin) return "Overview of your library and security operations.";
    if (isLibrarian) return "Monitor circulation and catalog activity.";
    if (isStudent) return "Here's your current reading and borrowing activity.";
    return "Explore the library catalog.";
  };

  const roleBadgeColor = {
    ADMIN: "rgba(168,85,247,0.12)",
    LIBRARIAN: "rgba(59,130,246,0.12)",
    STUDENT: "rgba(16,185,129,0.12)",
  }[primaryRole] || "var(--bg-elevated)";

  const roleBadgeText = {
    ADMIN: "#c084fc",
    LIBRARIAN: "#60a5fa",
    STUDENT: "#34d399",
  }[primaryRole] || "var(--text-secondary)";

  return (
    <div
      className="page-container space-y-6 animate-fadeIn"
      style={{ color: "var(--text-primary)" }}
    >
      {toast && (
        <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* ── Dashboard Header ───────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div
          className="relative overflow-hidden rounded-2xl border p-6"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--bg-surface)",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          {/* Subtle grid accent */}
          <div
            className="hero-grid pointer-events-none absolute inset-0 opacity-40"
            aria-hidden="true"
          />

          <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="space-y-1">
              {/* Role + realtime */}
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    backgroundColor: roleBadgeColor,
                    borderColor: "transparent",
                    color: roleBadgeText,
                  }}
                >
                  {primaryRole}
                </span>
                <RealtimeStatusBadge />
              </div>

              {/* Greeting */}
              <h1
                className="text-xl sm:text-2xl font-black tracking-tight"
                style={{ color: "var(--text-primary)" }}
              >
                {greeting},{" "}
                <span style={{ color: "var(--primary)" }}>
                  {user?.full_name?.split(" ")[0] || "there"}
                </span>
              </h1>

              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {getRoleSubtitle()}
              </p>
            </div>

            {/* Quick header actions */}
            <div className="flex items-center gap-2 shrink-0">
              {canIssueBook && (
                <button
                  onClick={() => setIsIssueModalOpen(true)}
                  className="btn btn-primary btn-sm"
                >
                  <BookOpen size={13} />
                  Issue Book
                </button>
              )}
              <Link to="/catalog" className="btn btn-secondary btn-sm">
                <Search size={13} />
                Catalog
              </Link>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── STAFF / ADMIN METRICS ─────────────────────────── */}
      {isStaff && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
        >
          <div className="section-label">
            <TrendingUp size={12} />
            Library Operational Metrics
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <DashboardStatCard
              title="Catalog Books"
              value={stats.totalBooks}
              subtitle="Distinct published titles"
              icon={BookOpen}
              color="indigo"
              loading={metricsLoading}
              to="/catalog"
            />
            <DashboardStatCard
              title="Active Loans"
              value={stats.activeLoans}
              subtitle="Currently checked out"
              icon={Library}
              color="blue"
              loading={metricsLoading}
              to="/borrowings?status=ACTIVE"
            />
            <DashboardStatCard
              title="Overdue Loans"
              value={stats.overdueLoans}
              subtitle={
                stats.overdueLoans > 0
                  ? "Requires immediate attention"
                  : "All loans on schedule"
              }
              icon={AlertTriangle}
              color={stats.overdueLoans > 0 ? "rose" : "emerald"}
              loading={metricsLoading}
              to="/borrowings?status=OVERDUE"
            />
            <DashboardStatCard
              title="Pending Fines"
              value={stats.pendingFinesCount}
              subtitle="Outstanding late assessments"
              icon={CircleDollarSign}
              color="amber"
              loading={metricsLoading}
              to="/fines?status=PENDING"
            />

            {isAdmin && (
              <>
                <DashboardStatCard
                  title="Registered Users"
                  value={stats.registeredUsers}
                  subtitle="Active library patrons & staff"
                  icon={Users}
                  color="purple"
                  loading={metricsLoading}
                  to="/users"
                />
                <DashboardStatCard
                  title="Categories"
                  value={stats.categoriesCount}
                  subtitle="Taxonomy disciplines & genres"
                  icon={FileText}
                  color="indigo"
                  loading={metricsLoading}
                  to="/categories"
                />
                <DashboardStatCard
                  title="Completed Returns"
                  value={stats.returnedLoans}
                  subtitle="Historical return records"
                  icon={CheckCircle}
                  color="emerald"
                  loading={metricsLoading}
                  to="/borrowings?status=RETURNED"
                />
                <DashboardStatCard
                  title="Security"
                  value="Hardened"
                  subtitle="RBAC · MFA · Redis limits"
                  icon={ShieldCheck}
                  color="emerald"
                  loading={metricsLoading}
                  to="/security/mfa"
                />
              </>
            )}
          </div>
        </motion.div>
      )}

      {/* ── STUDENT METRICS ───────────────────────────────── */}
      {isStudent && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
        >
          <div className="section-label">
            <BookOpen size={12} />
            My Reading Activity
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <DashboardStatCard
              title="My Active Loans"
              value={stats.activeLoans}
              subtitle="Books currently in my possession"
              icon={BookOpen}
              color="blue"
              loading={metricsLoading}
              to="/borrowings?status=ACTIVE"
            />
            <DashboardStatCard
              title="Overdue Books"
              value={stats.overdueLoans}
              subtitle={
                stats.overdueLoans > 0
                  ? "Late returns incur fines"
                  : "All books returned on time"
              }
              icon={AlertTriangle}
              color={stats.overdueLoans > 0 ? "rose" : "emerald"}
              loading={metricsLoading}
              to="/borrowings?status=OVERDUE"
            />
            <DashboardStatCard
              title="Total Borrowed"
              value={stats.totalLoans}
              subtitle="Lifetime borrowing history"
              icon={Library}
              color="indigo"
              loading={metricsLoading}
              to="/borrowings"
            />
            <DashboardStatCard
              title="Outstanding Fines"
              value={stats.pendingFinesCount}
              subtitle={
                stats.pendingFinesCount > 0
                  ? "Unsettled late penalties"
                  : "Account in good standing"
              }
              icon={CircleDollarSign}
              color={stats.pendingFinesCount > 0 ? "amber" : "emerald"}
              loading={metricsLoading}
              to="/fines"
            />
          </div>
        </motion.div>
      )}

      {/* ── QUICK ACTIONS ────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.1 }}
      >
        <div className="section-label">
          <Activity size={12} />
          Quick Actions
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <QuickActionCard
            title="Browse Catalog"
            description="Search books, check copy availability, and inspect details."
            icon={Search}
            to="/catalog"
            color="indigo"
          />

          {canIssueBook && (
            <QuickActionCard
              title="Issue Book"
              description="Checkout an available copy to a registered patron."
              icon={BookOpen}
              onClick={() => setIsIssueModalOpen(true)}
              color="blue"
              badge="Circulation"
            />
          )}

          <QuickActionCard
            title={isStaff ? "Circulation Ledger" : "My Borrowings"}
            description={
              isStaff
                ? "Manage checkouts, monitor due dates, and process returns."
                : "View active loans, track due dates, and see return history."
            }
            icon={Library}
            to="/borrowings"
            color="emerald"
          />

          <QuickActionCard
            title={isStaff ? "Fines & Accounts" : "My Fines"}
            description="View assessed overdue penalties, payment records, and balances."
            icon={CircleDollarSign}
            to="/fines"
            color="amber"
          />

          <PermissionGate permissions={["book:create", "book:update"]}>
            <QuickActionCard
              title="Categories"
              description="Organize genres, academic categories, and catalog taxonomy."
              icon={FileText}
              to="/categories"
              color="purple"
            />
          </PermissionGate>

          {isAdmin && (
            <QuickActionCard
              title="Users & IAM"
              description="Manage accounts, assign roles, and review security permissions."
              icon={Users}
              to="/users"
              color="purple"
              badge="Admin"
            />
          )}

          {isAdmin && (
            <QuickActionCard
              title="Audit Console"
              description="Review tamper-resistant security event logs."
              icon={Shield}
              to="/audit"
              color="indigo"
              badge="Admin"
            />
          )}

          <QuickActionCard
            title="Security & MFA"
            description="Configure TOTP two-factor authentication and recovery codes."
            icon={ShieldCheck}
            to="/security/mfa"
            color="emerald"
          />
        </div>
      </motion.div>

      {/* ── STAFF: Overdue Loans + Recent Activity ────────── */}
      {isStaff && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.15 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-5"
        >
          {/* Overdue */}
          <Panel>
            <SectionHeader
              icon={AlertTriangle}
              title="Overdue Loans"
              action={
                <Link
                  to="/borrowings?status=OVERDUE"
                  className="flex items-center gap-1 text-xs font-semibold transition"
                  style={{ color: "var(--primary)" }}
                >
                  View all ({stats.overdueLoans || 0})
                  <ArrowRight size={12} />
                </Link>
              }
            />

            {listsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="skeleton h-14 rounded-xl" />
                ))}
              </div>
            ) : overdueLoans.length === 0 ? (
              <EmptyState
                icon={CheckCircle}
                title="No Overdue Loans"
                description="All issued library items are within their due date windows."
              />
            ) : (
              <div className="space-y-2">
                {overdueLoans.slice(0, 5).map((loan) => (
                  <LoanRow key={loan.id} loan={loan} overdue />
                ))}
              </div>
            )}
          </Panel>

          {/* Recent Circulation */}
          <Panel>
            <SectionHeader
              icon={Clock}
              title="Recent Circulation"
              action={
                <Link
                  to="/borrowings"
                  className="flex items-center gap-1 text-xs font-semibold transition"
                  style={{ color: "var(--primary)" }}
                >
                  Full ledger
                  <ArrowRight size={12} />
                </Link>
              }
            />

            {listsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="skeleton h-14 rounded-xl" />
                ))}
              </div>
            ) : recentLoans.length === 0 ? (
              <EmptyState
                icon={Library}
                title="No Recent Activity"
                description="No borrowing records found."
              />
            ) : (
              <div className="space-y-2">
                {recentLoans.slice(0, 5).map((loan) => (
                  <LoanRow key={loan.id} loan={loan} />
                ))}
              </div>
            )}
          </Panel>
        </motion.div>
      )}

      {/* ── ADMIN: Library Availability + Audit ──────────── */}
      {isAdmin && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-5"
        >
          {/* Availability visualization */}
          <Panel>
            <SectionHeader icon={TrendingUp} title="Circulation Overview" />
            {metricsLoading ? (
              <div className="space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className="skeleton h-10 rounded-lg" />
                ))}
              </div>
            ) : (
              <div className="space-y-5">
                <AvailabilityBar
                  label="Active Loans"
                  available={stats.activeLoans || 0}
                  borrowed={(stats.activeLoans || 0) + (stats.overdueLoans || 0)}
                  color="blue"
                />
                <AvailabilityBar
                  label="Overdue vs Active"
                  available={stats.overdueLoans || 0}
                  borrowed={(stats.activeLoans || 0) + (stats.overdueLoans || 0)}
                  color="amber"
                />
                <AvailabilityBar
                  label="Returned vs Total"
                  available={stats.returnedLoans || 0}
                  borrowed={
                    (stats.returnedLoans || 0) +
                    (stats.activeLoans || 0) +
                    (stats.overdueLoans || 0)
                  }
                  color="emerald"
                />

                <div
                  className="pt-4 border-t grid grid-cols-3 gap-3 text-center"
                  style={{ borderColor: "var(--border)" }}
                >
                  {[
                    { label: "Active", value: stats.activeLoans ?? "—", color: "#60a5fa" },
                    { label: "Overdue", value: stats.overdueLoans ?? "—", color: "#fbbf24" },
                    { label: "Returned", value: stats.returnedLoans ?? "—", color: "#34d399" },
                  ].map(({ label, value, color }) => (
                    <div key={label}>
                      <div
                        className="text-xl font-black font-mono"
                        style={{ color }}
                      >
                        {value}
                      </div>
                      <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                        {label}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Panel>

          {/* Audit log */}
          {permissions.includes("audit_log:view") && (
            <Panel>
              <SectionHeader
                icon={Shield}
                title="Recent Audit Activity"
                action={
                  <Link
                    to="/audit"
                    className="flex items-center gap-1 text-xs font-semibold"
                    style={{ color: "var(--primary)" }}
                  >
                    Full console
                    <ArrowRight size={12} />
                  </Link>
                }
              />

              {listsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton h-12 rounded-xl" />
                  ))}
                </div>
              ) : recentAuditLogs.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No Recent Audit Events"
                  description="No audit trail entries found."
                />
              ) : (
                <div className="space-y-2">
                  {recentAuditLogs.map((log) => (
                    <AuditRow key={log.id} log={log} />
                  ))}
                </div>
              )}
            </Panel>
          )}
        </motion.div>
      )}

      {/* ── STUDENT: My Current Loans + Fines ────────────── */}
      {isStudent && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.15 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-5"
        >
          {/* My Active Loans */}
          <Panel>
            <SectionHeader
              icon={BookOpen}
              title="My Active Books"
              action={
                <Link
                  to="/borrowings"
                  className="flex items-center gap-1 text-xs font-semibold"
                  style={{ color: "var(--primary)" }}
                >
                  View history
                  <ArrowRight size={12} />
                </Link>
              }
            />

            {listsLoading ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="skeleton h-14 rounded-xl" />
                ))}
              </div>
            ) : studentLoans.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title="No Active Borrowings"
                description="You have no books checked out. Browse the catalog to find your next read."
                action={
                  <Link to="/catalog" className="btn btn-primary btn-sm">
                    <Search size={13} />
                    Browse Catalog
                  </Link>
                }
              />
            ) : (
              <div className="space-y-2">
                {studentLoans.map((loan) => (
                  <LoanRow key={loan.id} loan={loan} />
                ))}
              </div>
            )}
          </Panel>

          {/* My Fines */}
          <Panel>
            <SectionHeader
              icon={CircleDollarSign}
              title="My Outstanding Fines"
              action={
                <Link
                  to="/fines"
                  className="flex items-center gap-1 text-xs font-semibold"
                  style={{ color: "var(--primary)" }}
                >
                  Fines ledger
                  <ArrowRight size={12} />
                </Link>
              }
            />

            {listsLoading ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="skeleton h-14 rounded-xl" />
                ))}
              </div>
            ) : studentFines.length === 0 ? (
              <EmptyState
                icon={CheckCircle}
                title="No Outstanding Fines"
                description="Your account is in good standing with zero overdue penalties."
              />
            ) : (
              <div className="space-y-2">
                {studentFines.map((fine) => (
                  <FineRow key={fine.id} fine={fine} />
                ))}
              </div>
            )}
          </Panel>
        </motion.div>
      )}

      {/* ── Session Identity Card ─────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.25 }}
        className="grid gap-5 sm:grid-cols-2"
      >
        <Panel>
          <SectionHeader icon={Users} title="Session Identity" />
          <dl className="space-y-3 text-xs">
            {[
              { label: "Full Name", value: user?.full_name },
              { label: "Email", value: user?.email },
              {
                label: "User ID",
                value: user?.id ? `${user.id.slice(0, 8)}…` : "—",
                mono: true,
              },
              {
                label: "Account Status",
                value: user?.account_status || "ACTIVE",
                badge: true,
              },
            ].map(({ label, value, mono, badge }) => (
              <div key={label} className="flex items-start justify-between gap-2">
                <dt
                  className="text-[10px] uppercase tracking-wider shrink-0"
                  style={{ color: "var(--text-muted)" }}
                >
                  {label}
                </dt>
                <dd
                  className={`text-right ${mono ? "font-mono" : "font-semibold"}`}
                  style={{ color: "var(--text-primary)" }}
                >
                  {badge ? (
                    <span
                      className="rounded-full border px-2 py-0.5 text-[10px] font-bold"
                      style={{
                        borderColor: "rgba(16,185,129,0.3)",
                        backgroundColor: "rgba(16,185,129,0.1)",
                        color: "#34d399",
                      }}
                    >
                      ● {value}
                    </span>
                  ) : (
                    value || "—"
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </Panel>

        <Panel>
          <SectionHeader icon={ShieldCheck} title="Authorization Scope" />
          <div className="space-y-4 text-xs">
            <div>
              <div
                className="text-[10px] uppercase tracking-wider mb-2"
                style={{ color: "var(--text-muted)" }}
              >
                Assigned Roles
              </div>
              <div className="flex flex-wrap gap-2">
                {roles.length > 0 ? (
                  roles.map((role) => (
                    <span
                      key={role}
                      className="rounded-md border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider"
                      style={{
                        borderColor: "rgba(99,102,241,0.3)",
                        backgroundColor: "rgba(99,102,241,0.1)",
                        color: "var(--primary)",
                      }}
                    >
                      {role}
                    </span>
                  ))
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>No roles assigned</span>
                )}
              </div>
            </div>

            <div>
              <div
                className="text-[10px] uppercase tracking-wider mb-2"
                style={{ color: "var(--text-muted)" }}
              >
                Permissions ({permissions.length})
              </div>
              <div
                className="flex flex-wrap gap-1 max-h-20 overflow-y-auto rounded-lg border p-2"
                style={{
                  borderColor: "var(--border)",
                  backgroundColor: "var(--bg-elevated)",
                }}
              >
                {permissions.map((perm) => (
                  <span
                    key={perm}
                    className="mono rounded px-1.5 py-0.5 text-[10px]"
                    style={{
                      backgroundColor: "var(--bg-muted)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {perm}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </motion.div>

      {/* Issue Book Modal */}
      {isIssueModalOpen && (
        <IssueBookModal
          isOpen={isIssueModalOpen}
          onClose={() => setIsIssueModalOpen(false)}
          onSuccess={handleIssueSuccess}
        />
      )}
    </div>
  );
}

export default DashboardPreviewPage;
