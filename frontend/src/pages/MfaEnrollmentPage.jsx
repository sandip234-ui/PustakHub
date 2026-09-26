/**
 * MfaEnrollmentPage — Authenticated TOTP Multi-Factor Authentication Setup.
 * Generates TOTP secret and recovery codes, requiring 6-digit confirmation to activate.
 */

import { AlertTriangle, CheckCircle, ShieldCheck, ShieldOff, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { AuthError, AuthLabel } from "../components/AuthCard";
import useAuth from "../hooks/useAuth";
import authService from "../services/auth.service";

export function MfaEnrollmentPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [statusLoading, setStatusLoading] = useState(true);
  const [isMfaEnabled, setIsMfaEnabled] = useState(false);

  const [enrollData, setEnrollData] = useState(null);
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState(null);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [success, setSuccess] = useState(false);

  const [showDisableModal, setShowDisableModal] = useState(false);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [disableError, setDisableError] = useState(null);
  const [isDisabling, setIsDisabling] = useState(false);

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await authService.getMfaStatus();
        setIsMfaEnabled(Boolean(res.enabled ?? res.is_mfa_enabled));
      } catch {
        setError("Failed to fetch MFA status.");
      } finally {
        setStatusLoading(false);
      }
    }
    checkStatus();
  }, []);

  const handleStartEnrollment = async () => {
    setError(null);
    setIsEnrolling(true);
    try {
      const data = await authService.enrollMfa();
      setEnrollData(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start MFA enrollment.");
    } finally {
      setIsEnrolling(false);
    }
  };

  const handleVerifyEnrollment = async (e) => {
    e.preventDefault();
    setError(null);
    setIsVerifying(true);

    try {
      await authService.verifyMfaEnrollment({ code: totpCode.trim() });
      setSuccess(true);
      setIsMfaEnabled(true);
      if (refreshUser) await refreshUser();
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid TOTP code. Please try again.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDisableMfa = async (e) => {
    e.preventDefault();
    setDisableError(null);
    setIsDisabling(true);

    try {
      await authService.disableMfa({ password: disablePassword, code: disableCode.trim() });
      setIsMfaEnabled(false);
      setEnrollData(null);
      setShowDisableModal(false);
      if (refreshUser) await refreshUser();
    } catch (err) {
      setDisableError(err.response?.data?.detail || "Failed to disable MFA. Check your credentials.");
    } finally {
      setIsDisabling(false);
    }
  };

  if (statusLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center" style={{ backgroundColor: "var(--bg)" }}>
        <div
          className="h-8 w-8 animate-spin rounded-full border-2 border-t-transparent"
          style={{ borderColor: "var(--primary)" }}
        />
      </div>
    );
  }

  return (
    <div
      className="mx-auto max-w-2xl px-4 py-10"
      style={{ color: "var(--text-primary)" }}
    >
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black sm:text-3xl" style={{ color: "var(--text-primary)" }}>
              Two-Factor Authentication
            </h1>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Enhance your account security using a Time-based One-Time Password (TOTP) authenticator app.
            </p>
          </div>
          <span
            className="shrink-0 px-3 py-1 text-xs font-bold rounded-full border"
            style={
              isMfaEnabled
                ? {
                    backgroundColor: "rgba(16,185,129,0.1)",
                    borderColor: "rgba(16,185,129,0.3)",
                    color: "var(--success-text)",
                  }
                : {
                    backgroundColor: "rgba(245,158,11,0.1)",
                    borderColor: "rgba(245,158,11,0.3)",
                    color: "#b45309",
                  }
            }
          >
            {isMfaEnabled ? "Enabled" : "Disabled"}
          </span>
        </div>
      </div>

      <AuthError message={error} />

      {/* MFA Enabled state */}
      {isMfaEnabled && !enrollData && !success ? (
        <div
          className="rounded-2xl border p-6 space-y-6"
          style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}
        >
          <div className="flex items-start gap-4">
            <div
              className="rounded-xl p-3 border shrink-0"
              style={{
                backgroundColor: "rgba(16,185,129,0.1)",
                borderColor: "rgba(16,185,129,0.3)",
              }}
            >
              <ShieldCheck size={22} style={{ color: "var(--success-text)" }} />
            </div>
            <div>
              <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Your account is protected by MFA
              </h2>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                You will be prompted for a 6-digit TOTP code or backup recovery code every time you log in.
              </p>
            </div>
          </div>

          <div
            className="pt-4 border-t flex justify-between items-center"
            style={{ borderColor: "var(--border)" }}
          >
            <Link
              to="/dashboard"
              className="text-sm font-semibold"
              style={{ color: "var(--primary)" }}
            >
              ← Back to Dashboard
            </Link>

            <button
              onClick={() => setShowDisableModal(true)}
              className="btn btn-danger"
            >
              <ShieldOff size={14} />
              Disable MFA
            </button>
          </div>
        </div>
      ) : success ? (
        /* Success state */
        <div
          className="rounded-2xl border p-6 sm:p-8 space-y-6"
          style={{
            borderColor: "rgba(16,185,129,0.3)",
            backgroundColor: "var(--bg-surface)",
          }}
        >
          <div className="text-center">
            <div
              className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border mb-4"
              style={{
                backgroundColor: "rgba(16,185,129,0.1)",
                borderColor: "rgba(16,185,129,0.3)",
              }}
            >
              <CheckCircle size={30} style={{ color: "var(--success-text)" }} />
            </div>
            <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              MFA Successfully Activated!
            </h2>
            <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
              Two-factor authentication is now active on your account.
            </p>
          </div>

          {enrollData?.recovery_codes && (
            <div
              className="rounded-xl border p-5"
              style={{
                borderColor: "rgba(245,158,11,0.3)",
                backgroundColor: "rgba(245,158,11,0.07)",
              }}
            >
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={15} style={{ color: "#b45309" }} />
                <h3
                  className="font-bold text-sm uppercase tracking-wide"
                  style={{ color: "#b45309" }}
                >
                  Store Your One-Time Recovery Codes
                </h3>
              </div>
              <p className="text-xs mb-4" style={{ color: "var(--text-muted)" }}>
                These recovery codes can be used to log in if you lose access to your authenticator app.
                Each code is single-use and will never be shown again!
              </p>
              <div
                className="grid grid-cols-2 gap-2 p-4 rounded-lg font-mono text-sm border"
                style={{
                  backgroundColor: "var(--bg)",
                  borderColor: "var(--border)",
                  color: "var(--primary)",
                }}
              >
                {enrollData.recovery_codes.map((code, idx) => (
                  <div key={idx} className="tracking-wider">
                    {code}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button onClick={() => navigate("/dashboard")} className="btn btn-primary">
              Done & Return to Dashboard
            </button>
          </div>
        </div>
      ) : enrollData ? (
        /* Enrollment form */
        <div
          className="rounded-2xl border p-6 sm:p-8 space-y-6"
          style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}
        >
          <div>
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              Step 1: Scan Authenticator Code
            </h2>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Add PustakHub to Google Authenticator, Microsoft Authenticator, Authy, or 1Password.
            </p>
          </div>

          <div
            className="flex flex-col sm:flex-row items-center gap-6 p-5 rounded-xl border"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg)" }}
          >
            {/* QR Code always has white background — required for scanner */}
            <div className="bg-white p-3 rounded-xl shadow-lg flex items-center justify-center shrink-0">
              <QRCodeSVG
                value={enrollData.otpauth_uri}
                size={144}
                bgColor="#ffffff"
                fgColor="#000000"
                level="M"
              />
            </div>
            <div className="space-y-2 text-center sm:text-left flex-1">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Manual Entry Secret
              </span>
              <div
                className="font-mono text-xs sm:text-sm p-2.5 rounded-lg border break-all select-all"
                style={{
                  borderColor: "var(--border-strong)",
                  backgroundColor: "var(--bg-elevated)",
                  color: "var(--primary)",
                }}
              >
                {enrollData.secret}
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                If you cannot scan the QR code, type the secret key manually into your authenticator app.
              </p>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              Step 2: Verify Setup
            </h2>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Enter the 6-digit code displayed in your authenticator app to confirm and activate MFA.
            </p>
          </div>

          <form onSubmit={handleVerifyEnrollment} className="space-y-4">
            <div>
              <AuthLabel htmlFor="totp">6-Digit TOTP Code</AuthLabel>
              <input
                id="totp"
                type="text"
                required
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder="123456"
                className="input mono text-center text-xl tracking-widest sm:max-w-[200px]"
                style={{ color: "var(--primary)" }}
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={isVerifying || totpCode.length < 6}
                className="btn btn-primary"
              >
                {isVerifying ? "Verifying…" : "Verify & Enable MFA"}
              </button>
              <button
                type="button"
                onClick={() => setEnrollData(null)}
                className="btn btn-ghost"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      ) : (
        /* Start enrollment CTA */
        <div
          className="rounded-2xl border p-6 sm:p-8 space-y-6 text-center"
          style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}
        >
          <div
            className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border"
            style={{
              backgroundColor: "var(--primary-soft)",
              borderColor: "rgba(99,102,241,0.25)",
            }}
          >
            <ShieldCheck size={30} style={{ color: "var(--primary)" }} />
          </div>
          <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Protect Your PustakHub Account
          </h2>
          <p className="max-w-md mx-auto text-sm" style={{ color: "var(--text-secondary)" }}>
            Multi-Factor Authentication adds an extra layer of security. Along with your password, you will be required to provide a temporary 6-digit code.
          </p>

          <button onClick={handleStartEnrollment} disabled={isEnrolling} className="btn btn-primary">
            {isEnrolling ? "Initializing…" : "Begin MFA Enrollment"}
          </button>
        </div>
      )}

      {/* Disable MFA Modal */}
      {showDisableModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4" style={{ backgroundColor: "rgba(0,0,0,0.75)" }}>
          <div
            className="w-full max-w-md rounded-2xl border p-6 shadow-2xl"
            style={{
              backgroundColor: "var(--bg-surface)",
              borderColor: "var(--border)",
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                Disable Multi-Factor Authentication
              </h3>
              <button
                onClick={() => setShowDisableModal(false)}
                className="rounded-lg p-1.5 transition"
                style={{ color: "var(--text-muted)" }}
              >
                <X size={16} />
              </button>
            </div>
            <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
              To disable MFA, please confirm your current account password and a valid 6-digit TOTP code.
            </p>

            {disableError && (
              <div
                className="mb-4 rounded-xl border px-3 py-2.5 flex items-start gap-2 text-xs"
                style={{
                  borderColor: "rgba(244,63,94,0.3)",
                  backgroundColor: "var(--danger-bg)",
                  color: "var(--danger-text)",
                }}
              >
                <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                {disableError}
              </div>
            )}

            <form onSubmit={handleDisableMfa} className="space-y-3">
              <div>
                <AuthLabel htmlFor="disablePassword">Current Password</AuthLabel>
                <input
                  id="disablePassword"
                  type="password"
                  required
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <AuthLabel htmlFor="disableCode">6-Digit TOTP / Backup Code</AuthLabel>
                <input
                  id="disableCode"
                  type="text"
                  required
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value)}
                  placeholder="123456"
                  className="input"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-3 border-t" style={{ borderColor: "var(--border)" }}>
                <button type="button" onClick={() => setShowDisableModal(false)} className="btn btn-ghost">
                  Cancel
                </button>
                <button type="submit" disabled={isDisabling} className="btn btn-danger">
                  {isDisabling ? "Disabling…" : "Confirm & Disable"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default MfaEnrollmentPage;
