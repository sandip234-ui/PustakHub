/**
 * Health service — backend connectivity check.
 *
 * Provides a single function to query the /health endpoint.
 * Components should import from this file rather than calling
 * `api.get('/health')` directly.
 */

import api from "./api";

/**
 * Fetch the backend health status.
 * @returns {Promise<object>} Health payload from the backend.
 */
export const fetchHealth = () => api.get("/health").then((res) => res.data);
