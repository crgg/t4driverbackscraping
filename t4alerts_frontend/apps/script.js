/**
 * App Manager - Frontend Logic
 * Handles CRUD operations for monitoring applications
 */

class AppManager {
    constructor() {
        this.apps = [];
        this.currentAppId = null;
        this.currentScanAppId = null;
        this.init();
    }

    async init() {
        // Check auth
        const token = localStorage.getItem('t4_access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        // Check admin permissions
        if (!window.PermissionManager || !window.PermissionManager.isAdmin()) {
            this.showError('Admin access required');
            setTimeout(() => window.location.href = '/menu', 2000);
            return;
        }

        // Set default scan date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('scan-date').value = today;

        // Load apps
        await this.loadApps();
    }

    async loadApps() {
        this.showLoading(true);
        try {
            const token = localStorage.getItem('t4_access_token');
            const response = await fetch(window.T4Config.getEndpoint('apps'), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                this.showSessionExpired();
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to load apps');
            }

            this.apps = await response.json();
            this.renderApps();
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading apps:', error);
            this.showError('Failed to load applications: ' + error.message);
            this.showLoading(false);
        }
    }

    renderApps() {
        const tbody = document.getElementById('apps-list');
        const tableContainer = document.getElementById('apps-table-container');
        const errorDiv = document.getElementById('error');

        errorDiv.style.display = 'none';

        if (this.apps.length === 0) {
            tableContainer.style.display = 'none';
            tableContainer.insertAdjacentHTML('afterend', `
                <div class="empty-state">
                    <h3>No apps configured yet</h3>
                    <p>Click "Add Application" to get started</p>
                </div>
            `);
            return;
        }

        tableContainer.style.display = 'block';
        tbody.innerHTML = this.apps.map(app => `
            <tr>
                <td><code>${app.app_key}</code></td>
                <td>${app.app_name}</td>
                <td>${app.base_url}</td>
                <td>
                    <span class="status-badge ${app.is_active ? 'status-active' : 'status-inactive'}">
                        ${app.is_active ? '✓ Active' : '✗ Inactive'}
                    </span>
                </td>
                <td>${new Date(app.created_at).toLocaleDateString()}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="appManager.openScanModal(${app.id}, '${app.app_name}')" title="Scan">
                            📅
                        </button>
                        <button class="btn-icon" onclick="appManager.openEditModal(${app.id})" title="Edit">
                            ✏️
                        </button>
                        <button class="btn-icon" onclick="appManager.deleteApp(${app.id}, '${app.app_name}')" title="Delete">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    openCreateModal() {
        this.currentAppId = null;
        document.getElementById('modal-title').textContent = 'Add Application';
        document.getElementById('app-form').reset();
        document.getElementById('app-id').value = '';
        document.getElementById('app-key').disabled = false; // Can edit key on create
        document.getElementById('app-modal').style.display = 'flex';
    }

    async openEditModal(appId) {
        this.currentAppId = appId;
        const app = this.apps.find(a => a.id === appId);

        if (!app) {
            this.showToast('App not found', 'error');
            return;
        }

        document.getElementById('modal-title').textContent = 'Edit Application';
        document.getElementById('app-id').value = app.id;
        document.getElementById('app-key').value = app.app_key;
        document.getElementById('app-key').disabled = true; // Can't change key
        document.getElementById('app-name').value = app.app_name;
        document.getElementById('base-url').value = app.base_url;
        document.getElementById('login-path').value = app.login_path;
        document.getElementById('logs-path').value = app.logs_path;
        document.getElementById('username').value = ''; // Don't populate for security
        document.getElementById('password').value = '';
        document.getElementById('is-active').checked = app.is_active;

        document.getElementById('app-modal').style.display = 'flex';
    }

    closeAppModal() {
        document.getElementById('app-modal').style.display = 'none';
        document.getElementById('app-form').reset();
        this.currentAppId = null;
    }

    async saveApp() {
        const form = document.getElementById('app-form');

        // Validate
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const data = {
            app_key: document.getElementById('app-key').value.trim(),
            app_name: document.getElementById('app-name').value.trim(),
            base_url: document.getElementById('base-url').value.trim(),
            login_path: document.getElementById('login-path').value.trim(),
            logs_path: document.getElementById('logs-path').value.trim(),
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            is_active: document.getElementById('is-active').checked
        };

        // Skip password if editing and field is empty
        if (this.currentAppId && !data.password) {
            delete data.password;
            delete data.username; // Don't update username either if password not provided
        }

        const saveBtn = document.getElementById('save-btn');
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const token = localStorage.getItem('t4_access_token');
            const url = this.currentAppId
                ? `${window.T4Config.getEndpoint('apps')}/${this.currentAppId}`
                : window.T4Config.getEndpoint('apps');

            const method = this.currentAppId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            if (response.status === 401) {
                this.showSessionExpired();
                return;
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to save app');
            }

            this.showToast(this.currentAppId ? 'App updated successfully' : 'App created successfully', 'success');
            this.closeAppModal();
            await this.loadApps();

        } catch (error) {
            console.error('Error saving app:', error);
            this.showToast('Error: ' + error.message, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save App';
        }
    }

    async deleteApp(appId, appName) {
        if (!confirm(`Are you sure you want to delete "${appName}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        try {
            const token = localStorage.getItem('t4_access_token');
            const response = await fetch(`${window.T4Config.getEndpoint('apps')}/${appId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                this.showSessionExpired();
                return;
            }

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.error || 'Failed to delete app');
            }

            this.showToast('App deleted successfully', 'success');
            await this.loadApps();

        } catch (error) {
            console.error('Error deleting app:', error);
            this.showToast('Error: ' + error.message, 'error');
        }
    }

    openScanModal(appId, appName) {
        this.currentScanAppId = appId;
        document.getElementById('scan-app-name').textContent = appName;
        document.getElementById('scan-modal').style.display = 'flex';
    }

    closeScanModal() {
        document.getElementById('scan-modal').style.display = 'none';
        this.currentScanAppId = null;
    }

    async executeScan() {
        const dateInput = document.getElementById('scan-date');

        if (!dateInput.value) {
            this.showToast('Please select a date', 'error');
            return;
        }

        const scanBtn = document.getElementById('scan-btn');
        scanBtn.disabled = true;
        scanBtn.textContent = '⏳ Scanning...';

        try {
            const token = localStorage.getItem('t4_access_token');
            const response = await fetch(`${window.T4Config.getEndpoint('apps')}/${this.currentScanAppId}/scan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    date: dateInput.value
                })
            });

            if (response.status === 401) {
                this.showSessionExpired();
                return;
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Scan failed');
            }

            this.showToast(`Scan completed! Found ${result.results.no_controlados_nuevos} new errors`, 'success');
            this.closeScanModal();

        } catch (error) {
            console.error('Error scanning app:', error);
            this.showToast('Scan error: ' + error.message, 'error');
        } finally {
            scanBtn.disabled = false;
            scanBtn.textContent = '🚀 Start Scan';
        }
    }

    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    showSessionExpired() {
        document.getElementById('session-expired-modal').style.display = 'flex';
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize
let appManager;
window.addEventListener('DOMContentLoaded', () => {
    appManager = new AppManager();
});

// Global functions for HTML onclick handlers
function openCreateModal() {
    appManager.openCreateModal();
}

function closeAppModal() {
    appManager.closeAppModal();
}

function saveApp() {
    appManager.saveApp();
}

function closeScanModal() {
    appManager.closeScanModal();
}

function executeScan() {
    appManager.executeScan();
}
