/**
 * Audit API Service.
 *
 * Provides client methods for querying, filtering, and inspecting system audit logs.
 */

import api from "./api";

export const auditService = {
  /**
   * Query paginated audit log records with optional filtering.
   */
  async getAuditLogs(params = {}) {
    const response = await api.get("/v1/audit/logs", { params });
    return response.data;
  },

  /**
   * Retrieve a single audit log entry by UUID.
   */
  async getAuditLogById(auditId) {
    const response = await api.get(`/v1/audit/logs/${auditId}`);
    return response.data;
  },

  /**
   * Retrieve canonical list of audit action types and categories.
   */
  async getAuditActions() {
    const response = await api.get("/v1/audit/actions");
    return response.data;
  },
};

export default auditService;
