/**
 * ForgotPasswordPage — Request password reset link.
 * Implements anti-account-enumeration generic feedback.
 */

import { ArrowLeft, KeyRound, Mail, Send } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthCard, AuthError } from "../components/AuthCard";
import { AuthLabel } from "../components/AuthCard";
import authService from "../services/auth.service";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await authService.forgotPassword({
        email: email.trim().toLowerCase(),
      });
      setMessage(
        res.message ||
          "If an account exists for this email, password reset instructions have been sent."
      );
      setSubmitted(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "An error occurred while requesting password reset. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthCard
      icon={KeyRound}
      title="Reset Password"
      subtitle="Enter your email to receive a secure password reset link"
    >
      <AuthError message={error} />

      {submitted ? (
        <div className="space-y-5 text-center">
          <div
            className="rounded-xl border px-4 py-5"
            style={{
              borderColor: "rgba(16,185,129,0.3)",
              backgroundColor: "var(--success-bg)",
            }}
          >
            <div className="flex justify-center mb-3">
              <Mail size={28} style={{ color: "var(--success-text)" }} />
            </div>
            <p
              className="text-sm font-semibold"
              style={{ color: "var(--success-text)" }}
            >
              {message}
            </p>
            <p
              className="mt-2 text-xs"
              style={{ color: "var(--text-muted)" }}
            >
              Please check your inbox or spam folder. The reset link is valid for 15 minutes.
            </p>
          </div>

          <Link to="/login" className="btn btn-primary w-full justify-center">
            Return to Log In
          </Link>
        </div>
      ) : (
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

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary w-full mt-2"
            style={{ padding: "11px 22px" }}
          >
            <Send size={14} />
            {isSubmitting ? "Sending Link…" : "Send Reset Link"}
          </button>

          <div
            className="mt-4 flex items-center justify-center gap-1.5 text-sm"
            style={{ color: "var(--text-secondary)" }}
          >
            <ArrowLeft size={13} />
            <Link
              to="/login"
              className="font-semibold"
              style={{ color: "var(--primary)" }}
            >
              Back to Log In
            </Link>
          </div>
        </form>
      )}
    </AuthCard>
  );
}

export default ForgotPasswordPage;
