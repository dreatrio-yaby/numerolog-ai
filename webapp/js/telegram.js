/**
 * Telegram Mini App SDK wrapper
 */

const TelegramApp = {
    /** @type {WebApp} */
    tg: window.Telegram?.WebApp,

    /** Initialize the Mini App */
    init() {
        if (!this.tg) {
            console.error('Telegram WebApp not available');
            return false;
        }

        // Signal that the app is ready
        this.tg.ready();

        // Expand to full height
        this.tg.expand();

        // Enable closing confirmation if there are unsaved changes
        this.tg.enableClosingConfirmation();

        return true;
    },

    /** Get init data string for API authentication */
    getInitData() {
        return this.tg?.initData || '';
    },

    /** Get user info from init data */
    getUser() {
        return this.tg?.initDataUnsafe?.user || null;
    },

    /** Get user's language code */
    getLanguage() {
        const user = this.getUser();
        return user?.language_code || 'ru';
    },

    /** Show main button */
    showMainButton(text, onClick) {
        if (!this.tg?.MainButton) return;

        this.tg.MainButton.setText(text);
        this.tg.MainButton.onClick(onClick);
        this.tg.MainButton.show();
    },

    /** Hide main button */
    hideMainButton() {
        if (!this.tg?.MainButton) return;
        this.tg.MainButton.hide();
    },

    /** Show loading state on main button */
    showMainButtonLoading() {
        if (!this.tg?.MainButton) return;
        this.tg.MainButton.showProgress();
    },

    /** Hide loading state on main button */
    hideMainButtonLoading() {
        if (!this.tg?.MainButton) return;
        this.tg.MainButton.hideProgress();
    },

    /** Show alert popup */
    showAlert(message) {
        if (this.tg?.showAlert) {
            this.tg.showAlert(message);
        } else {
            alert(message);
        }
    },

    /** Show confirmation popup */
    showConfirm(message, callback) {
        if (this.tg?.showConfirm) {
            this.tg.showConfirm(message, callback);
        } else {
            callback(confirm(message));
        }
    },

    /** Open invoice for payment */
    openInvoice(url, callback) {
        if (this.tg?.openInvoice) {
            this.tg.openInvoice(url, callback);
        }
    },

    /** Open link in browser */
    openLink(url) {
        if (this.tg?.openLink) {
            this.tg.openLink(url);
        } else {
            window.open(url, '_blank');
        }
    },

    /** Open Telegram link */
    openTelegramLink(url) {
        if (this.tg?.openTelegramLink) {
            this.tg.openTelegramLink(url);
        } else {
            window.open(url, '_blank');
        }
    },

    /** Share URL via Telegram */
    shareUrl(url, text = '') {
        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
        this.openTelegramLink(shareUrl);
    },

    /** Copy text to clipboard */
    async copyToClipboard(text) {
        await navigator.clipboard.writeText(text);
        return true;
    },

    /** Trigger haptic feedback */
    hapticFeedback(type = 'light') {
        if (!this.tg?.HapticFeedback) return;

        switch (type) {
            case 'light':
                this.tg.HapticFeedback.impactOccurred('light');
                break;
            case 'medium':
                this.tg.HapticFeedback.impactOccurred('medium');
                break;
            case 'heavy':
                this.tg.HapticFeedback.impactOccurred('heavy');
                break;
            case 'success':
                this.tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'warning':
                this.tg.HapticFeedback.notificationOccurred('warning');
                break;
            case 'error':
                this.tg.HapticFeedback.notificationOccurred('error');
                break;
        }
    },

    /** Close the Mini App */
    close() {
        if (this.tg?.close) {
            this.tg.close();
        }
    },

    /** Disable closing confirmation */
    disableClosingConfirmation() {
        if (this.tg?.disableClosingConfirmation) {
            this.tg.disableClosingConfirmation();
        }
    }
};

// Export for use in other modules
window.TelegramApp = TelegramApp;
