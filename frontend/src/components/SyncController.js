/**
 * Sync Controller - Handle API Sync to PostgreSQL and Milvus
 */

export class SyncController {
    constructor(api, ui) {
        this.api = api;
        this.ui = ui;
        this.syncBtn = null;
        this.isSyncing = false;
        
        this.init();
    }

    init() {
        this.syncBtn = document.getElementById('syncApiBtn');
        if (this.syncBtn) {
            this.setupEventListeners();
            console.log('✅ SyncController initialized');
        } else {
            console.error('❌ Sync button not found');
        }
    }

    setupEventListeners() {
        this.syncBtn.addEventListener('click', () => {
            if (!this.isSyncing) {
                this.startSync();
            }
        });
    }

    /**
     * Start sync process
     */
    async startSync() {
        if (this.isSyncing) {
            console.log('⚠️ Sync already in progress');
            return;
        }

        console.log('🔄 Starting API sync...');
        this.isSyncing = true;
        
        // Change to syncing state
        this.setState('syncing');
        
        try {
            // Call CDC-based sync API to process pending events
            const response = await fetch('http://localhost:8862/api/v1/registry/sync/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Success state
                this.setState('success');
                this.ui.showToast(
                    `✅ Sync successful! ${result.synced_count || 0} functions synced to PostgreSQL and Milvus`,
                    'success'
                );
                
                console.log('✅ Sync completed:', result);
                
                // Reset to normal after 3 seconds
                setTimeout(() => {
                    this.resetState();
                }, 3000);
                
                // Trigger function list reload if on registry view
                this.triggerFunctionReload();
                
            } else {
                // Error state
                this.setState('error');
                this.ui.showToast(
                    `❌ Sync failed: ${result.message || 'Unknown error'}`,
                    'error'
                );
                
                console.error('❌ Sync failed:', result);
                
                // Reset to normal after 3 seconds
                setTimeout(() => {
                    this.resetState();
                }, 3000);
            }

        } catch (error) {
            // Network error
            this.setState('error');
            this.ui.showToast(
                `❌ Sync failed: ${error.message}`,
                'error'
            );
            
            console.error('❌ Sync error:', error);
            
            // Reset to normal after 3 seconds
            setTimeout(() => {
                this.resetState();
            }, 3000);
        } finally {
            this.isSyncing = false;
        }
    }

    /**
     * Set button state
     * @param {string} state - 'normal', 'syncing', 'success', 'error'
     */
    setState(state) {
        if (!this.syncBtn) return;

        // Remove all state classes
        this.syncBtn.classList.remove('syncing', 'success', 'error');
        
        // Get icon and text elements
        const icon = this.syncBtn.querySelector('i');
        const textEl = this.syncBtn.querySelector('.btn-text');
        
        switch (state) {
            case 'syncing':
                this.syncBtn.classList.add('syncing');
                this.syncBtn.disabled = true;
                if (icon) {
                    icon.className = 'fas fa-sync-alt';
                }
                if (textEl) {
                    textEl.textContent = 'Syncing';
                }
                break;
                
            case 'success':
                this.syncBtn.classList.add('success');
                this.syncBtn.disabled = false;
                if (icon) {
                    icon.className = 'fas fa-check';
                }
                if (textEl) {
                    textEl.textContent = 'Synced!';
                }
                break;
                
            case 'error':
                this.syncBtn.classList.add('error');
                this.syncBtn.disabled = false;
                if (icon) {
                    icon.className = 'fas fa-times';
                }
                if (textEl) {
                    textEl.textContent = 'Failed';
                }
                break;
                
            case 'normal':
            default:
                this.syncBtn.disabled = false;
                if (icon) {
                    icon.className = 'fas fa-sync-alt';
                }
                if (textEl) {
                    textEl.textContent = 'Sync API';
                }
                break;
        }
    }

    /**
     * Reset to normal state
     */
    resetState() {
        this.setState('normal');
    }

    /**
     * Trigger function list reload
     */
    triggerFunctionReload() {
        // Dispatch custom event for RegistryController to listen
        const event = new CustomEvent('functions-synced', {
            detail: { timestamp: Date.now() }
        });
        document.dispatchEvent(event);
    }

    /**
     * Check sync status (optional - for future use)
     */
    async checkSyncStatus() {
        try {
            const response = await fetch('http://localhost:8862/api/v1/registry/sync/status');
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Failed to check sync status:', error);
            return null;
        }
    }
}
