/**
 * HomePage — PustakHub landing page.
 *
 * Premium hero with:
 * - Hover.dev-inspired subtle grid + radial glow
 * - Motion entrance animations
 * - Real backend health status
 * - Theme-aware design
 * - prefers-reduced-motion respect
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  Activity,
  ArrowRight,
  BookOpen,
  CheckCircle,
  ChevronRight,
  Database,
  ShieldCheck,
  Users,
  XCircle,
  Zap,
} from "lucide-react";
import useAuth from "../hooks/useAuth";
import { fetchHealth } from "../services/health.service";

/* Feature pills */
const FEATURES = [
  { icon: ShieldCheck, label: "RBAC Security" },
  { icon: Activity, label: "Real-time Updates" },
  { icon: BookOpen, label: "Catalog Management" },
  { icon: Users, label: "IAM & MFA" },
];

function FeaturePill({ icon: Icon, label }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--bg-elevated)",
        color: "var(--text-secondary)",
      }}
    >
      <Icon size={12} style={{ color: "var(--primary)" }} />
      {label}
    </span>
  );
}

function StatusDot({ ok }) {
  return (
    <span
      className={`inline-flex h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`}
      style={ok ? { animation: "pulse-glow 2s ease-in-out infinite" } : {}}
    />
  );
}

function HomePage() {
  const { isAuthenticated, user } = useAuth();
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => setHealthError(err.message || "Connection failed"))
      .finally(() => setHealthLoading(false));
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.08, delayChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
  };

  return (
    <div
      className="relative flex min-h-[calc(100vh-56px)] items-center justify-center overflow-hidden px-4 py-16"
      style={{ backgroundColor: "var(--bg)" }}
    >
      {/* Subtle grid background (Hover.dev inspired) */}
      <div
        className="hero-grid pointer-events-none absolute inset-0"
        aria-hidden="true"
      />

      {/* Radial glow (Hover.dev inspired) */}
      <div
        className="radial-glow pointer-events-none absolute inset-0"
        aria-hidden="true"
      />

      {/* Content */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 w-full max-w-xl text-center"
      >
        {/* Logo mark */}
        <motion.div variants={itemVariants} className="flex justify-center mb-6">
          <div
            className="flex h-16 w-16 items-center justify-center rounded-2xl border shadow-lg"
            style={{
              backgroundColor: "var(--primary-soft)",
              borderColor: "rgba(99,102,241,0.25)",
              boxShadow: "0 8px 32px var(--primary-glow)",
            }}
          >
            <ShieldCheck size={32} style={{ color: "var(--primary)" }} />
          </div>
        </motion.div>

        {/* Badge */}
        <motion.div variants={itemVariants} className="flex justify-center mb-4">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wider"
            style={{
              borderColor: "rgba(99,102,241,0.3)",
              backgroundColor: "var(--primary-soft)",
              color: "var(--primary)",
            }}
          >
            <Zap size={10} />
            Enterprise Library Platform
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={itemVariants}
          className="text-4xl sm:text-5xl font-black tracking-tight mb-4"
          style={{ color: "var(--text-primary)", lineHeight: 1.1 }}
        >
          PustakHub
        </motion.h1>

        <motion.p
          variants={itemVariants}
          className="text-lg mb-2"
          style={{ color: "var(--text-secondary)" }}
        >
          Secure Library & Identity Management Platform
        </motion.p>

        <motion.p
          variants={itemVariants}
          className="text-sm mb-8 max-w-md mx-auto"
          style={{ color: "var(--text-muted)" }}
        >
          Role-based access control, real-time circulation tracking, MFA
          authentication, and comprehensive audit trails.
        </motion.p>

        {/* Feature pills */}
        <motion.div
          variants={itemVariants}
          className="flex flex-wrap justify-center gap-2 mb-8"
        >
          {FEATURES.map(({ icon, label }) => (
            <FeaturePill key={label} icon={icon} label={label} />
          ))}
        </motion.div>

        {/* CTAs */}
        <motion.div
          variants={itemVariants}
          className="flex flex-wrap items-center justify-center gap-3"
        >
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="btn btn-primary btn-lg group"
            >
              Go to Dashboard
              <span className="text-white/60">{user?.full_name?.split(" ")[0]}</span>
              <ArrowRight
                size={16}
                className="transition-transform group-hover:translate-x-1"
              />
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn btn-primary btn-lg group">
                Get Started
                <ChevronRight
                  size={16}
                  className="transition-transform group-hover:translate-x-1"
                />
              </Link>
              <Link to="/login" className="btn btn-secondary btn-lg">
                Log In
              </Link>
            </>
          )}
          <Link
            to="/catalog"
            className="btn btn-ghost btn-lg"
            style={{ color: "var(--text-secondary)" }}
          >
            <BookOpen size={15} />
            Browse Catalog
          </Link>
        </motion.div>

        {/* System Status Card */}
        <motion.div variants={itemVariants} className="mt-12">
          {healthLoading && (
            <div className="flex items-center justify-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
              <div className="skeleton h-3 w-3 rounded-full" />
              Checking system status...
            </div>
          )}

          {healthError && (
            <div
              className="rounded-xl border px-4 py-3 text-sm flex items-center gap-2"
              style={{
                borderColor: "rgba(239,68,68,0.2)",
                backgroundColor: "var(--danger-bg)",
                color: "var(--danger-text)",
              }}
            >
              <XCircle size={14} />
              {healthError}
            </div>
          )}

          {health && (
            <div
              className="rounded-2xl border p-5 text-left"
              style={{
                borderColor: "var(--border)",
                backgroundColor: "var(--bg-surface)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div
                className="flex items-center justify-between pb-3 mb-3 border-b"
                style={{ borderColor: "var(--border)" }}
              >
                <span
                  className="text-[11px] font-bold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  System Status
                </span>
                <span
                  className="inline-flex items-center gap-1.5 text-xs font-semibold"
                  style={{ color: "var(--success-text)" }}
                >
                  <StatusDot ok />
                  {health.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                {[
                  { label: "Service", value: health.service, icon: ShieldCheck },
                  { label: "Version", value: health.version, icon: Activity },
                  {
                    label: "Database",
                    value: health.database,
                    icon: Database,
                    ok: health.database?.toLowerCase().includes("connected") || health.database === "ok",
                  },
                  {
                    label: "Redis",
                    value: health.redis,
                    icon: Zap,
                    ok: health.redis?.toLowerCase().includes("connected") || health.redis === "ok",
                  },
                ].map(({ label, value, icon: Icon, ok }) => (
                  <div key={label} className="flex items-start gap-2">
                    <Icon
                      size={12}
                      className="mt-0.5 shrink-0"
                      style={{ color: ok !== undefined ? (ok ? "var(--success-text)" : "var(--danger-text)") : "var(--text-muted)" }}
                    />
                    <div>
                      <div style={{ color: "var(--text-muted)" }}>{label}</div>
                      <div
                        className="font-semibold"
                        style={{ color: ok !== undefined ? (ok ? "var(--success-text)" : "var(--danger-text)") : "var(--text-primary)" }}
                      >
                        {ok !== undefined && (
                          <span className="inline-block mr-1">
                            {ok ? <CheckCircle size={10} className="inline" /> : <XCircle size={10} className="inline" />}
                          </span>
                        )}
                        {value}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}

export default HomePage;
