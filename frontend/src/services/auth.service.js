/**
 * Authentication API service.
 *
 * Encapsulates all backend auth endpoint calls for registration, OTP verification,
 * login, token refresh, and logout.
 */

import api from "./api";

export const authService = {
  /**
   * Initiate student registration.
   * @param {{ name: string, email: string, password: string }} data
   * @returns {Promise<{ message: string, email: string }>}
   */
  async register(data) {
    const response = await api.post("/v1/auth/register", data);
    return response.data;
  },

  /**
   * Verify email OTP and complete account creation.
   * @param {{ email: string, otp: string }} data
   * @returns {Promise<{ message: string, email: string, user_id: string }>}
   */
  async verifyOtp(data) {
    const response = await api.post("/v1/auth/verify-otp", data);
    return response.data;
  },

  /**
   * Authenticate user credentials.
   * @param {{ email: string, password: string }} data
   * @returns {Promise<{ access_token: string, refresh_token: string, token_type: string, expires_in: number, user: object }>}
   */
  async login(data) {
    const response = await api.post("/v1/auth/login", data);
    return response.data;
  },

  /**
   * Rotate refresh token and obtain new access token.
   * @param {string} refreshToken
   * @returns {Promise<{ access_token: string, refresh_token: string, token_type: string, expires_in: number, user: object }>}
   */
  async refreshToken(refreshToken) {
    const response = await api.post("/v1/auth/refresh", { refresh_token: refreshToken });
    return response.data;
  },

  /**
   * Invalidate refresh token session on the server.
   * @param {string} [refreshToken]
   * @returns {Promise<{ message: string }>}
   */
  async logout(refreshToken) {
    const response = await api.post("/v1/auth/logout", { refresh_token: refreshToken || null });
    return response.data;
  },

  /**
   * Fetch current authenticated user profile.
   * @returns {Promise<object>}
   */
  async getCurrentUser() {
    const response = await api.get("/v1/auth/me");
    return response.data;
  },

  /**
   * Request password reset email.
   * @param {{ email: string }} data
   * @returns {Promise<{ message: string }>}
   */
  async forgotPassword(data) {
    const response = await api.post("/v1/auth/forgot-password", data);
    return response.data;
  },

  /**
   * Reset password using single-use reset token.
   * @param {{ token: string, new_password: string }} data
   * @returns {Promise<{ message: string }>}
   */
  async resetPassword(data) {
    const response = await api.post("/v1/auth/reset-password", data);
    return response.data;
  },

  /**
   * Initiate TOTP MFA enrollment (authenticated).
   * @returns {Promise<{ secret: string, otpauth_uri: string, recovery_codes: string[] }>}
   */
  async enrollMfa() {
    const response = await api.post("/v1/auth/mfa/enroll");
    return response.data;
  },

  /**
   * Verify TOTP code and enable MFA.
   * @param {{ totp_code: string }} data
   * @returns {Promise<{ message: string, is_mfa_enabled: boolean }>}
   */
  async verifyMfaEnrollment(data) {
    const payload =
      typeof data === "string"
        ? { code: data }
        : { code: data.code || data.totp_code };
    const response = await api.post("/v1/auth/mfa/verify-enrollment", payload);
    return response.data;
  },

  /**
   * Complete login challenge via TOTP or recovery code.
   * @param {{ mfa_token: string, code: string, is_recovery_code?: boolean }} data
   * @returns {Promise<{ access_token: string, refresh_token: string, token_type: string, expires_in: number, user: object }>}
   */
  async verifyMfaLogin(data) {
    const payload = {
      mfa_token: data.mfa_token,
      code: data.code,
    };
    const response = await api.post("/v1/auth/mfa/verify", payload);
    return response.data;
  },

  /**
   * Disable MFA factor after verifying password and valid TOTP code.
   * @param {{ password: string, code: string }} data
   * @returns {Promise<{ message: string, is_mfa_enabled: boolean }>}
   */
  async disableMfa(data) {
    const response = await api.post("/v1/auth/mfa/disable", data);
    return response.data;
  },

  /**
   * Safe MFA status inspection.
   * @returns {Promise<{ is_mfa_enabled: boolean }>}
   */
  async getMfaStatus() {
    const response = await api.get("/v1/auth/mfa/status");
    const enabled = Boolean(response.data?.enabled ?? response.data?.is_mfa_enabled);
    return { enabled, is_mfa_enabled: enabled };
  },
};

export default authService;

