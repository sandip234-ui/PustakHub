/**
 * Circulation, Borrowing & Fines API Service.
 *
 * Provides API client functions for:
 *   - Issuing copies: issueBook
 *   - Returning copies: returnBook
 *   - Borrowing transactions: getBorrowings, getBorrowingById, getUserBorrowings
 *   - Fines: getFines, getFineById, getUserFines
 *   - Users: getUsers (for staff member lookup during loan issuance)
 */

import api from "./api";

export const circulationService = {
  // --- Issue & Return ---
  async issueBook(data) {
    const response = await api.post("/v1/borrow", data);
    return response.data;
  },

  async returnBook(borrowId, data = {}) {
    const response = await api.post(`/v1/borrow/${borrowId}/return`, data);
    return response.data;
  },

  // --- Borrowing History ---
  async getBorrowings(params = {}) {
    const response = await api.get("/v1/borrowings", { params });
    return response.data;
  },

  async getBorrowingById(borrowId) {
    const response = await api.get(`/v1/borrowings/${borrowId}`);
    return response.data;
  },

  async getUserBorrowings(userId, params = {}) {
    const response = await api.get(`/v1/users/${userId}/borrowings`, { params });
    return response.data;
  },

  // --- Fines ---
  async getFines(params = {}) {
    const response = await api.get("/v1/fines", { params });
    return response.data;
  },

  async getFineById(fineId) {
    const response = await api.get(`/v1/fines/${fineId}`);
    return response.data;
  },

  async getUserFines(userId, params = {}) {
    const response = await api.get(`/v1/users/${userId}/fines`, { params });
    return response.data;
  },

  // --- Users Lookup (Staff only) ---
  async getUsers(params = {}) {
    const response = await api.get("/v1/users", { params });
    return response.data;
  },
};

export default circulationService;
