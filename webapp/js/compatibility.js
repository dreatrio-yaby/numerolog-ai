/**
 * Compatibility Page - Display compatibility result with AI interpretation
 */

const CompatibilityPage = {
    lang: 'ru',
    resultId: null,
    translations: {},

    async init() {
        // Initialize Telegram WebApp
        if (!TelegramApp.init()) {
            this.showError('Telegram WebApp not available');
            return;
        }

        // Get result_id from URL
        const params = new URLSearchParams(window.location.search);
        this.resultId = params.get('id');

        if (!this.resultId) {
            this.showError('No result ID provided');
            return;
        }

        // Load translations
        await this.loadTranslations();

        // Setup event listeners
        this.setupEventListeners();

        // Load result
        await this.loadResult();
    },

    async loadTranslations() {
        // Detect language from Telegram
        const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code;
        this.lang = (tgLang === 'ru' || tgLang === 'uk' || tgLang === 'be') ? 'ru' : 'en';

        const file = this.lang === 'ru' ? 'i18n/ru.json' : 'i18n/en.json';
        const response = await fetch(file);
        if (response.ok) {
            this.translations = await response.json();
        }
    },

    t(key) {
        return this.translations[key] || key;
    },

    async loadResult() {
        const result = await API.getCompatibilityResult(this.resultId);

        if (!result || result.error) {
            this.showError(this.t('error_loading_result'));
            return;
        }

        this.renderResult(result);
        this.hideLoading();

        // Load AI interpretation
        this.loadInterpretation();
    },

    renderResult(result) {
        const scores = result.scores || {};
        const overallScore = scores.overall_score || 0;
        const lifePathScore = scores.life_path_score || 0;
        const soulScore = scores.soul_score || 0;

        // Update title
        document.getElementById('compat-title').textContent = this.t('compatibility_title');
        document.getElementById('score-label').textContent = this.t('overall_compatibility');

        // Animate overall score
        this.animateScore(overallScore);

        // Update breakdown
        document.getElementById('life-path-label').textContent = this.t('life_path_compat');
        document.getElementById('soul-label').textContent = this.t('soul_compat');

        document.getElementById('life-path-score').textContent = lifePathScore + '%';
        document.getElementById('soul-score').textContent = soulScore + '%';

        // Animate bars after delay
        setTimeout(() => {
            document.getElementById('life-path-fill').style.width = lifePathScore + '%';
            document.getElementById('soul-fill').style.width = soulScore + '%';
        }, 100);

        // Partner date
        document.getElementById('partner-label').textContent = this.t('partner_birthdate');
        document.getElementById('partner-date').textContent = this.formatDate(result.partner_date);

        // Button texts
        document.getElementById('pro-btn-text').textContent = this.t('get_pro_analysis');
        document.getElementById('new-check-text').textContent = this.t('check_another');
    },

    animateScore(targetScore) {
        const scoreEl = document.getElementById('overall-score');
        const ringEl = document.getElementById('score-ring');

        // Animate number
        let current = 0;
        const duration = 1500;
        const step = targetScore / (duration / 16);

        const animate = () => {
            current = Math.min(current + step, targetScore);
            scoreEl.textContent = Math.round(current);

            // Animate ring (circumference = 2 * PI * 54 = 339.292)
            const circumference = 339.292;
            const offset = circumference - (circumference * current / 100);
            ringEl.style.strokeDashoffset = offset;

            if (current < targetScore) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    },

    async loadInterpretation() {
        const loadingEl = document.getElementById('interpretation-loading');
        const contentEl = document.getElementById('interpretation-content');
        const loadingTextEl = document.getElementById('interpretation-loading-text');

        loadingTextEl.textContent = this.t('analyzing');

        const response = await API.getCompatibilityInterpretation(this.resultId);

        if (response && response.interpretation) {
            // Parse and display interpretation
            const paragraphs = response.interpretation.split('\n\n');
            contentEl.innerHTML = paragraphs
                .filter(p => p.trim())
                .map(p => `<p>${this.escapeHtml(p)}</p>`)
                .join('');

            loadingEl.style.display = 'none';
            contentEl.style.display = 'block';
        } else {
            loadingEl.innerHTML = `<span>${this.t('interpretation_unavailable')}</span>`;
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString(this.lang === 'ru' ? 'ru-RU' : 'en-US', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    },

    setupEventListeners() {
        // Back button
        document.getElementById('header-back-btn').addEventListener('click', () => {
            this.goBack();
        });

        document.getElementById('error-back-btn')?.addEventListener('click', () => {
            this.goBack();
        });

        // PRO button - open reports tab with compatibility_pro
        document.getElementById('pro-btn').addEventListener('click', () => {
            TelegramApp.hapticFeedback('light');
            window.location.href = 'index.html?tab=reports&report=compatibility_pro';
        });

        // New check button - back to bot
        document.getElementById('new-check-btn').addEventListener('click', () => {
            TelegramApp.hapticFeedback('light');
            // Open bot chat with /compatibility command
            const botUsername = 'NumeroChatBot';
            TelegramApp.openTelegramLink(`https://t.me/${botUsername}`);
            TelegramApp.close();
        });

        // Handle back button in Telegram
        TelegramApp.onBackButton(() => {
            this.goBack();
        });
    },

    goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = 'index.html';
        }
    },

    hideLoading() {
        document.getElementById('compat-loading').style.display = 'none';
        document.getElementById('compat-content').style.display = 'block';
    },

    showError(message) {
        document.getElementById('compat-loading').style.display = 'none';
        document.getElementById('compat-error').style.display = 'flex';
        document.getElementById('error-text').textContent = message;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => CompatibilityPage.init());
