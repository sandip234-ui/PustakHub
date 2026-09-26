/**
 * Navbar — Top Application Navigation Bar.
 *
 * Premium SaaS-quality navigation with:
 * - Role-aware links (ADMIN / LIBRARIAN / STUDENT / GUEST)
 * - Light/Dark/System theme toggle
 * - Realtime status badge
 * - Accessible mobile menu
 * - Profile dropdown
 * - Keyboard accessible, focus-visible
 */

import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  BookOpen,
  ChevronDown,
  CircleDollarSign,
  FileText,
  LayoutDashboard,
  Library,
  LogOut,
  Menu,
  Monitor,
  Moon,
  Search,
  Settings,
  Shield,
  ShieldCheck,
  Sun,
  Users,
  X,
} from "lucide-react";
import useAuth from "../hooks/useAuth";
import usePermissions from "../hooks/usePermissions";
import useTheme from "../hooks/useTheme";
import RealtimeStatusBadge from "./RealtimeStatusBadge";

/* ── Theme Toggle ─────────────────────────────────────────── */
function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const options = [
    { value: "light", label: "Light", Icon: Sun },
    { value: "dark", label: "Dark", Icon: Moon },
    { value: "system", label: "System", Icon: Monitor },
  ];

  const CurrentIcon =
    theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:text-[var(--text-primary)] focus-visible:outline-2 focus-visible:outline-[var(--primary)]"
        aria-label="Toggle theme"
        title="Switch theme"
      >
        <CurrentIcon size={15} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-36 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-1 shadow-[var(--shadow-lg)] z-50">
          {options.map(({ value, label, Icon }) => (
            <button
              key={value}
              onClick={() => {
                setTheme(value);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${
                theme === value
                  ? "bg-[var(--primary-soft)] text-[var(--primary)] font-semibold"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Profile Dropdown ────────────────────────────────────── */
function ProfileDropdown({ user, primaryRole, getRoleBadgeStyle, onLogout, isLoggingOut }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const initials = (user?.full_name || user?.email || "U")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-2.5 py-1.5 text-sm transition hover:border-[var(--border-strong)] focus-visible:outline-2 focus-visible:outline-[var(--primary)]"
        aria-label="Open profile menu"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600/20 text-[10px] font-bold text-indigo-400">
          {initials}
        </span>
        <span className="hidden sm:block max-w-[100px] truncate text-[var(--text-primary)] text-xs font-medium">
          {user?.full_name?.split(" ")[0] || user?.email?.split("@")[0]}
        </span>
        <ChevronDown
          size={12}
          className={`text-[var(--text-muted)] transition ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-52 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-2 shadow-[var(--shadow-lg)] z-50">
          {/* User info */}
          <div className="mb-2 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-3">
            <div className="text-xs font-semibold text-[var(--text-primary)] truncate">
              {user?.full_name || user?.email}
            </div>
            <div className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">
              {user?.email}
            </div>
            <span
              className={`mt-1.5 inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getRoleBadgeStyle(primaryRole)}`}
            >
              {primaryRole}
            </span>
          </div>

          <Link
            to="/security/mfa"
            onClick={() => setOpen(false)}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-[var(--text-secondary)] transition hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]"
          >
            <Shield size={13} />
            Security & MFA
          </Link>

          <div className="my-1 border-t border-[var(--border)]" />

          <button
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            disabled={isLoggingOut}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-[var(--danger-text)] transition hover:bg-[var(--danger-bg)] disabled:opacity-50"
          >
            <LogOut size={13} />
            {isLoggingOut ? "Signing out..." : "Sign Out"}
          </button>
        </div>
      )}
    </div>
  );
}

/* ── Main Navbar ──────────────────────────────────────────── */
export function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const { isStaff, hasRole, primaryRole } = usePermissions();
  const isAdmin = hasRole("ADMIN");
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Mobile menu close handler
  const handleNavClick = () => {
    setIsMobileMenuOpen(false);
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      navigate("/login");
    } finally {
      setIsLoggingOut(false);
    }
  };

  const isActive = (path) => {
    if (path === "/" && location.pathname !== "/") return false;
    return location.pathname.startsWith(path);
  };

  const navLinkClass = (path) =>
    `flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
      isActive(path)
        ? "bg-[var(--primary-soft)] text-[var(--primary)]"
        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]"
    }`;

  const getRoleBadgeStyle = (role) => {
    switch ((role || "").toUpperCase()) {
      case "ADMIN":
        return "bg-purple-500/10 border-purple-500/30 text-purple-400 dark:text-purple-300";
      case "LIBRARIAN":
        return "bg-blue-500/10 border-blue-500/30 text-blue-400 dark:text-blue-300";
      case "STUDENT":
        return "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-300";
      default:
        return "bg-[var(--bg-muted)] border-[var(--border)] text-[var(--text-muted)]";
    }
  };

  const navLinks = isAuthenticated ? (
    <>
      <Link to="/dashboard" className={navLinkClass("/dashboard")}>
        <LayoutDashboard size={14} />
        Dashboard
      </Link>
      <Link to="/catalog" className={navLinkClass("/catalog")}>
        <BookOpen size={14} />
        Catalog
      </Link>
      <Link to="/borrowings" className={navLinkClass("/borrowings")}>
        <Library size={14} />
        Borrowings
      </Link>
      <Link to="/fines" className={navLinkClass("/fines")}>
        <CircleDollarSign size={14} />
        Fines
      </Link>
      {isStaff && (
        <Link to="/categories" className={navLinkClass("/categories")}>
          <FileText size={14} />
          Categories
        </Link>
      )}
      {isAdmin && (
        <Link to="/users" className={navLinkClass("/users")}>
          <Users size={14} />
          Users
        </Link>
      )}
      {isStaff && (
        <Link to="/audit" className={navLinkClass("/audit")}>
          <Activity size={14} />
          Audit
        </Link>
      )}
    </>
  ) : (
    <>
      <Link to="/" className={navLinkClass("/")}>
        Home
      </Link>
      <Link to="/catalog" className={navLinkClass("/catalog")}>
        <Search size={14} />
        Catalog
      </Link>
    </>
  );

  return (
    <nav
      className="navbar"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between gap-4">

          {/* Brand */}
          <div className="flex items-center gap-6 shrink-0">
            <Link
              to={isAuthenticated ? "/dashboard" : "/"}
              className="flex items-center gap-2.5 font-bold text-[var(--text-primary)] hover:opacity-90 transition"
              aria-label="PustakHub home"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600/15 border border-indigo-500/25 text-indigo-500 shadow-sm">
                <ShieldCheck size={17} />
              </span>
              <span className="text-[15px] tracking-tight">PustakHub</span>
            </Link>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-0.5">
              {navLinks}
            </div>
          </div>

          {/* Right side controls */}
          <div className="hidden md:flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <RealtimeStatusBadge />
                <ThemeToggle />
                <ProfileDropdown
                  user={user}
                  primaryRole={primaryRole}
                  getRoleBadgeStyle={getRoleBadgeStyle}
                  onLogout={handleLogout}
                  isLoggingOut={isLoggingOut}
                />
              </>
            ) : (
              <>
                <ThemeToggle />
                <Link
                  to="/login"
                  className="btn btn-secondary btn-sm"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="btn btn-primary btn-sm"
                >
                  Register
                </Link>
              </>
            )}
          </div>

          {/* Mobile: theme + hamburger */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] transition hover:text-[var(--text-primary)]"
              aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-[var(--border)] bg-[var(--bg)] px-4 pt-3 pb-5 space-y-1 animate-fadeIn">
          {isAuthenticated ? (
            <>
              {/* User info strip */}
              <div className="flex items-center justify-between px-3 py-2 mb-2 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)]">
                <div>
                  <div className="text-xs font-semibold text-[var(--text-primary)]">
                    {user?.full_name || user?.email}
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)]">{user?.email}</div>
                </div>
                <div className="flex items-center gap-2">
                  <RealtimeStatusBadge />
                  <span
                    className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getRoleBadgeStyle(primaryRole)}`}
                  >
                    {primaryRole}
                  </span>
                </div>
              </div>

              {/* Mobile nav links */}
              {[
                { to: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
                { to: "/catalog", label: "Catalog", Icon: BookOpen },
                { to: "/borrowings", label: "Borrowings", Icon: Library },
                { to: "/fines", label: "Fines", Icon: CircleDollarSign },
                ...(isStaff ? [{ to: "/categories", label: "Categories", Icon: FileText }] : []),
                ...(isAdmin ? [{ to: "/users", label: "Users & IAM", Icon: Users }] : []),
                ...(isStaff ? [{ to: "/audit", label: "Audit Trails", Icon: Activity }] : []),
                { to: "/security/mfa", label: "Security / MFA", Icon: Settings },
              ].map(({ to, label, Icon }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={handleNavClick}
                  className={`flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition ${
                    isActive(to)
                      ? "bg-[var(--primary-soft)] text-[var(--primary)] font-semibold"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  <Icon size={15} />
                  {label}
                </Link>
              ))}

              <div className="pt-2 border-t border-[var(--border)]">
                <button
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm text-[var(--danger-text)] transition hover:bg-[var(--danger-bg)] disabled:opacity-50"
                >
                  <LogOut size={15} />
                  {isLoggingOut ? "Signing out..." : "Sign Out"}
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                to="/"
                onClick={handleNavClick}
                className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)] transition"
              >
                Home
              </Link>
              <Link
                to="/catalog"
                onClick={handleNavClick}
                className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)] transition"
              >
                <Search size={15} />
                Catalog
              </Link>
              <div className="pt-2 grid grid-cols-2 gap-2 border-t border-[var(--border)]">
                <Link
                  to="/login"
                  onClick={handleNavClick}
                  className="btn btn-secondary text-center justify-center"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  onClick={handleNavClick}
                  className="btn btn-primary text-center justify-center"
                >
                  Register
                </Link>
              </div>
            </>
          )}
        </div>
      )}
    </nav>
  );
}

export default Navbar;
