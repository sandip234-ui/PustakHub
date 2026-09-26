/**
 * MainLayout — Top-level application layout with Navbar and Footer.
 * Theme-aware using CSS variables from design system.
 */

import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import { ShieldCheck } from "lucide-react";

function MainLayout() {
  return (
    <div
      className="min-h-screen flex flex-col font-sans antialiased"
      style={{ backgroundColor: "var(--bg)", color: "var(--text-primary)" }}
    >
      {/* Top Application Navigation */}
      <Navbar />

      {/* Main Routed Content Area */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer
        className="border-t py-5"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--bg)",
        }}
      >
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
            <ShieldCheck size={13} className="text-indigo-500/60" />
            <span>PustakHub — Secure Library & Identity Management Platform</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <span>Enterprise Edition</span>
            <span className="h-3 w-px" style={{ backgroundColor: "var(--border)" }} />
            <span>RBAC · MFA · Realtime · Audit</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default MainLayout;
