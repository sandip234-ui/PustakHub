/**
 * Centralised API client for PustakHub.
 *
 * Configures Axios with:
 *   - Base API URL
 *   - Request interceptor attaching Bearer access token
 *   - Response interceptor handling 401s and token refresh with queueing
 */

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10_000,
});

// Variable to track in-flight refresh requests to avoid multiple concurrent refreshes
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Attach JWT Bearer Access Token
api.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("pustakhub_access_token");
    if (accessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 and Refresh Token Rotation
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 429 Too Many Requests: Do NOT treat as authentication failure or trigger refresh loop
    if (error.response?.status === 429) {
      return Promise.reject(error);
    }

    // Skip refresh for auth endpoints themselves to avoid infinite loops
    const isAuthEndpoint =
      originalRequest?.url?.includes("/auth/login") ||
      originalRequest?.url?.includes("/auth/register") ||
      originalRequest?.url?.includes("/auth/verify-otp") ||
      originalRequest?.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("pustakhub_refresh_token");
      if (!refreshToken) {
        isRefreshing = false;
        localStorage.removeItem("pustakhub_access_token");
        localStorage.removeItem("pustakhub_refresh_token");
        localStorage.removeItem("pustakhub_user");
        window.dispatchEvent(new Event("auth:logout"));
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(
          `${api.defaults.baseURL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { "Content-Type": "application/json" } }
        );

        const { access_token, refresh_token: new_refresh_token, user } = response.data;

        localStorage.setItem("pustakhub_access_token", access_token);
        if (new_refresh_token) {
          localStorage.setItem("pustakhub_refresh_token", new_refresh_token);
        }
        if (user) {
          localStorage.setItem("pustakhub_user", JSON.stringify(user));
        }

        api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
        originalRequest.headers.Authorization = `Bearer ${access_token}`;

        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("pustakhub_access_token");
        localStorage.removeItem("pustakhub_refresh_token");
        localStorage.removeItem("pustakhub_user");
        window.dispatchEvent(new Event("auth:logout"));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;