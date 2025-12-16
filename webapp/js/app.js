/**
 * Main application logic for Mini App
 */

const App = {
    // Current language
    lang: 'ru',

    // User data from API
    userData: null,

    // Translations
    i18n: {},

    // Settings that have been modified
    pendingSettings: null,

    /** Initialize the app */
    async init() {
        // Initialize Telegram SDK
        if (!TelegramApp.init()) {
            console.error('Failed to initialize Telegram');
            return;
        }

        // Check for deep link to report page
        const startParam = TelegramApp.getStartParam();
        if (startParam && startParam.startsWith('report_')) {
            // Redirect to report page
            window.location.href = `report.html?id=${startParam.replace('report_', '')}`;
            return;
        }

        // Load translations
        await this.loadTranslations();

        // Setup event listeners
        this.setupEventListeners();

        // Load user data
        await this.loadUserData();

        // Hide loading
        document.getElementById('loading').classList.add('hidden');
    },

    /** Load translations */
    async loadTranslations() {
        const [ruRes, enRes] = await Promise.all([
            fetch('i18n/ru.json'),
            fetch('i18n/en.json')
        ]);

        this.i18n = {
            ru: await ruRes.json(),
            en: await enRes.json()
        };
    },

    /** Apply translations to the page */
    applyTranslations() {
        const texts = this.i18n[this.lang] || this.i18n.ru || {};

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (texts[key]) {
                el.textContent = texts[key];
            }
        });
    },

    /** Get translated text */
    t(key) {
        const texts = this.i18n[this.lang] || this.i18n.ru || {};
        return texts[key] || key;
    },

    /** Setup event listeners */
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.getAttribute('data-tab');
                this.switchTab(tabId);
                TelegramApp.hapticFeedback('light');
            });
        });

        // Language selector
        document.getElementById('setting-language')?.addEventListener('change', (e) => {
            this.handleSettingChange('language', e.target.value);
        });

        // Notifications toggle
        document.getElementById('setting-notifications')?.addEventListener('change', (e) => {
            this.handleSettingChange('notifications_enabled', e.target.checked);
            this.updateNotificationTimeVisibility();
        });

        // Notification time
        document.getElementById('setting-notification-time')?.addEventListener('change', (e) => {
            this.handleSettingChange('notification_time', e.target.value);
        });

        // Buy buttons
        document.getElementById('buy-lite')?.addEventListener('click', () => {
            this.handleBuy('subscription_lite');
        });

        document.getElementById('buy-pro')?.addEventListener('click', () => {
            this.handleBuy('subscription_pro');
        });

        // Copy referral link
        document.getElementById('copy-link')?.addEventListener('click', async () => {
            const link = document.getElementById('referral-link').value;
            const success = await TelegramApp.copyToClipboard(link);
            if (success) {
                TelegramApp.hapticFeedback('success');
                TelegramApp.showAlert(this.t('link_copied'));
            }
        });

        // Share referral link
        document.getElementById('share-link')?.addEventListener('click', () => {
            const link = document.getElementById('referral-link').value;
            TelegramApp.shareUrl(link, this.t('share_text'));
        });
    },

    /** Switch active tab */
    switchTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `tab-${tabId}`);
        });

        // Show/hide main button based on tab
        if (tabId === 'settings' && this.pendingSettings) {
            TelegramApp.showMainButton(this.t('btn_save'), () => this.saveSettings());
        } else {
            TelegramApp.hideMainButton();
        }
    },

    /** Load user data from API */
    async loadUserData() {
        this.userData = await API.getUser();
        this.lang = this.userData.user.language;
        this.applyTranslations();

        if (this.userData.is_onboarded) {
            this.renderUserData();
        } else {
            this.renderNotOnboardedState();
        }
    },

    /** Render state for users who haven't completed onboarding */
    renderNotOnboardedState() {
        // Profile tab - show placeholder with onboarding prompt
        document.getElementById('profile-name').textContent = '-';
        document.getElementById('profile-birthdate').textContent = '-';

        // Numbers - show placeholder
        document.getElementById('num-life-path').textContent = '-';
        document.getElementById('num-soul').textContent = '-';
        document.getElementById('num-expression').textContent = '-';
        document.getElementById('num-personality').textContent = '-';

        // Cycles
        document.getElementById('cycle-year').textContent = '-';
        document.getElementById('cycle-month').textContent = '-';
        document.getElementById('cycle-day').textContent = '-';

        // Matrix - show onboarding prompt
        document.getElementById('matrix-grid').innerHTML =
            `<p class="empty-state">${this.t('complete_onboarding')}</p>`;

        // Settings - these work even without onboarding!
        document.getElementById('setting-language').value = this.userData.user.language;
        document.getElementById('setting-notifications').checked = this.userData.user.notifications_enabled;
        document.getElementById('setting-notification-time').value = this.userData.user.notification_time;
        this.updateNotificationTimeVisibility();

        // Subscription - show current (FREE)
        const badge = document.getElementById('current-plan');
        badge.textContent = this.userData.subscription.type.toUpperCase();
        badge.className = `plan-badge ${this.userData.subscription.type}`;
        document.getElementById('plan-expires').textContent = '';

        // Payments - empty
        document.getElementById('payments-list').innerHTML =
            `<p class="empty-state">${this.t('no_payments')}</p>`;

        // Reports - show onboarding prompt
        document.getElementById('reports-list').innerHTML =
            `<p class="empty-state">${this.t('complete_onboarding')}</p>`;

        // Referral - show data (referral link works even before onboarding)
        document.getElementById('referral-count').textContent = this.userData.referral.referrals_count;
        document.getElementById('bonus-questions').textContent = this.userData.referral.questions_bonus;
        document.getElementById('referral-link').value = this.userData.referral.link;
    },

    /** Render user data to the UI */
    renderUserData() {
        if (!this.userData) return;

        const { user, numerology, subscription, referral, reports } = this.userData;

        // Profile tab
        document.getElementById('profile-name').textContent = user.name;
        document.getElementById('profile-birthdate').textContent = this.formatDate(user.birth_date);

        // Numbers
        document.getElementById('num-life-path').textContent = numerology.life_path;
        document.getElementById('num-soul').textContent = numerology.soul_number;
        document.getElementById('num-expression').textContent = numerology.expression_number;
        document.getElementById('num-personality').textContent = numerology.personality_number;

        // Cycles
        document.getElementById('cycle-year').textContent = numerology.personal_year;
        document.getElementById('cycle-month').textContent = numerology.personal_month;
        document.getElementById('cycle-day').textContent = numerology.personal_day;

        // Matrix
        this.renderMatrix(numerology.matrix);

        // Settings
        document.getElementById('setting-language').value = user.language;
        document.getElementById('setting-notifications').checked = user.notifications_enabled;
        document.getElementById('setting-notification-time').value = user.notification_time;
        this.updateNotificationTimeVisibility();

        // Subscription
        this.renderSubscription(subscription);

        // Payments
        this.renderPayments();

        // Reports
        this.renderReports();

        // Referral
        document.getElementById('referral-count').textContent = referral.referrals_count;
        document.getElementById('bonus-questions').textContent = referral.questions_bonus;
        document.getElementById('referral-link').value = referral.link;
    },

    /** Render Pythagoras matrix */
    renderMatrix(matrix) {
        const grid = document.getElementById('matrix-grid');
        grid.innerHTML = '';

        // Matrix layout: 1,2,3 / 4,5,6 / 7,8,9
        for (let i = 1; i <= 9; i++) {
            const count = matrix[i] || 0;
            const cell = document.createElement('div');
            cell.className = 'matrix-cell';
            cell.innerHTML = `
                <span class="matrix-number">${i}</span>
                <span class="matrix-count ${count === 0 ? 'empty' : ''}">${count > 0 ? '1'.repeat(count) : '-'}</span>
            `;
            grid.appendChild(cell);
        }
    },

    /** Render subscription status */
    renderSubscription(subscription) {
        const badge = document.getElementById('current-plan');
        const expires = document.getElementById('plan-expires');

        badge.textContent = subscription.type.toUpperCase();
        badge.className = `plan-badge ${subscription.type}`;

        if (subscription.is_active && subscription.expires) {
            expires.textContent = `${this.t('expires')}: ${this.formatDate(subscription.expires.split('T')[0])}`;
        } else {
            expires.textContent = '';
        }

        // Hide buy buttons if already subscribed to that plan
        const buyLite = document.getElementById('buy-lite');
        const buyPro = document.getElementById('buy-pro');

        if (subscription.is_active) {
            if (subscription.type === 'pro') {
                buyLite.style.display = 'none';
                buyPro.style.display = 'none';
            } else if (subscription.type === 'lite') {
                buyLite.style.display = 'none';
            }
        }
    },

    /** Render payment history */
    async renderPayments() {
        const data = await API.getPayments();
        const list = document.getElementById('payments-list');

        if (!data.payments || data.payments.length === 0) {
            list.innerHTML = `<p class="empty-state">${this.t('no_payments')}</p>`;
            return;
        }

        list.innerHTML = data.payments.map(p => `
            <div class="payment-item">
                <div class="payment-info">
                    <span class="payment-type">${this.getPaymentTypeName(p.type)}</span>
                    <span class="payment-date">${this.formatDate(p.date.split('T')[0])}</span>
                </div>
                <span class="payment-amount">${p.amount}★</span>
            </div>
        `).join('');
    },

    /** Render available reports */
    async renderReports() {
        const data = await API.getReports();
        const list = document.getElementById('reports-list');

        list.innerHTML = data.reports.map(r => {
            const name = this.lang === 'ru' ? r.name_ru : r.name_en;
            const desc = this.t(`report_desc_${r.id}`) || '';
            const requiresInput = r.requires_input !== null;
            const isAccessible = r.status === 'purchased' || r.status === 'included_in_pro';
            let statusText = '';
            let statusClass = '';

            if (r.status === 'purchased') {
                statusText = this.t('report_purchased');
                statusClass = 'purchased';
            } else if (r.status === 'included_in_pro') {
                statusText = this.t('report_included');
                statusClass = 'included';
            }

            // Button text: "Открыть" for accessible, price for others
            const btnText = isAccessible ? this.t('btn_open') : `${r.price}★`;

            return `
                <div class="report-item">
                    <div class="report-info">
                        <span class="report-name">${name}</span>
                        ${desc ? `<span class="report-desc">${desc}</span>` : ''}
                        ${requiresInput && !isAccessible ? `<span class="report-note">${this.t('report_requires_input')}</span>` : ''}
                        ${statusText ? `<span class="report-status ${statusClass}">${statusText}</span>` : ''}
                    </div>
                    <button class="report-btn" data-report="${r.id}" data-accessible="${isAccessible}">
                        ${btnText}
                    </button>
                </div>
            `;
        }).join('');

        // Add click handlers
        list.querySelectorAll('.report-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const reportId = btn.getAttribute('data-report');
                const isAccessible = btn.getAttribute('data-accessible') === 'true';

                TelegramApp.hapticFeedback('light');

                if (isAccessible) {
                    // Open report in premium view
                    window.location.href = `report.html?id=${reportId}`;
                } else {
                    // Redirect to bot for purchase
                    TelegramApp.openTelegramLink(`https://t.me/NumeroChatBot?start=report_${reportId}`);
                    TelegramApp.close();
                }
            });
        });
    },

    /** Handle setting change */
    handleSettingChange(key, value) {
        if (!this.pendingSettings) {
            this.pendingSettings = {};
        }
        this.pendingSettings[key] = value;

        // Change language immediately for preview
        if (key === 'language') {
            this.lang = value;
            this.applyTranslations();
        }

        // Show save button
        TelegramApp.showMainButton(this.t('btn_save'), () => this.saveSettings());
    },

    /** Save pending settings */
    async saveSettings() {
        if (!this.pendingSettings) return;

        TelegramApp.showMainButtonLoading();

        await API.updateSettings(this.pendingSettings);
        TelegramApp.hapticFeedback('success');
        TelegramApp.showAlert(this.t('settings_saved'));
        this.pendingSettings = null;
        TelegramApp.hideMainButton();
        TelegramApp.hideMainButtonLoading();
    },

    /** Update notification time row visibility */
    updateNotificationTimeVisibility() {
        const enabled = document.getElementById('setting-notifications').checked;
        const timeRow = document.getElementById('notification-time-row');
        timeRow.style.display = enabled ? 'flex' : 'none';
    },

    /** Handle purchase */
    async handleBuy(productType) {
        TelegramApp.hapticFeedback('medium');

        const data = await API.createInvoice(productType);

        if (data.invoice_url) {
            // Open invoice directly in Mini App
            TelegramApp.openInvoice(data.invoice_url, async (status) => {
                if (status === 'paid') {
                    TelegramApp.hapticFeedback('success');
                    TelegramApp.showAlert(this.t('payment_success'));
                    // Reload user data to reflect new subscription/purchase
                    await this.loadUserData();
                } else if (status === 'failed') {
                    TelegramApp.hapticFeedback('error');
                    TelegramApp.showAlert(this.t('payment_failed'));
                }
                // 'cancelled' status - no action needed
            });
        } else {
            TelegramApp.hapticFeedback('error');
            TelegramApp.showAlert(this.t('error_purchase'));
        }
    },

    /** Format date for display */
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString(this.lang === 'ru' ? 'ru-RU' : 'en-US', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    },

    /** Get payment type display name */
    getPaymentTypeName(type) {
        const names = {
            subscription_lite: 'LITE',
            subscription_pro: 'PRO',
            report_full_portrait: this.t('report_full_portrait'),
            report_financial_code: this.t('report_financial_code'),
            report_date_calendar: this.t('report_date_calendar'),
            report_year_forecast: this.t('report_year_forecast'),
            report_name_selection: this.t('report_name_selection'),
            report_compatibility_pro: this.t('report_compatibility_pro')
        };
        return names[type] || type;
    }
};

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
