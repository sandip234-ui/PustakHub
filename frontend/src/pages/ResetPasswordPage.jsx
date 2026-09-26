/**
 * ResetPasswordPage — Reset password with single-use token from email link.
 *
 * Implements:
 * - URL token extraction via query param (?token=...)
 * - Missing/invalid token fallback with route to /forgot-password
 * - Independent password visibility toggles (Eye/EyeOff)
 * - Password strength validation matching backend policy
 * - Single-use token consumption via authService.resetPassword
 * - Success state with navigation to /login
 * - Network-error distinction from server errors
 */

import { ArrowLeft, CheckCircle, Eye, EyeOff, KeyRound, Lock, RefreshCw, XCircle } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthCard, AuthError, AuthLabel } from "../components/AuthCard";
import authService from "../services/auth.service";

function validatePasswordPolicy(password) {
  if (password.length < 8) {
    return "Password must be at least 8 characters long.";
  }
  if (password.length > 128) {
    return "Password must be at most 128 characters long.";
  }
  if (!/[A-Z]/.test(password)) {
    return "Password must contain at least one uppercase letter.";
  }
  if (!/[a-z]/.test(password)) {
    return "Password must contain at least one lowercase letter.";
  }
  if (!/\d/.test(password)) {
    return "Password must contain at least one digit.";
  }
  if (!/[!@#$%^&*(),.?":{}|<>\-_=+[\]\\/~`]/.test(password)) {
    return "Password must contain at least one special character.";
  }
  return null;
}

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get("token") || "";

  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });

  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!token.trim()) {
      setError("Invalid or missing reset token.");
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const policyError = validatePasswordPolicy(formData.newPassword);
    if (policyError) {
      setError(policyError);
      return;
    }

    setIsSubmitting(true);

    try {
      await authService.resetPassword({
        token: token.trim(),
        new_password: formData.newPassword,
      });
      setSuccess(true);
    } catch (err) {
      if (!err.response) {
        setError("Unable to reach the server. Please check your network connection.");
      } else {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (Array.isArray(detail)) {
          setError(detail.map((d) => d.msg).join(", "));
        } else {
          setError(err.response?.data?.message || "Failed to reset password. The link may have expired or already been used.");
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthCard
      icon={Lock}
      title="Set New Password"
      subtitle={token ? "Enter your new password below" : "Invalid Password Reset Link"}
    >
      <AuthError message={error} />

      {!token ? (
        <div className="space-y-5 text-center">
          <div
            className="rounded-xl border px-4 py-5"
            style={{
              borderColor: "rgba(244,63,94,0.3)",
              backgroundColor: "var(--danger-bg)",
            }}
          >
            <div className="flex justify-center mb-3">
              <XCircle size={32} style={{ color: "var(--danger-text)" }} />
            </div>
            <p className="font-semibold text-base" style={{ color: "var(--danger-text)" }}>
              Invalid or missing reset token.
            </p>
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              The password reset link you clicked is missing a valid security token or may have been corrupted.
            </p>
          </div>

          <Link to="/forgot-password" className="btn btn-primary w-full justify-center">
            Request a New Reset Link
          </Link>

          <div
            className="mt-4 flex items-center justify-center gap-1.5 text-sm"
            style={{ color: "var(--text-secondary)" }}
          >
            <ArrowLeft size={13} />
            <Link to="/login" className="font-semibold" style={{ color: "var(--primary)" }}>
              Back to Log In
            </Link>
          </div>
        </div>
      ) : success ? (
        <div className="space-y-5 text-center">
          <div
            className="rounded-xl border px-4 py-5"
            style={{
              borderColor: "rgba(16,185,129,0.3)",
              backgroundColor: "var(--success-bg)",
            }}
          >
            <div className="flex justify-center mb-3">
              <CheckCircle size={32} style={{ color: "var(--success-text)" }} />
            </div>
            <p className="font-semibold text-base" style={{ color: "var(--success-text)" }}>
              Password reset successful.
            </p>
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              Your password has been updated and prior active sessions have been revoked for your security.
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate("/login")}
            className="btn btn-primary w-full justify-center"
          >
            Continue to Login
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* New Password */}
          <div>
            <AuthLabel htmlFor="newPassword">New Password</AuthLabel>
            <div className="relative">
              <input
                id="newPassword"
                type={showNewPassword ? "text" : "password"}
                name="newPassword"
                required
                autoComplete="new-password"
                value={formData.newPassword}
                onChange={handleChange}
                placeholder="Enter new password (min. 8 chars)"
                className="input"
                style={{ paddingRight: "2.5rem" }}
              />
              <button
                type="button"
                onClick={() => setShowNewPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 transition cursor-pointer"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                aria-label={showNewPassword ? "Hide password" : "Show password"}
                title={showNewPassword ? "Hide password" : "Show password"}
              >
                {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Must contain min. 8 chars, uppercase, lowercase, digit, and symbol.
            </p>
          </div>

          {/* Confirm New Password */}
          <div>
            <AuthLabel htmlFor="confirmPassword">Confirm New Password</AuthLabel>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                name="confirmPassword"
                required
                autoComplete="new-password"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Repeat new password"
                className="input"
                style={{ paddingRight: "2.5rem" }}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 transition cursor-pointer"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                title={showConfirmPassword ? "Hide password" : "Show password"}
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary w-full mt-2 justify-center"
            style={{ padding: "11px 22px" }}
          >
            {isSubmitting ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Resetting Password...</span>
              </>
            ) : (
              <>
                <KeyRound size={14} />
                <span>Reset Password</span>
              </>
            )}
          </button>

          <div
            className="mt-4 flex items-center justify-center gap-1.5 text-sm"
            style={{ color: "var(--text-secondary)" }}
          >
            <ArrowLeft size={13} />
            <Link to="/login" className="font-semibold" style={{ color: "var(--primary)" }}>
              Back to Log In
            </Link>
          </div>
        </form>
      )}
    </AuthCard>
  );
}

export default ResetPasswordPage;
