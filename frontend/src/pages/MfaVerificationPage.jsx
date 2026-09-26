/**
 * MfaVerificationPage — MFA Login Challenge Step.
 * User provides 6-digit TOTP code against the intermediate mfa_token.
 */

import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AuthCard, AuthError, AuthLabel } from "../components/AuthCard";
import useAuth from "../hooks/useAuth";
import authService from "../services/auth.service";

export function MfaVerificationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { completeMfaLogin } = useAuth();

  const mfaToken = location.state?.mfa_token;
  const from = location.state?.from || "/dashboard";

  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If no mfa_token in state, redirect to login
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
        code: code.trim(),
        is_recovery_code: false,
      });

      completeMfaLogin(data);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Invalid two-factor code. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthCard
      icon={ShieldCheck}
      title="Two-Factor Verification"
      subtitle="Enter the 6-digit authentication code from your app"
    >
      <AuthError message={error} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <AuthLabel htmlFor="code">Authenticator Code</AuthLabel>
          <input
            id="code"
            type="text"
            required
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            className="input mono text-center text-2xl tracking-widest"
            style={{ color: "var(--primary)" }}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || code.length < 6}
          className="btn btn-primary w-full mt-2"
          style={{ padding: "11px 22px" }}
        >
          {isSubmitting ? "Verifying…" : "Verify & Log In"}
        </button>
      </form>

      <div
        className="mt-6 pt-5 border-t text-center text-sm"
        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
      >
        Lost access to your authenticator?{" "}
        <Link
          to="/mfa-recovery"
          state={{ mfa_token: mfaToken, from }}
          className="font-semibold transition"
          style={{ color: "var(--primary)" }}
        >
          Use a recovery code
        </Link>
      </div>
    </AuthCard>
  );
}

export default MfaVerificationPage;
