/**
 * Report page logic - loads and renders premium reports
 */

const ReportPage = {
    // Current language
    language: 'ru',

    // Report icons mapping
    reportIcons: {
        'full_portrait': '📜',
        'financial_code': '💰',
        'date_calendar': '📅',
        'year_forecast': '🗓️',
        'name_selection': '📝',
        'compatibility_pro': '💑'
    },

    // Section icons mapping (keywords -> icons)
    sectionIcons: {
        // Russian
        'миссия': '🎯',
        'предназначение': '🎯',
        'путь': '🛤️',
        'душа': '💫',
        'внутренний мир': '💫',
        'внешность': '👤',
        'восприятие': '👤',
        'талант': '⭐',
        'карьера': '💼',
        'работа': '💼',
        'деньги': '💰',
        'финанс': '💰',
        'доход': '💰',
        'любовь': '💕',
        'отношения': '💕',
        'семья': '👨‍👩‍👧‍👦',
        'здоровье': '🏥',
        'энергия': '⚡',
        'матрица': '🔢',
        'сильные стороны': '💪',
        'слабые': '🔧',
        'развитие': '📈',
        'совет': '💡',
        'рекомендац': '💡',
        'прогноз': '🔮',
        'период': '📆',
        'год': '📆',
        'месяц': '📆',
        'январь': '❄️',
        'февраль': '❄️',
        'март': '🌱',
        'апрель': '🌱',
        'май': '🌸',
        'июнь': '☀️',
        'июль': '☀️',
        'август': '☀️',
        'сентябрь': '🍂',
        'октябрь': '🍂',
        'ноябрь': '🍂',
        'декабрь': '❄️',
        'предупреждени': '⚠️',
        'опасност': '⚠️',
        'совместимост': '💑',
        'партнер': '💑',
        'имя': '📝',
        'имен': '📝',
        'календарь': '📅',
        'дат': '📅',
        'благоприятн': '✅',
        'неблагоприятн': '❌',
        // English
        'mission': '🎯',
        'life path': '🛤️',
        'soul': '💫',
        'inner': '💫',
        'personality': '👤',
        'expression': '👤',
        'talent': '⭐',
        'career': '💼',
        'work': '💼',
        'money': '💰',
        'financ': '💰',
        'income': '💰',
        'love': '💕',
        'relationship': '💕',
        'family': '👨‍👩‍👧‍👦',
        'health': '🏥',
        'energy': '⚡',
        'matrix': '🔢',
        'strength': '💪',
        'weakness': '🔧',
        'growth': '📈',
        'advice': '💡',
        'recommend': '💡',
        'forecast': '🔮',
        'period': '📆',
        'year': '📆',
        'month': '📆',
        'january': '❄️',
        'february': '❄️',
        'march': '🌱',
        'april': '🌱',
        'may': '🌸',
        'june': '☀️',
        'july': '☀️',
        'august': '☀️',
        'september': '🍂',
        'october': '🍂',
        'november': '🍂',
        'december': '❄️',
        'warning': '⚠️',
        'danger': '⚠️',
        'compatibility': '💑',
        'partner': '💑',
        'name': '📝',
        'calendar': '📅',
        'date': '📅',
        'favorable': '✅',
        'unfavorable': '❌'
    },

    // Translations
    i18n: {
        ru: {
            loading: 'Загружаем отчёт...',
            error: 'Не удалось загрузить отчёт',
            back: 'Назад',
            generated: 'Сгенерировано',
            subtitle: 'Персональный анализ'
        },
        en: {
            loading: 'Loading report...',
            error: 'Failed to load report',
            back: 'Back',
            generated: 'Generated',
            subtitle: 'Personal Analysis'
        }
    },

    /** Initialize the report page */
    async init() {
        // Initialize Telegram WebApp
        TelegramApp.init();

        // Get language
        this.language = TelegramApp.getLanguage().startsWith('ru') ? 'ru' : 'en';

        // Update loading text
        document.getElementById('loading-text').textContent = this.t('loading');

        // Get report ID and optional instance ID from URL or start_param
        const { reportId, instanceId } = this.getReportId();

        if (!reportId) {
            this.showError(this.t('error'));
            return;
        }

        // Setup back buttons
        this.setupBackButtons();

        // Load and render report
        await this.loadReport(reportId, instanceId);
    },

    /** Get translation */
    t(key) {
        return this.i18n[this.language]?.[key] || this.i18n['en'][key] || key;
    },

    /** Get report ID and optional instance ID from URL or start_param */
    getReportId() {
        // Try URL parameter first
        const urlParams = new URLSearchParams(window.location.search);
        let reportId = urlParams.get('id');
        let instanceId = urlParams.get('instance');

        // Try start_param (from Telegram deep link)
        if (!reportId) {
            const startParam = TelegramApp.getStartParam();
            if (startParam && startParam.startsWith('report_')) {
                // Format: report_<type> or report_<type>_<instance>
                const parts = startParam.replace('report_', '').split('_');
                reportId = parts[0];
                if (parts.length > 1) {
                    instanceId = parts.slice(1).join('_');
                }
            }
        }

        return { reportId, instanceId };
    },

    /** Setup back button handlers */
    setupBackButtons() {
        const backBtn = document.getElementById('back-btn');
        const headerBackBtn = document.getElementById('header-back-btn');

        const goBack = () => {
            TelegramApp.hapticFeedback('light');
            // Try to go back in history, or close the app
            if (window.history.length > 1) {
                window.history.back();
            } else {
                TelegramApp.close();
            }
        };

        if (backBtn) backBtn.addEventListener('click', goBack);
        if (headerBackBtn) headerBackBtn.addEventListener('click', goBack);

        // Also setup Telegram back button
        if (TelegramApp.tg?.BackButton) {
            TelegramApp.tg.BackButton.show();
            TelegramApp.tg.BackButton.onClick(goBack);
        }
    },

    /** Load report from API */
    async loadReport(reportId, instanceId = null) {
        try {
            const data = await API.getReportContent(reportId, instanceId);
            this.renderReport(data);
        } catch (error) {
            console.error('Failed to load report:', error);
            this.showError(this.t('error'));
        }
    },

    /** Show error state */
    showError(message) {
        document.getElementById('report-loading').style.display = 'none';
        document.getElementById('report-error').style.display = 'flex';
        document.getElementById('error-text').textContent = message;
        document.getElementById('back-btn').textContent = this.t('back');
    },

    /** Render the report */
    renderReport(data) {
        // Hide loading, show content
        document.getElementById('report-loading').style.display = 'none';
        document.getElementById('report-content').style.display = 'block';

        // Set header
        const header = document.querySelector('.report-header');
        header.classList.add(data.id);

        const title = this.language === 'ru' ? data.title_ru : data.title_en;
        document.getElementById('report-icon').textContent = this.reportIcons[data.id] || '📜';
        document.getElementById('report-title').textContent = title;
        document.getElementById('report-subtitle').textContent = this.t('subtitle');

        // Set footer date
        if (data.generated_at) {
            const date = new Date(data.generated_at);
            const formattedDate = date.toLocaleDateString(this.language === 'ru' ? 'ru-RU' : 'en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            document.getElementById('footer-date').textContent = `${this.t('generated')} ${formattedDate}`;
        }

        // Render content
        this.renderContent(data.content);

        // Trigger success haptic
        TelegramApp.hapticFeedback('success');
    },

    /** Render report content with sections */
    renderContent(content) {
        const body = document.getElementById('report-body');

        // Parse markdown content into sections
        const sections = this.parseIntoSections(content);

        // Render each section
        sections.forEach((section, index) => {
            const sectionEl = this.createSection(section, index);
            body.appendChild(sectionEl);
        });
    },

    /** Parse content into sections based on headers */
    parseIntoSections(content) {
        const sections = [];
        const lines = content.split('\n');

        let currentSection = null;
        let introContent = [];

        for (const line of lines) {
            // Check for section header (## or ### or numbered like "1." or "1)")
            const h2Match = line.match(/^##\s+(.+)$/);
            const h3Match = line.match(/^###\s+(.+)$/);
            const numberedMatch = line.match(/^(\d+[\.\)]\s*)(.+)$/);
            const boldHeaderMatch = line.match(/^\*\*(.+)\*\*$/);

            if (h2Match || h3Match) {
                // Save previous section
                if (currentSection) {
                    sections.push(currentSection);
                } else if (introContent.length > 0) {
                    // Save intro content
                    sections.push({
                        type: 'intro',
                        content: introContent.join('\n').trim()
                    });
                    introContent = [];
                }

                const title = (h2Match || h3Match)[1].trim();
                currentSection = {
                    type: 'section',
                    title: title,
                    icon: this.getSectionIcon(title),
                    content: ''
                };
            } else if (numberedMatch && line.length < 100 && !currentSection) {
                // This might be a section header like "1. Миссия"
                if (introContent.length > 0) {
                    sections.push({
                        type: 'intro',
                        content: introContent.join('\n').trim()
                    });
                    introContent = [];
                }

                const title = numberedMatch[2].trim();
                currentSection = {
                    type: 'section',
                    title: title,
                    icon: this.getSectionIcon(title),
                    content: ''
                };
            } else if (boldHeaderMatch && !currentSection && line.length < 80) {
                // Bold header like **Раздел**
                if (introContent.length > 0) {
                    sections.push({
                        type: 'intro',
                        content: introContent.join('\n').trim()
                    });
                    introContent = [];
                }

                const title = boldHeaderMatch[1].trim();
                currentSection = {
                    type: 'section',
                    title: title,
                    icon: this.getSectionIcon(title),
                    content: ''
                };
            } else {
                // Regular content
                if (currentSection) {
                    currentSection.content += line + '\n';
                } else {
                    introContent.push(line);
                }
            }
        }

        // Push last section
        if (currentSection) {
            sections.push(currentSection);
        } else if (introContent.length > 0) {
            sections.push({
                type: 'intro',
                content: introContent.join('\n').trim()
            });
        }

        return sections.filter(s => s.content && s.content.trim());
    },

    /** Get icon for section based on title keywords */
    getSectionIcon(title) {
        const lowerTitle = title.toLowerCase();

        for (const [keyword, icon] of Object.entries(this.sectionIcons)) {
            if (lowerTitle.includes(keyword)) {
                return icon;
            }
        }

        return '✨'; // Default icon
    },

    /** Create section DOM element */
    createSection(section, index) {
        if (section.type === 'intro') {
            const div = document.createElement('div');
            div.className = 'report-intro';
            div.innerHTML = this.renderMarkdown(section.content);
            return div;
        }

        const div = document.createElement('div');
        div.className = 'report-section';

        div.innerHTML = `
            <div class="section-header">
                <span class="section-icon">${section.icon}</span>
                <h2 class="section-title">${this.escapeHtml(section.title)}</h2>
            </div>
            <div class="section-content">
                ${this.renderMarkdown(section.content)}
            </div>
        `;

        return div;
    },

    /** Render markdown to HTML */
    renderMarkdown(content) {
        // Use marked.js if available
        if (typeof marked !== 'undefined') {
            // Configure marked
            marked.setOptions({
                breaks: true,
                gfm: true
            });
            return marked.parse(content);
        }

        // Fallback: simple markdown rendering
        let html = this.escapeHtml(content);

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        // Lists
        html = html.replace(/^[-•]\s+(.+)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        return `<p>${html}</p>`;
    },

    /** Escape HTML entities */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ReportPage.init();
});
