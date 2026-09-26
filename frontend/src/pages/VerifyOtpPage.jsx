/**
 * VerifyOtpPage — 6-Digit Email Verification.
 * Verifies the temporary registration OTP and provisions the PostgreSQL User.
 */

import { CheckCircle, Mail } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthCard, AuthError, AuthLabel } from "../components/AuthCard";
import useAuth from "../hooks/useAuth";

export function VerifyOtpPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { verifyOtp } = useAuth();

  const [email, setEmail] = useState(() => searchParams.get("email") || "");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const cleanedOtp = otp.trim();
    if (!/^\d{6}$/.test(cleanedOtp)) {
      setError("Please enter a valid 6-digit numeric verification code.");
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await verifyOtp({
        email: email.trim().toLowerCase(),
        otp: cleanedOtp,
      });

      setSuccess(res.message || "Account verified successfully! Redirecting to login…");
      setTimeout(() => {
        navigate("/login", {
          state: { verifiedEmail: email.trim().toLowerCase() },
        });
      }, 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(", "));
      } else {
        setError(err.response?.data?.message || "Verification failed. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthCard
      icon={Mail}
      title="Verify Your Email"
      subtitle={
        <>
          Enter the 6-digit code sent to{" "}
          <span className="font-semibold" style={{ color: "var(--primary)" }}>
            {email || "your email address"}
          </span>
        </>
      }
    >
      <AuthError message={error} />

      {success && (
        <div
          className="mb-5 rounded-xl border px-4 py-3 flex items-start gap-2.5 text-sm"
          style={{
            borderColor: "rgba(16,185,129,0.3)",
            backgroundColor: "var(--success-bg)",
            color: "var(--success-text)",
          }}
          role="status"
        >
          <CheckCircle size={15} className="mt-0.5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <AuthLabel htmlFor="email">Email Address</AuthLabel>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@example.com"
            className="input"
          />
        </div>

        <div>
          <AuthLabel htmlFor="otp">6-Digit Verification Code</AuthLabel>
          <input
            id="otp"
            type="text"
            required
            maxLength={6}
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            placeholder="123456"
            className="input mono text-center text-2xl tracking-widest"
            style={{ color: "var(--primary)" }}
          />
          <p className="mt-1.5 text-xs text-center" style={{ color: "var(--text-muted)" }}>
            The code expires in 5 minutes.
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || otp.length !== 6}
          className="btn btn-primary w-full mt-2"
          style={{ padding: "11px 22px" }}
        >
          {isSubmitting ? "Verifying…" : "Verify & Activate Account"}
        </button>
      </form>

      <div
        className="mt-5 flex items-center justify-between text-xs border-t pt-4"
        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
      >
        <Link
          to="/register"
          className="transition"
          style={{ color: "var(--text-secondary)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
        >
          ← Back to Registration
        </Link>
        <Link
          to="/login"
          className="font-semibold transition"
          style={{ color: "var(--primary)" }}
        >
          Already verified? Log in
        </Link>
      </div>
    </AuthCard>
  );
}

export default VerifyOtpPage;
