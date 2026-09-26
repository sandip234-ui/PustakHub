/**
 * App — Root component and router definition with authentication and theme providers.
 */

import { BrowserRouter, Route, Routes } from "react-router-dom";
import GuestRoute from "./components/GuestRoute";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { RealtimeProvider } from "./context/RealtimeContext";
import { ThemeProvider } from "./context/ThemeContext";
import MainLayout from "./layouts/MainLayout";
import AuditPage from "./pages/AuditPage";
import BookDetailsPage from "./pages/BookDetailsPage";
import BorrowingDetailsPage from "./pages/BorrowingDetailsPage";
import BorrowingsPage from "./pages/BorrowingsPage";
import CatalogPage from "./pages/CatalogPage";
import CategoriesPage from "./pages/CategoriesPage";
import DashboardPreviewPage from "./pages/DashboardPreviewPage";
import FinesPage from "./pages/FinesPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import MfaEnrollmentPage from "./pages/MfaEnrollmentPage";
import MfaRecoveryPage from "./pages/MfaRecoveryPage";
import MfaVerificationPage from "./pages/MfaVerificationPage";
import NotFoundPage from "./pages/NotFoundPage";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import UserDetailsPage from "./pages/UserDetailsPage";
import UsersPage from "./pages/UsersPage";
import VerifyOtpPage from "./pages/VerifyOtpPage";

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <RealtimeProvider>
          <BrowserRouter>
            <Routes>
            <Route element={<MainLayout />}>
              {/* Public Landing & Catalog */}
              <Route path="/" element={<HomePage />} />
              <Route path="/catalog" element={<CatalogPage />} />
              <Route path="/books/:id" element={<BookDetailsPage />} />

              {/* Guest-only routes */}
              <Route element={<GuestRoute />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/verify-otp" element={<VerifyOtpPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/mfa-verify" element={<MfaVerificationPage />} />
                <Route path="/mfa-recovery" element={<MfaRecoveryPage />} />
              </Route>

              {/* Authenticated user routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<DashboardPreviewPage />} />
                <Route path="/borrowings" element={<BorrowingsPage />} />
                <Route path="/borrowings/:id" element={<BorrowingDetailsPage />} />
                <Route path="/fines" element={<FinesPage />} />
                <Route path="/mfa-enroll" element={<MfaEnrollmentPage />} />
                <Route path="/security/mfa" element={<MfaEnrollmentPage />} />
              </Route>

              {/* Staff-only management routes (ADMIN & LIBRARIAN) */}
              <Route element={<ProtectedRoute allowedRoles={["ADMIN", "LIBRARIAN"]} />}>
                <Route path="/categories" element={<CategoriesPage />} />
                <Route path="/audit" element={<AuditPage />} />
              </Route>

              {/* Administrator-only IAM management routes */}
              <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
                <Route path="/users" element={<UsersPage />} />
                <Route path="/users/:id" element={<UserDetailsPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<NotFoundPage />} />
            </Route>
            </Routes>
          </BrowserRouter>
        </RealtimeProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;