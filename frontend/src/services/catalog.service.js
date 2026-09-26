/**
 * Catalog API Service.
 *
 * Provides functions for Categories, Books, and Physical Copies API endpoints.
 */

import api from "./api";

export const catalogService = {
  // --- Category APIs ---
  async getCategories(params = {}) {
    const response = await api.get("/v1/categories", { params });
    return response.data;
  },

  async getCategoryById(categoryId) {
    const response = await api.get(`/v1/categories/${categoryId}`);
    return response.data;
  },

  async createCategory(data) {
    const response = await api.post("/v1/categories", data);
    return response.data;
  },

  async updateCategory(categoryId, data) {
    const response = await api.put(`/v1/categories/${categoryId}`, data);
    return response.data;
  },

  async deleteCategory(categoryId) {
    const response = await api.delete(`/v1/categories/${categoryId}`);
    return response.data;
  },

  // --- Book APIs ---
  async getBooks(params = {}) {
    const response = await api.get("/v1/books", { params });
    return response.data;
  },

  async getBookById(bookId) {
    const response = await api.get(`/v1/books/${bookId}`);
    return response.data;
  },

  async createBook(data) {
    const response = await api.post("/v1/books", data);
    return response.data;
  },

  async updateBook(bookId, data) {
    const response = await api.put(`/v1/books/${bookId}`, data);
    return response.data;
  },

  async deleteBook(bookId) {
    const response = await api.delete(`/v1/books/${bookId}`);
    return response.data;
  },

  // --- Book Copy APIs ---
  async getBookCopies(bookId, params = {}) {
    const response = await api.get(`/v1/books/${bookId}/copies`, { params });
    return response.data;
  },

  async createBookCopy(bookId, data) {
    const response = await api.post(`/v1/books/${bookId}/copies`, data);
    return response.data;
  },

  async getCopyById(copyId) {
    const response = await api.get(`/v1/copies/${copyId}`);
    return response.data;
  },

  async updateCopy(copyId, data) {
    const response = await api.put(`/v1/copies/${copyId}`, data);
    return response.data;
  },

  async deleteCopy(copyId) {
    const response = await api.delete(`/v1/copies/${copyId}`);
    return response.data;
  },
};

export default catalogService;
