/**
 * LoginPage — User authentication.
 *
 * Authenticates with email and password, establishing access and refresh tokens.
 */

import { AlertTriangle, CheckCircle, Eye, EyeOff, Lock, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: location.state?.verifiedEmail || "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = location.state?.from?.pathname || "/dashboard";

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await login({
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      });

      if (res?.mfa_required) {
        navigate("/mfa-verify", {
          state: { mfa_token: res.mfa_token, from },
          replace: true,
        });
      } else {
        navigate(from, { replace: true });
      }
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
          setError(err.response?.data?.message || "Invalid email or password.");
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="relative flex min-h-[calc(100vh-56px)] items-center justify-center px-4 py-12"
      style={{ backgroundColor: "var(--bg)" }}
    >
      {/* Grid background */}
      <div className="hero-grid pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="radial-glow pointer-events-none absolute inset-0" aria-hidden="true" />

      <div className="relative z-10 w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <div
            className="inline-flex h-14 w-14 items-center justify-center rounded-2xl border mb-4 shadow-lg"
            style={{
              backgroundColor: "var(--primary-soft)",
              borderColor: "rgba(99,102,241,0.25)",
              boxShadow: "0 8px 24px var(--primary-glow)",
            }}
          >
            <ShieldCheck size={26} style={{ color: "var(--primary)" }} />
          </div>
          <h1
            className="text-2xl font-black tracking-tight sm:text-3xl"
            style={{ color: "var(--text-primary)" }}
          >
            Welcome Back
          </h1>
          <p className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>
            Sign in to your PustakHub library account
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl border p-6 sm:p-8"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderColor: "var(--border)",
            boxShadow: "var(--shadow-lg)",
          }}
        >
          {location.state?.verifiedEmail && !error && (
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
              <span>Email verified successfully! Please sign in with your credentials.</span>
            </div>
          )}

          {error && (
            <div
              className="mb-5 rounded-xl border px-4 py-3 flex items-start gap-2.5 text-sm"
              style={{
                borderColor: "rgba(244,63,94,0.3)",
                backgroundColor: "var(--danger-bg)",
                color: "var(--danger-text)",
              }}
              role="alert"
            >
              <AlertTriangle size={15} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold uppercase tracking-wider mb-1.5"
                style={{ color: "var(--text-muted)" }}
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                name="email"
                required
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="student@example.com"
                className="input"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold transition"
                  style={{ color: "var(--primary)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--primary-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--primary)")}
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  required
                  autoComplete="current-password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="input"
                  style={{ paddingRight: "2.5rem" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 transition cursor-pointer"
                  style={{ color: "var(--text-muted)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary w-full mt-2"
              style={{ padding: "11px 22px" }}
            >
              <Lock size={14} />
              {isSubmitting ? "Signing in…" : "Log In"}
            </button>
          </form>

          <div
            className="mt-6 text-center text-sm border-t pt-5"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            Don&apos;t have an account?{" "}
            <Link
              to="/register"
              className="font-semibold transition"
              style={{ color: "var(--primary)" }}
            >
              Register as student
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
