/**
 * API client for Mini App backend
 */

const API = {
    // API Gateway URL
    baseUrl: 'https://wrp9wc6j8i.execute-api.eu-central-1.amazonaws.com/prod/api',

    /** Make authenticated API request */
    async request(endpoint, options = {}) {
        const initData = TelegramApp.getInitData();

        if (!initData) {
            throw new Error('No init data available');
        }

        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-Telegram-Init-Data': initData,
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }

        return await response.json();
    },

    /** GET /api/user - Get user data */
    async getUser() {
        return this.request('/user', { method: 'GET' });
    },

    /** PUT /api/user/settings - Update settings */
    async updateSettings(settings) {
        return this.request('/user/settings', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    },

    /** GET /api/payments - Get payment history */
    async getPayments() {
        return this.request('/payments', { method: 'GET' });
    },

    /** GET /api/reports - Get available reports */
    async getReports() {
        return this.request('/reports', { method: 'GET' });
    },

    /** GET /api/reports/{reportId} - Get report content */
    async getReportContent(reportId, instanceId = null) {
        const path = instanceId ? `/reports/${reportId}/${instanceId}` : `/reports/${reportId}`;
        return this.request(path, { method: 'GET' });
    },

    /** DELETE /api/reports/{reportId}/{instanceId} - Delete report instance */
    async deleteReportInstance(reportId, instanceId) {
        return this.request(`/reports/${reportId}/${instanceId}`, { method: 'DELETE' });
    },

    /** POST /api/invoice - Create invoice for purchase */
    async createInvoice(type) {
        return this.request('/invoice', {
            method: 'POST',
            body: JSON.stringify({ type })
        });
    },

    // Compatibility endpoints

    /** GET /api/compatibility - Get compatibility history */
    async getCompatibilityHistory() {
        return this.request('/compatibility', { method: 'GET' });
    },

    /** GET /api/compatibility/{id} - Get specific result */
    async getCompatibilityResult(resultId) {
        return this.request(`/compatibility/${resultId}`, { method: 'GET' });
    },

    /** POST /api/compatibility - Create new compatibility check */
    async createCompatibility(partnerDate) {
        return this.request('/compatibility', {
            method: 'POST',
            body: JSON.stringify({ partner_date: partnerDate })
        });
    },

    /** POST /api/compatibility/{id}/interpret - Get AI interpretation */
    async getCompatibilityInterpretation(resultId) {
        return this.request(`/compatibility/${resultId}/interpret`, { method: 'POST' });
    },

    /** DELETE /api/compatibility/{id} - Delete compatibility result */
    async deleteCompatibility(resultId) {
        return this.request(`/compatibility/${resultId}`, { method: 'DELETE' });
    },

    // Report generation

    /** POST /api/reports/{id}/generate - Generate report with context */
    async generateReport(reportId, context = {}) {
        return this.request(`/reports/${reportId}/generate`, {
            method: 'POST',
            body: JSON.stringify({ context })
        });
    },

    // Profile interpretation

    /** GET /api/user/interpretation - Get profile AI interpretation */
    async getProfileInterpretation() {
        return this.request('/user/interpretation', { method: 'GET' });
    }
};

// Export for use in other modules
window.API = API;
