/**
 * Settings Controller - Manage application settings and preferences
 */

export class SettingsController {
    constructor(api, state, ui, conversationService) {
        this.api = api;
        this.state = state;
        this.ui = ui;
        this.conversationService = conversationService;
        this.settings = this.loadSettings();
        
        this.init();
    }

    init() {
        console.log('⚙️ Settings Controller initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for view changes
        document.addEventListener('viewChanged', (e) => {
            if (e.detail === 'settings') {
                this.renderSettings();
            }
        });

        // Save settings button
        const saveBtn = document.getElementById('save-settings');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveAllSettings());
        }

        // Reset settings button
        const resetBtn = document.getElementById('reset-settings');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetSettings());
        }

        // Export data button
        const exportBtn = document.getElementById('export-data');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAllData());
        }

        // Import data button
        const importBtn = document.getElementById('import-data');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importData());
        }

        // Clear data button
        const clearBtn = document.getElementById('clear-all-data');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAllData());
        }
    }

    /**
     * Render settings view
     */
    renderSettings() {
        const container = document.getElementById('settings-view');
        if (!container) return;

        const user = this.state.getState('user');
        
        container.innerHTML = `
            <div class="settings-container">
                <div class="settings-section">
                    <h2>
                        <i class="fas fa-user"></i>
                        Profile
                    </h2>
                    <div class="settings-card">
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" id="setting-username" value="${user?.username || ''}" readonly>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="setting-email" value="${user?.email || ''}" readonly>
                        </div>
                        <div class="form-group">
                            <label>Role</label>
                            <input type="text" id="setting-role" value="${user?.role || 'user'}" readonly>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h2>
                        <i class="fas fa-palette"></i>
                        Appearance
                    </h2>
                    <div class="settings-card">
                        <div class="form-group">
                            <label>Theme</label>
                            <select id="setting-theme">
                                <option value="dark" ${this.settings.theme === 'dark' ? 'selected' : ''}>Dark</option>
                                <option value="light" ${this.settings.theme === 'light' ? 'selected' : ''}>Light</option>
                                <option value="auto" ${this.settings.theme === 'auto' ? 'selected' : ''}>Auto</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Font Size</label>
                            <select id="setting-font-size">
                                <option value="small" ${this.settings.fontSize === 'small' ? 'selected' : ''}>Small</option>
                                <option value="medium" ${this.settings.fontSize === 'medium' ? 'selected' : ''}>Medium</option>
                                <option value="large" ${this.settings.fontSize === 'large' ? 'selected' : ''}>Large</option>
                            </select>
                        </div>
                        <div class="form-group checkbox-group">
                            <label>
                                <input type="checkbox" id="setting-animations" ${this.settings.animations ? 'checked' : ''}>
                                <span>Enable animations</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h2>
                        <i class="fas fa-comment"></i>
                        Chat Settings
                    </h2>
                    <div class="settings-card">
                        <div class="form-group checkbox-group">
                            <label>
                                <input type="checkbox" id="setting-stream" ${this.settings.streamResponses ? 'checked' : ''}>
                                <span>Stream responses</span>
                            </label>
                        </div>
                        <div class="form-group checkbox-group">
                            <label>
                                <input type="checkbox" id="setting-auto-save" ${this.settings.autoSaveConversations ? 'checked' : ''}>
                                <span>Auto-save conversations</span>
                            </label>
                        </div>
                        <div class="form-group checkbox-group">
                            <label>
                                <input type="checkbox" id="setting-sound" ${this.settings.soundEnabled ? 'checked' : ''}>
                                <span>Sound notifications</span>
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Default Language</label>
                            <select id="setting-language">
                                <option value="auto" ${this.settings.language === 'auto' ? 'selected' : ''}>Auto-detect</option>
                                <option value="en" ${this.settings.language === 'en' ? 'selected' : ''}>English</option>
                                <option value="vi" ${this.settings.language === 'vi' ? 'selected' : ''}>Tiếng Việt</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h2>
                        <i class="fas fa-keyboard"></i>
                        Keyboard Shortcuts
                    </h2>
                    <div class="settings-card">
                        <div class="shortcuts-list">
                            <div class="shortcut-item">
                                <span class="shortcut-key"><kbd>Ctrl</kbd> + <kbd>K</kbd></span>
                                <span class="shortcut-desc">Open quick search</span>
                            </div>
                            <div class="shortcut-item">
                                <span class="shortcut-key"><kbd>Ctrl</kbd> + <kbd>N</kbd></span>
                                <span class="shortcut-desc">New conversation</span>
                            </div>
                            <div class="shortcut-item">
                                <span class="shortcut-key"><kbd>Ctrl</kbd> + <kbd>Enter</kbd></span>
                                <span class="shortcut-desc">Send message</span>
                            </div>
                            <div class="shortcut-item">
                                <span class="shortcut-key"><kbd>Esc</kbd></span>
                                <span class="shortcut-desc">Close modal/Cancel</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h2>
                        <i class="fas fa-database"></i>
                        Data Management
                    </h2>
                    <div class="settings-card">
                        <div class="data-stats">
                            <div class="stat-item">
                                <i class="fas fa-comments"></i>
                                <span>${this.conversationService.getStats().totalConversations} Conversations</span>
                            </div>
                            <div class="stat-item">
                                <i class="fas fa-message"></i>
                                <span>${this.conversationService.getStats().totalMessages} Messages</span>
                            </div>
                            <div class="stat-item">
                                <i class="fas fa-hard-drive"></i>
                                <span>${this.getStorageSize()} Storage Used</span>
                            </div>
                        </div>
                        <div class="data-actions">
                            <button id="export-data" class="btn-secondary">
                                <i class="fas fa-download"></i>
                                Export All Data
                            </button>
                            <button id="import-data" class="btn-secondary">
                                <i class="fas fa-upload"></i>
                                Import Data
                            </button>
                            <button id="clear-all-data" class="btn-secondary danger">
                                <i class="fas fa-trash"></i>
                                Clear All Data
                            </button>
                        </div>
                    </div>
                </div>

                <div class="settings-section">
                    <h2>
                        <i class="fas fa-info-circle"></i>
                        About
                    </h2>
                    <div class="settings-card">
                        <div class="about-info">
                            <h3>IOC Agentic System</h3>
                            <p>Version 1.0.0</p>
                            <p>An intelligent orchestration system with function calling capabilities.</p>
                            <div class="about-links">
                                <a href="https://github.com/yourusername/akaAPIs" target="_blank">
                                    <i class="fab fa-github"></i> GitHub
                                </a>
                                <a href="/docs" target="_blank">
                                    <i class="fas fa-book"></i> Documentation
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="settings-actions">
                    <button id="save-settings" class="btn-primary">
                        <i class="fas fa-save"></i>
                        Save Settings
                    </button>
                    <button id="reset-settings" class="btn-secondary">
                        <i class="fas fa-undo"></i>
                        Reset to Defaults
                    </button>
                </div>
            </div>
        `;

        // Re-attach event listeners for dynamically created elements
        this.attachDynamicListeners();
    }

    /**
     * Attach event listeners to dynamically created elements
     */
    attachDynamicListeners() {
        document.getElementById('save-settings')?.addEventListener('click', () => this.saveAllSettings());
        document.getElementById('reset-settings')?.addEventListener('click', () => this.resetSettings());
        document.getElementById('export-data')?.addEventListener('click', () => this.exportAllData());
        document.getElementById('import-data')?.addEventListener('click', () => this.importData());
        document.getElementById('clear-all-data')?.addEventListener('click', () => this.clearAllData());
    }

    /**
     * Save all settings
     */
    saveAllSettings() {
        try {
            this.settings = {
                theme: document.getElementById('setting-theme')?.value || 'dark',
                fontSize: document.getElementById('setting-font-size')?.value || 'medium',
                animations: document.getElementById('setting-animations')?.checked || true,
                streamResponses: document.getElementById('setting-stream')?.checked || true,
                autoSaveConversations: document.getElementById('setting-auto-save')?.checked || true,
                soundEnabled: document.getElementById('setting-sound')?.checked || false,
                language: document.getElementById('setting-language')?.value || 'auto'
            };

            this.persistSettings();
            this.applySettings();
            this.ui.showToast('Settings saved successfully', 'success');
        } catch (error) {
            console.error('Error saving settings:', error);
            this.ui.showToast('Failed to save settings', 'error');
        }
    }

    /**
     * Reset settings to defaults
     */
    async resetSettings() {
        const confirmed = await this.ui.confirm(
            'Reset Settings',
            'Are you sure you want to reset all settings to defaults?'
        );

        if (confirmed) {
            this.settings = this.getDefaultSettings();
            this.persistSettings();
            this.applySettings();
            this.renderSettings();
            this.ui.showToast('Settings reset to defaults', 'success');
        }
    }

    /**
     * Export all data
     */
    exportAllData() {
        try {
            const data = {
                version: '1.0.0',
                exportedAt: new Date().toISOString(),
                conversations: this.state.getState('conversations') || [],
                settings: this.settings
            };

            const dataStr = JSON.stringify(data, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `ioc-backup-${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            this.ui.showToast('Data exported successfully', 'success');
        } catch (error) {
            console.error('Error exporting data:', error);
            this.ui.showToast('Failed to export data', 'error');
        }
    }

    /**
     * Import data
     */
    async importData() {
        try {
            const file = await this.ui.uploadFile('.json');
            if (!file) return;

            const text = await file.text();
            const data = JSON.parse(text);

            // Validate data structure
            if (!data.version || !data.conversations) {
                throw new Error('Invalid backup file format');
            }

            const confirmed = await this.ui.confirm(
                'Import Data',
                `This will import ${data.conversations.length} conversations. Continue?`
            );

            if (!confirmed) return;

            // Import conversations
            this.state.setState('conversations', data.conversations);
            this.conversationService.saveToLocalStorage(data.conversations);

            // Import settings if available
            if (data.settings) {
                this.settings = { ...this.getDefaultSettings(), ...data.settings };
                this.persistSettings();
                this.applySettings();
            }

            this.ui.showToast('Data imported successfully', 'success');
            this.renderSettings();
        } catch (error) {
            console.error('Error importing data:', error);
            this.ui.showToast('Failed to import data: ' + error.message, 'error');
        }
    }

    /**
     * Clear all data
     */
    async clearAllData() {
        const confirmed = await this.ui.confirm(
            'Clear All Data',
            'This will permanently delete all conversations and data. This action cannot be undone. Continue?',
            'danger'
        );

        if (confirmed) {
            await this.conversationService.clearAllConversations();
            this.ui.showToast('All data cleared', 'success');
            this.renderSettings();
        }
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            const stored = localStorage.getItem('ioc_settings');
            return stored ? { ...this.getDefaultSettings(), ...JSON.parse(stored) } : this.getDefaultSettings();
        } catch (error) {
            console.error('Error loading settings:', error);
            return this.getDefaultSettings();
        }
    }

    /**
     * Get default settings
     */
    getDefaultSettings() {
        return {
            theme: 'dark',
            fontSize: 'medium',
            animations: true,
            streamResponses: true,
            autoSaveConversations: true,
            soundEnabled: false,
            language: 'auto'
        };
    }

    /**
     * Persist settings to localStorage
     */
    persistSettings() {
        try {
            localStorage.setItem('ioc_settings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('Error persisting settings:', error);
        }
    }

    /**
     * Apply settings to the application
     */
    applySettings() {
        // Apply theme
        document.documentElement.setAttribute('data-theme', this.settings.theme);

        // Apply font size
        document.documentElement.style.fontSize = {
            small: '14px',
            medium: '16px',
            large: '18px'
        }[this.settings.fontSize] || '16px';

        // Apply animations
        if (!this.settings.animations) {
            document.documentElement.classList.add('no-animations');
        } else {
            document.documentElement.classList.remove('no-animations');
        }

        // Emit settings changed event
        document.dispatchEvent(new CustomEvent('settingsChanged', { detail: this.settings }));
    }

    /**
     * Get storage size
     */
    getStorageSize() {
        try {
            let total = 0;
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    total += localStorage[key].length + key.length;
                }
            }
            
            // Convert to KB/MB
            if (total < 1024) {
                return total + ' B';
            } else if (total < 1024 * 1024) {
                return (total / 1024).toFixed(2) + ' KB';
            } else {
                return (total / (1024 * 1024)).toFixed(2) + ' MB';
            }
        } catch (error) {
            return 'Unknown';
        }
    }

    /**
     * Get current settings
     */
    getSettings() {
        return { ...this.settings };
    }
}
