/**
 * User & IAM Administration API Service.
 *
 * Provides functions for user management, role assignments, status updates,
 * and effective permission inspection.
 */

import api from "./api";

export const userService = {
  // --- User Queries ---
  async getUsers(params = {}) {
    const response = await api.get("/v1/users", { params });
    return response.data;
  },

  async getUserById(userId) {
    const response = await api.get(`/v1/users/${userId}`);
    return response.data;
  },

  async updateUserStatus(userId, status) {
    const response = await api.patch(`/v1/users/${userId}/status`, {
      account_status: status,
    });
    return response.data;
  },

  async getUserPermissions(userId) {
    const response = await api.get(`/v1/users/${userId}/permissions`);
    return response.data;
  },

  // --- Role Assignments ---
  async assignRole(userId, roleName) {
    const response = await api.post(`/v1/users/${userId}/roles`, {
      role_name: roleName,
    });
    return response.data;
  },

  async revokeRole(userId, roleName) {
    const response = await api.delete(`/v1/users/${userId}/roles/${roleName}`);
    return response.data;
  },

  async getRoles(params = {}) {
    const response = await api.get("/v1/roles", { params });
    return response.data;
  },

  // --- Permissions & Matrix ---
  async getPermissions() {
    const response = await api.get("/v1/permissions");
    return response.data;
  },

  async getPermissionMatrix() {
    const response = await api.get("/v1/permissions/matrix");
    return response.data;
  },
};

export default userService;
