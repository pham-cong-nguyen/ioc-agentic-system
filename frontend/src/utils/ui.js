/**
 * UI Manager - Handle UI operations and notifications
 */

export class UIManager {
    constructor() {
        this.toastContainer = document.getElementById('toastContainer');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.modalContainer = document.getElementById('modalContainer');
    }

    // =====================================================
    // Toast Notifications
    // =====================================================

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type} fade-in`;
        
        const icon = this.getToastIcon(type);
        
        toast.innerHTML = `
            <i class="${icon}"></i>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.toastContainer.appendChild(toast);

        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.closeToast(toast);
        });

        // Auto close
        setTimeout(() => {
            this.closeToast(toast);
        }, duration);
    }

    closeToast(toast) {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    getToastIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // =====================================================
    // Loading Overlay
    // =====================================================

    showLoading(message = 'Processing...') {
        if (this.loadingOverlay) {
            const messageEl = this.loadingOverlay.querySelector('p');
            if (messageEl) {
                messageEl.textContent = message;
            }
            this.loadingOverlay.classList.add('active');
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('active');
        }
    }

    // =====================================================
    // Modal Dialogs
    // =====================================================

    showModal(title, content, actions = []) {
        const modal = document.createElement('div');
        modal.className = 'modal fade-in';
        
        const actionsHTML = actions.map(action => `
            <button class="btn-${action.type || 'secondary'}" data-action="${action.action}">
                ${action.icon ? `<i class="${action.icon}"></i>` : ''}
                ${action.label}
            </button>
        `).join('');

        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-dialog scale-in">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="btn-icon modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${actionsHTML}
                </div>
            </div>
        `;

        this.modalContainer.appendChild(modal);

        // Setup event handlers
        return new Promise((resolve) => {
            const closeModal = (result) => {
                modal.classList.add('fade-out');
                setTimeout(() => {
                    modal.remove();
                }, 300);
                resolve(result);
            };

            // Close button
            modal.querySelector('.modal-close').addEventListener('click', () => {
                closeModal(null);
            });

            // Backdrop click
            modal.querySelector('.modal-backdrop').addEventListener('click', () => {
                closeModal(null);
            });

            // Action buttons
            modal.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = e.currentTarget.dataset.action;
                    closeModal(action);
                });
            });
        });
    }

    showConfirm(title, message) {
        return this.showModal(title, `<p>${message}</p>`, [
            { label: 'Cancel', action: 'cancel', type: 'secondary' },
            { label: 'Confirm', action: 'confirm', type: 'primary' }
        ]);
    }

    showAlert(title, message) {
        return this.showModal(title, `<p>${message}</p>`, [
            { label: 'OK', action: 'ok', type: 'primary' }
        ]);
    }

    // =====================================================
    // Utility Methods
    // =====================================================

    formatDate(date) {
        const d = new Date(date);
        const now = new Date();
        const diff = now - d;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        
        return d.toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    formatTime(date) {
        return new Date(date).toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success', 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            this.showToast('Failed to copy', 'error');
        }
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    async readJSONFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const json = JSON.parse(e.target.result);
                    resolve(json);
                } catch (error) {
                    reject(new Error('Invalid JSON file'));
                }
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    async uploadFile(accept = '*') {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = accept;
            input.onchange = (e) => {
                const file = e.target.files[0];
                resolve(file || null);
            };
            input.click();
        });
    }

    formatRelativeTime(date) {
        const d = new Date(date);
        const now = new Date();
        const diff = now - d;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        if (days < 30) return `${Math.floor(days / 7)}w ago`;
        if (days < 365) return `${Math.floor(days / 30)}mo ago`;
        return `${Math.floor(days / 365)}y ago`;
    }
}
