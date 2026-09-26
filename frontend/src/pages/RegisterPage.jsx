/**
 * RegisterPage — Public student registration.
 *
 * Captures name, email, and password. Dispatches an OTP to the email
 * and directs the student to /verify-otp upon submission.
 */

import { AlertTriangle, BookOpen, Eye, EyeOff, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

function FormField({
  id,
  label,
  type = "text",
  name,
  value,
  onChange,
  placeholder,
  hint,
  autoComplete,
  showPasswordToggle = false,
  isPasswordVisible = false,
  onTogglePasswordVisibility,
}) {
  const inputType = showPasswordToggle
    ? isPasswordVisible
      ? "text"
      : "password"
    : type;

  return (
    <div>
      <label
        htmlFor={id}
        className="block text-xs font-semibold uppercase tracking-wider mb-1.5"
        style={{ color: "var(--text-muted)" }}
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={inputType}
          name={name}
          required
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="input"
          style={showPasswordToggle ? { paddingRight: "2.5rem" } : undefined}
        />
        {showPasswordToggle && (
          <button
            type="button"
            onClick={onTogglePasswordVisibility}
            className="absolute inset-y-0 right-0 flex items-center pr-3 transition cursor-pointer"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
            aria-label={isPasswordVisible ? "Hide password" : "Show password"}
            title={isPasswordVisible ? "Hide password" : "Show password"}
          >
            {isPasswordVisible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {hint && (
        <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
          {hint}
        </p>
      )}
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });

      navigate(`/verify-otp?email=${encodeURIComponent(formData.email.trim().toLowerCase())}`);
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
          setError(err.response?.data?.message || "Registration failed. Please check your inputs.");
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
            <BookOpen size={26} style={{ color: "var(--primary)" }} />
          </div>
          <h1
            className="text-2xl font-black tracking-tight sm:text-3xl"
            style={{ color: "var(--text-primary)" }}
          >
            Create Student Account
          </h1>
          <p className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>
            Register to borrow books and access library resources
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
            <FormField
              id="name"
              label="Full Name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Jane Doe"
              autoComplete="name"
            />
            <FormField
              id="email"
              label="Email Address"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="student@example.com"
              autoComplete="email"
            />
            <FormField
              id="password"
              label="Password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              hint="Min 8 chars, uppercase, lowercase, number & special symbol."
              autoComplete="new-password"
              showPasswordToggle
              isPasswordVisible={showPassword}
              onTogglePasswordVisibility={() => setShowPassword((prev) => !prev)}
            />
            <FormField
              id="confirmPassword"
              label="Confirm Password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="••••••••"
              autoComplete="new-password"
              showPasswordToggle
              isPasswordVisible={showConfirmPassword}
              onTogglePasswordVisibility={() => setShowConfirmPassword((prev) => !prev)}
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary w-full mt-2"
              style={{ padding: "11px 22px" }}
            >
              <UserPlus size={14} />
              {isSubmitting ? "Sending Verification Code…" : "Register & Send OTP"}
            </button>
          </form>

          <div
            className="mt-6 text-center text-sm border-t pt-5"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold transition"
              style={{ color: "var(--primary)" }}
            >
              Log in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
