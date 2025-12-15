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

    /** POST /api/invoice - Create invoice for purchase */
    async createInvoice(type) {
        return this.request('/invoice', {
            method: 'POST',
            body: JSON.stringify({ type })
        });
    }
};

// Export for use in other modules
window.API = API;
