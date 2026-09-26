/**
 * Authentication Context.
 *
 * Manages global authentication state, token storage, and session lifecycle.
 */

import { createContext, useCallback, useEffect, useState } from "react";
import authService from "../services/auth.service";

/* eslint-disable react-refresh/only-export-components */
export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("pustakhub_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [accessToken, setAccessToken] = useState(() =>
    localStorage.getItem("pustakhub_access_token")
  );
  const [refreshToken, setRefreshToken] = useState(() =>
    localStorage.getItem("pustakhub_refresh_token")
  );
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem("pustakhub_access_token");
    localStorage.removeItem("pustakhub_refresh_token");
    localStorage.removeItem("pustakhub_user");
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  }, []);

  // Sync profile on mount if token exists
  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      const token = localStorage.getItem("pustakhub_access_token");
      if (!token) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const profile = await authService.getCurrentUser();
        if (isMounted) {
          setUser(profile);
          localStorage.setItem("pustakhub_user", JSON.stringify(profile));
        }
      } catch {
        // Interceptor handles refresh; if failed completely, session is cleared
        if (isMounted && !localStorage.getItem("pustakhub_access_token")) {
          clearSession();
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadUser();

    const handleAutoLogout = () => {
      clearSession();
    };

    window.addEventListener("auth:logout", handleAutoLogout);
    return () => {
      isMounted = false;
      window.removeEventListener("auth:logout", handleAutoLogout);
    };
  }, [clearSession]);

  const login = async (credentials) => {
    const data = await authService.login(credentials);
    const { access_token, refresh_token: ref_token, user: userData } = data;

    localStorage.setItem("pustakhub_access_token", access_token);
    localStorage.setItem("pustakhub_refresh_token", ref_token);
    localStorage.setItem("pustakhub_user", JSON.stringify(userData));

    setAccessToken(access_token);
    setRefreshToken(ref_token);
    setUser(userData);

    return data;
  };

  const completeMfaLogin = (data) => {
    const { access_token, refresh_token: ref_token, user: userData } = data;

    localStorage.setItem("pustakhub_access_token", access_token);
    localStorage.setItem("pustakhub_refresh_token", ref_token);
    localStorage.setItem("pustakhub_user", JSON.stringify(userData));

    setAccessToken(access_token);
    setRefreshToken(ref_token);
    setUser(userData);

    return data;
  };

  const register = async (userData) => {
    return await authService.register(userData);
  };

  const verifyOtp = async (otpData) => {
    return await authService.verifyOtp(otpData);
  };

  const logout = async () => {
    try {
      const refToken = localStorage.getItem("pustakhub_refresh_token");
      if (refToken) {
        await authService.logout(refToken);
      }
    } catch {
      // Ignore network errors during logout
    } finally {
      clearSession();
    }
  };

  const refreshUser = async () => {
    try {
      const profile = await authService.getCurrentUser();
      setUser(profile);
      localStorage.setItem("pustakhub_user", JSON.stringify(profile));
      return profile;
    } catch {
      return null;
    }
  };

  const value = {
    user,
    accessToken,
    refreshToken,
    isAuthenticated: Boolean(user && accessToken),
    isLoading,
    login,
    completeMfaLogin,
    refreshUser,
    register,
    verifyOtp,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
