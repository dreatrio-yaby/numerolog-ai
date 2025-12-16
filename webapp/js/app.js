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

        // Handle URL parameters for deep linking
        this.handleDeepLinks();
    },

    /** Handle deep links from URL parameters */
    handleDeepLinks() {
        const params = new URLSearchParams(window.location.search);
        const tab = params.get('tab');
        const reportId = params.get('report');

        if (tab) {
            this.switchTab(tab);
        }

        if (reportId) {
            // Open report input form after a short delay
            setTimeout(() => this.showReportInputForm(reportId), 300);
        }
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

        // Modal close handlers
        document.getElementById('modal-close')?.addEventListener('click', () => {
            this.closeModal();
        });
        document.getElementById('modal-backdrop')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Profile interpretation
        document.getElementById('get-interpretation')?.addEventListener('click', () => {
            TelegramApp.hapticFeedback('light');
            this.loadProfileInterpretation();
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
            const isGenerated = r.is_generated === true;
            const isMulti = r.multi_instance === true;
            const instanceCount = r.instance_count || 0;
            let statusText = '';
            let statusClass = '';

            if (r.status === 'purchased') {
                statusText = this.t('report_purchased');
                statusClass = 'purchased';
            } else if (r.status === 'included_in_pro') {
                statusText = this.t('report_included');
                statusClass = 'included';
            }

            // For multi-instance reports with instances, render expandable card
            if (isMulti && isAccessible && instanceCount > 0) {
                return this.renderMultiInstanceReport(r, name, desc, statusText, statusClass);
            }

            // Single-instance or no instances yet
            let btnText;
            if (isAccessible && isGenerated) {
                btnText = this.t('btn_open');
            } else if (isAccessible && !isGenerated) {
                btnText = this.t('btn_create');
            } else {
                btnText = `${r.price}★`;
            }

            return `
                <div class="report-item">
                    <div class="report-info">
                        <span class="report-name">${name}</span>
                        ${desc ? `<span class="report-desc">${desc}</span>` : ''}
                        ${requiresInput && !isAccessible ? `<span class="report-note">${this.t('report_requires_input')}</span>` : ''}
                        ${statusText ? `<span class="report-status ${statusClass}">${statusText}</span>` : ''}
                    </div>
                    <button class="report-btn" data-report="${r.id}" data-accessible="${isAccessible}" data-generated="${isGenerated}" data-multi="false">
                        ${btnText}
                    </button>
                </div>
            `;
        }).join('');

        // Add click handlers for single-instance reports
        list.querySelectorAll('.report-btn:not([data-instance])').forEach(btn => {
            btn.addEventListener('click', () => {
                const reportId = btn.getAttribute('data-report');
                const isAccessible = btn.getAttribute('data-accessible') === 'true';
                const isGenerated = btn.getAttribute('data-generated') === 'true';

                TelegramApp.hapticFeedback('light');

                if (isAccessible && isGenerated) {
                    // Open report in premium view
                    window.location.href = `report.html?id=${reportId}`;
                } else if (isAccessible && !isGenerated) {
                    // Show input form in Mini App for generation
                    this.showReportInputForm(reportId);
                } else {
                    // Not purchased - create invoice
                    this.handleBuy(`report_${reportId}`);
                }
            });
        });

        // Add handlers for multi-instance expandable headers
        list.querySelectorAll('.report-header-expandable').forEach(header => {
            header.addEventListener('click', () => {
                const item = header.closest('.report-item-multi');
                item.classList.toggle('expanded');
                TelegramApp.hapticFeedback('light');
            });
        });

        // Add handlers for instance open buttons
        list.querySelectorAll('.instance-open-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const reportId = btn.getAttribute('data-report');
                const instanceId = btn.getAttribute('data-instance');
                TelegramApp.hapticFeedback('light');
                window.location.href = `report.html?id=${reportId}&instance=${instanceId}`;
            });
        });

        // Add handlers for instance delete buttons
        list.querySelectorAll('.instance-delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const reportId = btn.getAttribute('data-report');
                const instanceId = btn.getAttribute('data-instance');

                TelegramApp.hapticFeedback('medium');

                const confirmed = await new Promise(resolve => {
                    TelegramApp.showConfirm(this.t('confirm_delete_report'), resolve);
                });

                if (confirmed) {
                    await API.deleteReportInstance(reportId, instanceId);
                    TelegramApp.hapticFeedback('success');
                    // Re-render reports
                    await this.renderReports();
                }
            });
        });

        // Add handlers for create new buttons
        list.querySelectorAll('.create-new-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const reportId = btn.getAttribute('data-report');
                TelegramApp.hapticFeedback('light');
                // Show input form in Mini App
                this.showReportInputForm(reportId);
            });
        });
    },

    /** Render multi-instance report with expandable list */
    renderMultiInstanceReport(report, name, desc, statusText, statusClass) {
        const instances = report.instances || [];
        const countText = this.lang === 'ru' ? `${instances.length} отчётов` : `${instances.length} reports`;

        return `
            <div class="report-item report-item-multi">
                <div class="report-header-expandable">
                    <div class="report-info">
                        <span class="report-name">${name}</span>
                        ${desc ? `<span class="report-desc">${desc}</span>` : ''}
                        ${statusText ? `<span class="report-status ${statusClass}">${statusText}</span>` : ''}
                    </div>
                    <div class="report-expand-info">
                        <span class="instance-count">${countText}</span>
                        <span class="expand-icon">▼</span>
                    </div>
                </div>
                <div class="instances-list">
                    ${instances.map(inst => this.renderReportInstance(report.id, inst)).join('')}
                    <button class="create-new-btn" data-report="${report.id}">
                        + ${this.t('btn_create_new')}
                    </button>
                </div>
            </div>
        `;
    },

    /** Render single instance item */
    renderReportInstance(reportId, instance) {
        const contextLabel = this.getInstanceContextLabel(reportId, instance.context);
        const date = instance.created_at ? this.formatDate(instance.created_at.split('T')[0]) : '';

        return `
            <div class="instance-item">
                <div class="instance-info">
                    <span class="instance-context">${contextLabel}</span>
                    <span class="instance-date">${date}</span>
                </div>
                <div class="instance-actions">
                    <button class="instance-open-btn" data-report="${reportId}" data-instance="${instance.instance_id}">
                        ${this.t('btn_open')}
                    </button>
                    <button class="instance-delete-btn" data-report="${reportId}" data-instance="${instance.instance_id}">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    },

    /** Get human-readable label for instance context */
    getInstanceContextLabel(reportId, context) {
        if (!context) return '';

        if (reportId === 'compatibility_pro') {
            const name = context.partner_name || context.name || '';
            const date = context.partner_birth_date || context.birth_date || '';
            if (name && date) {
                return `${name} (${this.formatDate(date)})`;
            }
            return name || this.t('partner');
        }

        if (reportId === 'name_selection') {
            const purpose = context.purpose;
            const gender = context.gender;
            if (purpose === 'child') {
                const genderText = gender === 'male' ? this.t('boy') : gender === 'female' ? this.t('girl') : '';
                return genderText ? `${this.t('for_child')} (${genderText})` : this.t('for_child');
            }
            if (purpose === 'business') return this.t('for_business');
            if (purpose === 'self') return this.t('for_self');
            return '';
        }

        if (reportId === 'year_forecast') {
            return context.year ? `${context.year}` : '';
        }

        if (reportId === 'date_calendar') {
            if (context.month && context.year) {
                const monthNames = this.lang === 'ru'
                    ? ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
                    : ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                return `${monthNames[context.month]} ${context.year}`;
            }
            return '';
        }

        return '';
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
    },

    // ========== Modal & Report Forms ==========

    /** Show report input form modal */
    showReportInputForm(reportId) {
        const modal = document.getElementById('report-modal');
        const body = document.getElementById('modal-body');

        let formHtml = '';
        const currentYear = new Date().getFullYear();
        const currentMonth = new Date().getMonth() + 1;

        if (reportId === 'name_selection') {
            formHtml = `
                <h3>${this.t('name_selection_title')}</h3>
                <div class="form-group">
                    <label>${this.t('purpose')}</label>
                    <select id="form-name-purpose">
                        <option value="child">${this.t('for_child')}</option>
                        <option value="business">${this.t('for_business')}</option>
                        <option value="self">${this.t('for_self')}</option>
                    </select>
                </div>
                <div class="form-group" id="form-gender-group" style="display:none;">
                    <label>${this.t('gender')}</label>
                    <select id="form-child-gender">
                        <option value="male">${this.t('boy')}</option>
                        <option value="female">${this.t('girl')}</option>
                    </select>
                </div>
                <button class="form-submit-btn" id="form-submit">${this.t('btn_create')}</button>
            `;
        } else if (reportId === 'compatibility_pro') {
            formHtml = `
                <h3>${this.t('compatibility_pro_title')}</h3>
                <div class="form-group">
                    <label>${this.t('partner_name')}</label>
                    <input type="text" id="form-partner-name" placeholder="${this.t('enter_name')}">
                </div>
                <div class="form-group">
                    <label>${this.t('partner_birthdate')}</label>
                    <input type="date" id="form-partner-birthdate">
                </div>
                <button class="form-submit-btn" id="form-submit">${this.t('btn_create')}</button>
            `;
        } else if (reportId === 'year_forecast') {
            formHtml = `
                <h3>${this.t('year_forecast_title')}</h3>
                <div class="form-group">
                    <label>${this.t('select_year')}</label>
                    <select id="form-forecast-year">
                        <option value="${currentYear}">${currentYear}</option>
                        <option value="${currentYear + 1}">${currentYear + 1}</option>
                    </select>
                </div>
                <button class="form-submit-btn" id="form-submit">${this.t('btn_create')}</button>
            `;
        } else if (reportId === 'date_calendar') {
            const monthNames = this.lang === 'ru'
                ? ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
                : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

            let monthOptions = '';
            for (let i = 0; i < 12; i++) {
                const m = ((currentMonth - 1 + i) % 12) + 1;
                const y = currentYear + Math.floor((currentMonth - 1 + i) / 12);
                monthOptions += `<option value="${m}-${y}">${monthNames[m - 1]} ${y}</option>`;
            }

            formHtml = `
                <h3>${this.t('date_calendar_title')}</h3>
                <div class="form-group">
                    <label>${this.t('select_month')}</label>
                    <select id="form-calendar-month">${monthOptions}</select>
                </div>
                <button class="form-submit-btn" id="form-submit">${this.t('btn_create')}</button>
            `;
        } else if (reportId === 'full_portrait' || reportId === 'financial_code') {
            // Single-instance, no form needed - generate directly
            this.submitReportGeneration(reportId, {});
            return;
        } else {
            this.closeModal();
            return;
        }

        body.innerHTML = formHtml;
        modal.classList.remove('hidden');

        this.setupReportFormHandlers(reportId);
    },

    /** Setup form handlers for report input */
    setupReportFormHandlers(reportId) {
        if (reportId === 'name_selection') {
            document.getElementById('form-name-purpose')?.addEventListener('change', (e) => {
                const genderGroup = document.getElementById('form-gender-group');
                genderGroup.style.display = e.target.value === 'child' ? 'block' : 'none';
            });

            document.getElementById('form-submit')?.addEventListener('click', () => {
                const purpose = document.getElementById('form-name-purpose').value;
                const gender = purpose === 'child'
                    ? document.getElementById('form-child-gender').value
                    : null;
                this.submitReportGeneration('name_selection', { purpose, gender });
            });
        } else if (reportId === 'compatibility_pro') {
            document.getElementById('form-submit')?.addEventListener('click', () => {
                const partnerName = document.getElementById('form-partner-name').value;
                const partnerBirthdate = document.getElementById('form-partner-birthdate').value;

                if (!partnerName || !partnerBirthdate) {
                    TelegramApp.showAlert(this.t('fill_all_fields'));
                    return;
                }

                this.submitReportGeneration('compatibility_pro', {
                    partner_name: partnerName,
                    partner_birth_date: partnerBirthdate
                });
            });
        } else if (reportId === 'year_forecast') {
            document.getElementById('form-submit')?.addEventListener('click', () => {
                const year = parseInt(document.getElementById('form-forecast-year').value);
                this.submitReportGeneration('year_forecast', { year });
            });
        } else if (reportId === 'date_calendar') {
            document.getElementById('form-submit')?.addEventListener('click', () => {
                const value = document.getElementById('form-calendar-month').value;
                const [month, year] = value.split('-').map(Number);
                this.submitReportGeneration('date_calendar', { month, year });
            });
        }
    },

    /** Submit report generation request */
    async submitReportGeneration(reportId, context) {
        const modal = document.getElementById('report-modal');
        const body = document.getElementById('modal-body');

        // Show loading
        body.innerHTML = `
            <div class="modal-loading">
                <div class="spinner"></div>
                <p>${this.t('generating_report')}</p>
            </div>
        `;
        modal.classList.remove('hidden');

        const result = await API.generateReport(reportId, context);

        if (result.status === 'completed') {
            TelegramApp.hapticFeedback('success');
            this.closeModal();

            // Navigate to report
            const url = result.instance_id
                ? `report.html?id=${reportId}&instance=${result.instance_id}`
                : `report.html?id=${reportId}`;
            window.location.href = url;
        } else if (result.status === 'generating') {
            // Report is being generated, wait and retry
            body.innerHTML = `
                <div class="modal-loading">
                    <div class="spinner"></div>
                    <p>${this.t('report_generating_wait')}</p>
                </div>
            `;
            // Poll for completion
            setTimeout(() => this.pollReportStatus(reportId, context), 3000);
        } else {
            TelegramApp.hapticFeedback('error');
            TelegramApp.showAlert(this.t('error_generating'));
            this.closeModal();
        }
    },

    /** Poll for report generation status */
    async pollReportStatus(reportId, context) {
        const result = await API.generateReport(reportId, context);

        if (result.status === 'completed') {
            TelegramApp.hapticFeedback('success');
            this.closeModal();
            const url = result.instance_id
                ? `report.html?id=${reportId}&instance=${result.instance_id}`
                : `report.html?id=${reportId}`;
            window.location.href = url;
        } else if (result.status === 'generating') {
            setTimeout(() => this.pollReportStatus(reportId, context), 3000);
        } else {
            TelegramApp.hapticFeedback('error');
            TelegramApp.showAlert(this.t('error_generating'));
            this.closeModal();
        }
    },

    /** Close modal */
    closeModal() {
        document.getElementById('report-modal')?.classList.add('hidden');
    },

    // ========== Profile Interpretation ==========

    /** Load AI interpretation for user profile */
    async loadProfileInterpretation() {
        const container = document.getElementById('interpretation-container');
        const card = document.getElementById('interpretation-card');

        if (!container || !card) return;

        // Show loading state
        container.innerHTML = `
            <div class="interpretation-loading">
                <div class="spinner-small"></div>
                <span>${this.t('analyzing')}</span>
            </div>
        `;

        const result = await API.getProfileInterpretation();

        if (result && result.interpretation) {
            // Display interpretation
            const paragraphs = result.interpretation.split('\n\n');
            container.innerHTML = `
                <div class="interpretation-text">
                    ${paragraphs
                        .filter(p => p.trim())
                        .map(p => `<p>${this.escapeHtml(p)}</p>`)
                        .join('')}
                </div>
            `;
            TelegramApp.hapticFeedback('success');
        } else {
            // Show error/retry button
            container.innerHTML = `
                <p class="interpretation-error">${this.t('interpretation_error')}</p>
                <button class="btn-interpretation" id="retry-interpretation">
                    ${this.t('btn_retry')}
                </button>
            `;
            document.getElementById('retry-interpretation')?.addEventListener('click', () => {
                TelegramApp.hapticFeedback('light');
                this.loadProfileInterpretation();
            });
        }
    },

    /** Escape HTML for safe display */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
