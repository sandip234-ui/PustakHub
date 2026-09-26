/**
 * MfaRecoveryPage — Login using single-use backup recovery codes.
 * Fully theme-aware with AuthCard wrapper.
 */

import { KeyRound, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AuthCard, AuthError, AuthLabel } from "../components/AuthCard";
import useAuth from "../hooks/useAuth";
import authService from "../services/auth.service";

export function MfaRecoveryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { completeMfaLogin } = useAuth();

  const mfaToken = location.state?.mfa_token;
  const from = location.state?.from || "/dashboard";

  const [recoveryCode, setRecoveryCode] = useState("");
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!mfaToken) {
    return (
      <div
        className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center"
        style={{ backgroundColor: "var(--bg)" }}
      >
        <p className="mb-5 text-sm" style={{ color: "var(--text-secondary)" }}>
          No active MFA challenge session found.
        </p>
        <Link to="/login" className="btn btn-primary">
          Return to Login
        </Link>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const data = await authService.verifyMfaLogin({
        mfa_token: mfaToken,
        code: recoveryCode.trim(),
        is_recovery_code: true,
      });

      completeMfaLogin(data);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Invalid or consumed recovery code."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthCard
      icon={ShieldAlert}
      title="Account Recovery"
      subtitle="Log in using one of your single-use backup recovery codes"
    >
      <AuthError message={error} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <AuthLabel htmlFor="recoveryCode">Recovery Code</AuthLabel>
          <input
            id="recoveryCode"
            type="text"
            required
            value={recoveryCode}
            onChange={(e) => setRecoveryCode(e.target.value)}
            placeholder="ABCD-1234-EFGH"
            className="input mono text-center text-lg tracking-widest uppercase"
          />
        </div>

        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Note: This recovery code will be permanently consumed upon successful verification.
        </p>

        <button
          type="submit"
          disabled={isSubmitting || !recoveryCode.trim()}
          className="btn btn-primary w-full mt-2"
          style={{ padding: "11px 22px" }}
        >
          <KeyRound size={14} />
          {isSubmitting ? "Verifying Code…" : "Verify & Recover Access"}
        </button>
      </form>

      <div
        className="mt-6 pt-5 border-t text-center text-sm"
        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
      >
        Have your authenticator app?{" "}
        <Link
          to="/mfa-verify"
          state={{ mfa_token: mfaToken, from }}
          className="font-semibold transition"
          style={{ color: "var(--primary)" }}
        >
          Use standard TOTP code
        </Link>
      </div>
    </AuthCard>
  );
}

export default MfaRecoveryPage;
