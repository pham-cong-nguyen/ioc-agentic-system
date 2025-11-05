/**
 * API Service - Handle all API communications
 * Centralized API client with error handling and token management
 */

export class ApiService {
    constructor() {
        this.baseURL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8862/api/v1'
            : '/api/v1';
        this.token = localStorage.getItem('access_token');
    }

    // =====================================================
    // Core Request Methods
    // =====================================================

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            }
        };

        // Add auth token if available
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            // Handle different response types
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || error.message || `HTTP ${response.status}`);
            }

            // For DELETE with 204 No Content, return success object
            if (response.status === 204) {
                return { success: true };
            }

            // Return json if content-type is json
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            // Default return for successful requests
            return { success: true };
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = query ? `${endpoint}?${query}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // =====================================================
    // Authentication
    // =====================================================

    async login(username, password) {
        const response = await this.post('/auth/login', { username, password });
        this.token = response.access_token;
        localStorage.setItem('access_token', response.access_token);
        return response;
    }

    async logout() {
        try {
            await this.post('/auth/logout', {});
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.token = null;
            localStorage.removeItem('access_token');
        }
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // =====================================================
    // Query Processing (Orchestrator)
    // =====================================================

    async processQuery(query, language = 'vi', conversationId = null) {
        return this.post('/query', {
            query,
            language,
            conversation_id: conversationId
        });
    }

    async processQueryV2(query, language = 'vi', conversationId = null) {
        return this.post('/agent/v2/query', {
            query,
            language,
            conversation_id: conversationId
        });
    }

    async getQueryHistory(limit = 10, offset = 0) {
        return this.get('/query/history', { limit, offset });
    }

    async getQueryResult(queryId) {
        return this.get(`/query/${queryId}`);
    }

    async submitFeedback(queryId, rating, feedback = null) {
        return this.post('/query/feedback', {
            query_id: queryId,
            rating,
            feedback
        });
    }

    async getExampleQueries() {
        return this.get('/query/examples');
    }

    // =====================================================
    // Function Registry
    // =====================================================

    async getFunctions(params = {}) {
        return this.get('/registry/functions', params);
    }

    async searchFunctions(query, domain = null, limit = 50) {
        return this.get('/registry/functions/search', { 
            query, 
            domain,
            limit 
        });
    }

    async getFunction(functionId) {
        return this.get(`/registry/functions/${functionId}`);
    }

    async createFunction(functionData) {
        return this.post('/registry/functions', functionData);
    }

    async updateFunction(functionId, functionData) {
        return this.put(`/registry/functions/${functionId}`, functionData);
    }

    async deleteFunction(functionId) {
        return this.delete(`/registry/functions/${functionId}`);
    }

    async bulkImportFunctions(functions) {
        return this.post('/registry/functions/bulk', { functions });
    }

    async exportFunctions() {
        return this.get('/registry/functions/export');
    }

    async getRegistryStatistics() {
        return this.get('/registry/statistics');
    }

    // =====================================================
    // System
    // =====================================================

    async getHealth() {
        return this.get('/health', {}, false);
    }

    async getSystemStatus() {
        return this.get('/status');
    }
}
