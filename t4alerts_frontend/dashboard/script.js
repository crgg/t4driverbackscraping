// T4 Alerts v2.1 Dashboard Script

class StatsManager {
    constructor() {
        this.appsListContainer = document.getElementById('apps-list-container');
        this.appViewContainer = document.getElementById('app-view-container');
        this.dashboardOverview = document.getElementById('dashboard-overview');
        this.feedContainer = document.getElementById('feed-container');
        this.pageTitle = document.getElementById('page-title');
        this.currentAppKey = null;
        this.currentDate = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

        // Expose helper to window so custom scan can use it
        window.createAccordionLogItem = this.createAccordionLogItem.bind(this);

        this.initDatePicker();

        // Handle Back/Forward navigation
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.appKey) {
                this.selectApp(event.state.appKey, event.state.appName, null, false);
            } else {
                const pathParts = window.location.pathname.split('/');
                const pathAppKey = pathParts[2];

                if (pathAppKey) {
                    window.location.reload();
                } else {
                    this.showOverview();
                }
            }
        });
    }

    initDatePicker() {
        const picker = document.getElementById('stats-date-picker');
        if (picker) {
            picker.value = this.currentDate;
            picker.addEventListener('change', (e) => {
                this.currentDate = e.target.value;
                if (this.currentAppKey) {
                    this.loadAppStats(this.currentAppKey);
                }
            });
        }
    }

    async loadAppsList() {
        try {
            const response = await fetch(T4Config.getEndpoint('stats_apps_debug'));
            const data = await response.json();
            const apps = data.apps || data;

            this.appsListContainer.innerHTML = '';

            const pathParts = window.location.pathname.split('/');
            const initialAppKey = pathParts.length > 2 && pathParts[1] === 'errors' ? pathParts[2] : null;
            let initialAppFound = false;

            apps.forEach(app => {
                const item = document.createElement('div');
                item.className = 'sub-nav-item';
                item.innerText = app.name;

                if (initialAppKey && app.key === initialAppKey) {
                    item.classList.add('active');
                    initialAppFound = true;
                }

                item.onclick = () => this.selectApp(app.key, app.name, item);
                this.appsListContainer.appendChild(item);
            });

            if (initialAppFound) {
                const appName = apps.find(a => a.key === initialAppKey).name;
                this.selectApp(initialAppKey, appName, document.querySelector(`.sub-nav-item.active`), false);
            }

        } catch (error) {
            console.error("STATS LOAD ERROR:", error);
            this.appsListContainer.innerHTML = `<div class="sub-nav-item" style="color:red">Error: ${error.message}</div>`;
        }
    }

    selectApp(appKey, appName, element, updateHistory = true) {
        document.querySelectorAll('.sub-nav-item').forEach(el => el.classList.remove('active'));
        if (element) {
            element.classList.add('active');
        } else {
            const items = document.querySelectorAll('.sub-nav-item');
            for (const item of items) {
                if (item.innerText === appName) {
                    item.classList.add('active');
                    break;
                }
            }
        }

        this.currentAppKey = appKey;
        this.pageTitle.innerText = `Stats: ${appName}`;

        this.dashboardOverview.style.display = 'none';
        this.feedContainer.style.display = 'none';
        const historyView = document.getElementById('view-error-history');
        if (historyView) historyView.style.display = 'none';
        const customScanView = document.getElementById('custom-scan-view');
        if (customScanView) customScanView.style.display = 'none';

        this.appViewContainer.style.display = 'block';

        if (updateHistory) {
            const newUrl = `/errors/${appKey}`;
            window.history.pushState({ appKey, appName }, '', newUrl);
        }

        this.loadAppStats(appKey);
    }

    showOverview() {
        this.currentAppKey = null;
        this.pageTitle.innerText = 'Dashboard Overview';
        document.querySelectorAll('.sub-nav-item').forEach(el => el.classList.remove('active'));

        this.dashboardOverview.style.display = 'block';
        this.feedContainer.style.display = 'block';
        this.appViewContainer.style.display = 'none';
        const customScanView = document.getElementById('custom-scan-view');
        if (customScanView) customScanView.style.display = 'none';
    }

    async loadAppStats(appKey) {
        const loadingEl = document.getElementById('loading');
        loadingEl.style.display = 'block';
        loadingEl.innerHTML = '🔄 Scraping logs in real-time... (this may take 3-5 seconds)';

        try {
            const endpoint = `${window.T4Config.getEndpoint('stats_view')}/${appKey}`;
            const token = localStorage.getItem('t4_access_token');
            const response = await fetch(`${endpoint}?date=${this.currentDate}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errText}`);
            }

            const data = await response.json();
            window.cachedLogs = data.logs;
            window.cachedStats = data.stats;

        } catch (error) {
            console.error('❌ Stats load error:', error);
            document.getElementById('logs-uncontrolled').innerHTML =
                `<div style="color: red; padding: 20px;">
                    <strong>Error loading stats</strong><br>
                    ${error.message}
                </div>`;

        } finally {
            loadingEl.style.display = 'none';
            // Always render logs immediately
            this.renderLogs(window.cachedLogs || { uncontrolled: [], controlled: [] });

            // Only render chart if Stats tab is currently visible
            const statsView = document.getElementById('view-stats');
            if (statsView && statsView.style.display !== 'none') {
                // Wait for layout to fully stabilize before rendering chart
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        // Extra safety delay for complex layout changes
                        setTimeout(() => {
                            if (window.cachedStats) this.renderStatsChart(window.cachedStats);
                        }, 50);
                    });
                });
            }
        }
    }

    renderLogs(logs) {
        const renderList = (list, containerId, isControlled) => {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="log-item">No logs found for this date.</div>';
                return;
            }

            list.forEach(log => {
                const item = this.createAccordionLogItem(log, isControlled);
                container.appendChild(item);
            });
        };

        renderList(logs.uncontrolled, 'logs-uncontrolled', false);
        renderList(logs.controlled, 'logs-controlled', true);
    }

    createAccordionLogItem(log, isControlled) {
        const row = document.createElement('div');
        row.className = 'history-item';

        const summary = document.createElement('div');
        summary.className = 'history-summary';
        summary.style.display = 'flex';
        summary.style.alignItems = 'center';
        summary.style.gap = '15px';

        let displayTimestamp = log.timestamp || '00-00-00';
        const timeMatch = (log.message || '').match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
        if (timeMatch) displayTimestamp = timeMatch[1];

        const dateEl = document.createElement('div');
        dateEl.className = 'history-date';
        dateEl.style.minWidth = '140px';
        dateEl.innerText = displayTimestamp;

        const previewEl = document.createElement('div');
        previewEl.className = 'history-preview';
        previewEl.style.flex = '1';

        // Extract SQLSTATE for preview if it exists, otherwise show first 100 chars
        const sqlstateMatch = (log.message || '').match(/SQLSTATE\[(\w+)\]/);
        let previewText;
        if (sqlstateMatch) {
            previewText = `SQLSTATE[${sqlstateMatch[1]}]`;
        } else {
            // Show first 100 characters for non-SQL errors
            previewText = (log.message || '').substring(0, 100);
            if ((log.message || '').length > 100) previewText += '...';
        }
        previewEl.innerText = escapeHtml(previewText);
        if (isControlled) previewEl.style.color = '#aaa';

        const countEl = document.createElement('div');
        countEl.className = 'app-badge';
        countEl.style.background = isControlled ? 'rgba(255, 191, 0, 0.1)' : 'rgba(255, 0, 85, 0.1)';
        countEl.style.color = isControlled ? '#ffbf00' : '#ff0055';
        countEl.innerText = `x${log.count}`;

        const menuContainer = document.createElement('div');
        menuContainer.className = 'menu-container';

        const menuBtn = document.createElement('button');
        menuBtn.className = 'menu-btn';
        menuBtn.innerHTML = '&#8942;';

        const dropdown = document.createElement('div');
        dropdown.className = 'menu-dropdown';
        const safeMessage = log.message.replace(/"/g, '&quot;');
        dropdown.innerHTML = `
            <button class="menu-item" data-full-content="${safeMessage}" onclick="sendErrorEmail(event, '${displayTimestamp}', this)">
                📧 Send Email
            </button>
        `;

        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.menu-dropdown.show').forEach(d => { if (d !== dropdown) d.classList.remove('show'); });
            dropdown.classList.toggle('show');
        });

        window.addEventListener('click', (e) => { if (!menuContainer.contains(e.target)) dropdown.classList.remove('show'); });

        menuContainer.appendChild(menuBtn);
        menuContainer.appendChild(dropdown);

        summary.appendChild(dateEl);
        summary.appendChild(previewEl);
        summary.appendChild(countEl);
        summary.appendChild(menuContainer);

        const detail = document.createElement('div');
        detail.className = 'history-detail';
        detail.innerHTML = `<div class="history-detail-content"><pre class="code-block">${escapeHtml(log.message)}</pre></div>`;

        summary.addEventListener('click', (e) => {
            if (menuContainer.contains(e.target)) return;
            const isOpen = row.classList.contains('active');
            if (!isOpen) {
                row.classList.add('active');
                detail.style.maxHeight = detail.scrollHeight + "px";
            } else {
                row.classList.remove('active');
                detail.style.maxHeight = null;
            }
        });

        row.appendChild(summary);
        row.appendChild(detail);
        return row;
    }

    renderStatsChart(stats) {
        const container = document.getElementById('chart-container');
        if (!container) return;

        const sqlstateData = stats.sqlstate_distribution || [];
        if (sqlstateData.length === 0) {
            if (window.currentSqlChart) { window.currentSqlChart.destroy(); window.currentSqlChart = null; }
            container.style.height = 'auto';
            container.innerHTML = '<div style="color: #888; text-align: center; padding: 40px 20px;">No SQLSTATE errors found</div>';
            return;
        }

        if (window.currentSqlChart) window.currentSqlChart.destroy();
        container.style.height = '450px';
        container.innerHTML = '<canvas id="sqlChart"></canvas>';
        const ctx = document.getElementById('sqlChart').getContext('2d');

        const labels = sqlstateData.map(item => item.sqlstate);
        const counts = sqlstateData.map(item => item.count);
        const colors = this.generateColors(labels.length);

        window.currentSqlChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Occurrences',
                    data: counts,
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace('0.7', '1')),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                    x: { grid: { display: false }, ticks: { color: '#ccc', maxRotation: 45, minRotation: 45 } }
                }
            }
        });

        // Ensure it takes full size immediately
        setTimeout(() => {
            if (window.currentSqlChart) {
                window.currentSqlChart.resize();
                window.currentSqlChart.update();
            }
        }, 50);

        this.renderCustomLegend(labels, counts, colors);
    }

    renderCustomLegend(labels, counts, colors) {
        let legendContainer = document.getElementById('sqlstate-legend');
        if (!legendContainer) {
            const statsView = document.getElementById('view-stats');
            legendContainer = document.createElement('div');
            legendContainer.id = 'sqlstate-legend';
            legendContainer.className = 'chart-card small';
            legendContainer.innerHTML = '<h3>SQLSTATE Codes</h3><div id="legend-items"></div>';
            statsView.appendChild(legendContainer);
        }
        const itemsContainer = document.getElementById('legend-items');
        itemsContainer.innerHTML = '';
        labels.forEach((label, i) => {
            const item = document.createElement('div');
            item.style.cssText = 'display: flex; align-items: center; margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 5px;';
            item.innerHTML = `<div style="width: 20px; height: 20px; background: ${colors[i]}; margin-right: 10px; border-radius: 3px;"></div>
                              <span style="color: #ccc; flex: 1;">${label}</span>
                              <span style="color: #00f3ff; font-weight: bold;">×${counts[i]}</span>`;
            itemsContainer.appendChild(item);
        });
    }

    generateColors(count) {
        const base = ['rgba(255, 0, 85, 0.7)', 'rgba(0, 243, 255, 0.7)', 'rgba(188, 19, 254, 0.7)', 'rgba(255, 215, 0, 0.7)'];
        return Array.from({ length: count }, (_, i) => base[i % base.length]);
    }
}

// --- GLOBAL HELPERS ---
function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

window.toggleAccordion = async function (id) {
    const content = document.getElementById(id);
    const header = document.getElementById('accordion-stats');
    if (content.style.maxHeight) {
        content.style.maxHeight = null;
        header.classList.remove('active');
        return;
    }
    header.classList.add('active');
    if (!window.appsLoaded && window.statsManager) {
        await window.statsManager.loadAppsList();
        window.appsLoaded = true;
    }
    content.style.maxHeight = content.scrollHeight + "px";
};

window.switchTab = function (tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('view-logs').style.display = tabName === 'logs' ? 'flex' : 'none';
    document.getElementById('view-stats').style.display = tabName === 'stats' ? 'grid' : 'none';

    // When switching to stats, render or resize the chart
    if (tabName === 'stats') {
        // Use double RAF to ensure the display change has fully taken effect
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                if (window.cachedStats) {
                    // If chart exists, resize it. Otherwise, create it.
                    if (window.currentSqlChart) {
                        window.currentSqlChart.resize();
                        window.currentSqlChart.update();
                    } else if (window.statsManager) {
                        window.statsManager.renderStatsChart(window.cachedStats);
                    }
                }
            });
        });
    }
};

class DashboardView {
    async init() {
        document.getElementById('dashboard-overview').style.display = 'none';
        document.getElementById('feed-container').style.display = 'none';
        window.statsManager = new StatsManager();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const curDate = document.getElementById('current-date');
    if (curDate) curDate.innerText = new Date().toLocaleDateString();

    // Update User Role in Sidebar
    const roleDisplay = document.getElementById('user-role-display');
    if (roleDisplay && window.PermissionManager) {
        const role = window.PermissionManager.getRole();
        roleDisplay.innerText = role.charAt(0).toUpperCase() + role.slice(1);
    }

    new DashboardView().init();
});

// --- ERROR HISTORY ---
// --- ERROR HISTORY ---
window.historyData = [];
window.historyPage = 1;
window.historyPageSize = 20;
window.historySearchTerm = '';

window.loadErrorHistory = async function () {
    const list = document.getElementById('history-list');
    const load = document.getElementById('history-loading');
    const pag = document.getElementById('history-pagination');

    list.innerHTML = '';
    load.style.display = 'block';
    pag.style.display = 'none';

    try {
        const token = localStorage.getItem('t4_access_token');
        // Fetch up to 1000 records to allow decent client-side searching/paging
        const res = await fetch(`${window.T4Config.getEndpoint('error_history')}?limit=1000`, { headers: { 'Authorization': `Bearer ${token}` } });
        window.historyData = await res.json();

        load.style.display = 'none';

        if (window.historyData.length === 0) {
            list.innerHTML = '<div style="text-align:center; padding: 20px;">No errors found.</div>';
            return;
        }

        pag.style.display = 'flex';
        renderHistory();

    } catch (err) {
        load.style.display = 'none';
        list.innerHTML = `<div style="color:red; padding:20px;">Error: ${err.message}</div>`;
    }
};

window.sortHistory = function (col) {
    if (!window.historySort) window.historySort = { col: 'first_seen', asc: false };
    if (window.historySort.col === col) window.historySort.asc = !window.historySort.asc;
    else { window.historySort.col = col; window.historySort.asc = true; }
    renderHistory();
};

window.filterHistory = function () {
    const input = document.getElementById('history-search');
    window.historySearchTerm = input.value.toLowerCase();
    window.historyPage = 1; // Reset to first page on search
    renderHistory();
};

window.changeHistoryPage = function (delta) {
    window.historyPage += delta;
    renderHistory();
};

window.renderHistory = function () {
    const list = document.getElementById('history-list');
    const pageInfo = document.getElementById('history-page-info');
    list.innerHTML = '';

    // 1. Filter
    let filtered = window.historyData;
    if (window.historySearchTerm) {
        filtered = window.historyData.filter(item =>
            (item.app_name && item.app_name.toLowerCase().includes(window.historySearchTerm)) ||
            (item.error_content && item.error_content.toLowerCase().includes(window.historySearchTerm))
        );
    }

    // 2. Sort
    const { col, asc } = window.historySort || { col: 'first_seen', asc: false };
    filtered.sort((a, b) => {
        let vA = (a[col] || "").toString().toLowerCase();
        let vB = (b[col] || "").toString().toLowerCase();
        if (vA < vB) return asc ? -1 : 1;
        if (vA > vB) return asc ? 1 : -1;
        return 0;
    });

    // 3. Paginate
    const totalItems = filtered.length;
    const totalPages = Math.ceil(totalItems / window.historyPageSize) || 1;

    // Clamp page
    if (window.historyPage < 1) window.historyPage = 1;
    if (window.historyPage > totalPages) window.historyPage = totalPages;

    pageInfo.innerText = `Page ${window.historyPage} of ${totalPages} (${totalItems} items)`;

    const start = (window.historyPage - 1) * window.historyPageSize;
    const end = start + window.historyPageSize;
    const pageItems = filtered.slice(start, end);

    if (pageItems.length === 0) {
        list.innerHTML = '<div style="text-align:center; padding: 20px; color: #888;">No matching records found.</div>';
        return;
    }

    pageItems.forEach(item => {
        const row = document.createElement('div');
        row.className = 'history-item';
        let d = item.first_seen;
        const sum = document.createElement('div');
        sum.className = 'history-summary';
        sum.innerHTML = `<div><span class="app-badge">${escapeHtml(item.app_name)}</span></div><div class="history-date">${d}</div><div class="history-preview">${escapeHtml(item.error_content)}</div>`;
        const det = document.createElement('div');
        det.className = 'history-detail';
        det.innerHTML = `<div class="history-detail-content"><pre class="code-block">${escapeHtml(item.error_content)}</pre></div>`;
        sum.addEventListener('click', () => {
            const isOpen = row.classList.contains('active');
            document.querySelectorAll('.history-item.active').forEach(r => { r.classList.remove('active'); r.querySelector('.history-detail').style.maxHeight = null; });
            if (!isOpen) { row.classList.add('active'); det.style.maxHeight = det.scrollHeight + "px"; }
        });
        row.appendChild(sum);
        row.appendChild(det);
        list.appendChild(row);
    });
};


// REMOVED: scanAllApps() eliminada
// Razón: El endpoint /api/error-history/scan fue eliminado del backend.
// El error history se actualiza automáticamente cada vez que se hace scraping
// desde custom-scan o desde errors/[app] individual.


// --- EMAIL ---
window.openEmailModal = function (event, timestamp, btn) {
    if (event) event.stopPropagation();
    if (btn) btn.closest('.menu-dropdown').classList.remove('show');
    const encoded = btn.getAttribute('data-full-content');
    const content = encoded ? encoded : "No content";
    const appKey = window.statsManager.currentAppKey;
    window.currentEmailContext = { appKey, timestamp };
    document.getElementById('email-to').value = '';
    document.getElementById('email-subject').value = `Alert: Error in ${appKey}`;
    document.getElementById('email-body').value = `Time: ${timestamp}\n\nApp: ${appKey}\n\nContent:\n${content}`;
    document.getElementById('email-modal').style.display = 'flex';
};

window.closeEmailModal = function () { document.getElementById('email-modal').style.display = 'none'; };

window.submitErrorEmail = async function () {
    const btn = document.getElementById('btn-submit-email');
    const payload = {
        recipients: document.getElementById('email-to').value,
        subject: document.getElementById('email-subject').value,
        body: document.getElementById('email-body').value,
        app_key: window.currentEmailContext ? window.currentEmailContext.appKey : null
    };
    if (!payload.recipients) return alert("Recipient required");
    btn.innerText = 'Sending...';
    try {
        const token = localStorage.getItem('t4_access_token');
        const res = await fetch(window.T4Config.getEndpoint('stats_send_email'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(payload)
        });
        if (res.ok) { btn.innerText = 'Sent!'; setTimeout(closeEmailModal, 1000); }
        else throw new Error("Failed");
    } catch (e) { btn.innerText = 'Error'; alert(e.message); }
};

window.sendErrorEmail = window.openEmailModal;

// --- CUSTOM SCAN MODAL ---
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('custom-modal-form');
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); handleModalScanAndSave(); });

    const nameIn = document.getElementById('m-scan-app-name');
    const keyIn = document.getElementById('m-scan-app-key');
    if (nameIn && keyIn) {
        nameIn.addEventListener('input', (e) => {
            keyIn.value = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        });
    }

    const temp = document.getElementById('scan-template');
    if (temp) {
        populateTemplates(temp);
        temp.addEventListener('change', (e) => {
            const opt = e.target.options[e.target.selectedIndex];
            if (opt.dataset.app) fillCustomScanForm(JSON.parse(opt.dataset.app));
        });
    }

    const saveBtn = document.getElementById('btn-save-app');
    if (saveBtn) saveBtn.addEventListener('click', saveCurrentAppConfig);
});

window.openCustomScanModal = function () { document.getElementById('custom-scan-modal').style.display = 'flex'; };
window.closeCustomScanModal = function () { document.getElementById('custom-scan-modal').style.display = 'none'; };

async function handleModalScanAndSave() {
    const btn = document.getElementById('btn-modal-start');
    btn.disabled = true;
    btn.innerText = '⏳ Scanning...';
    try {
        const payload = {
            app_key: document.getElementById('m-scan-app-key').value.trim(),
            app_name: document.getElementById('m-scan-app-name').value.trim(),
            base_url: document.getElementById('m-scan-base-url').value.trim(),
            login_path: document.getElementById('m-scan-login-path').value.trim(),
            logs_path: document.getElementById('m-scan-logs-path').value.trim(),
            username: document.getElementById('m-scan-username').value.trim(),
            password: document.getElementById('m-scan-password').value,
            is_active: true
        };
        const date = document.getElementById('m-scan-date').value || new Date().toISOString().split('T')[0];
        await executeCustomScanFromPayload(payload, date);
        btn.innerText = '✅ Done';
        setTimeout(() => { closeCustomScanModal(); btn.disabled = false; btn.innerText = '🚀 Start Scan'; }, 800);
    } catch (e) { alert(e.message); btn.disabled = false; btn.innerText = '🚀 Start Scan'; }
}

async function saveCurrentAppConfig() {
    const saveBtn = document.getElementById('btn-save-app');
    const fields = ['m-scan-app-key', 'm-scan-app-name', 'm-scan-base-url', 'm-scan-login-path', 'm-scan-logs-path', 'm-scan-username', 'm-scan-password'];

    // Safety check
    for (const id of fields) {
        if (!document.getElementById(id)) {
            console.error("Missing element:", id);
            alert("Critical Error: Fields lost. Please reload.");
            return;
        }
    }

    const payload = {
        app_key: document.getElementById('m-scan-app-key').value.trim(),
        app_name: document.getElementById('m-scan-app-name').value.trim(),
        base_url: document.getElementById('m-scan-base-url').value.trim(),
        login_path: document.getElementById('m-scan-login-path').value.trim(),
        logs_path: document.getElementById('m-scan-logs-path').value.trim(),
        username: document.getElementById('m-scan-username').value.trim(),
        password: document.getElementById('m-scan-password').value,
        is_active: true
    };

    if (!payload.app_key || !payload.password) return alert("Key and Password required");

    saveBtn.innerText = '⏳ Saving...';
    try {
        const token = localStorage.getItem('t4_access_token');
        const res = await fetch(`${window.T4Config.API_BASE_URL}/apps/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(payload)
        });
        if (res.ok) { alert('✅ Saved!'); window.location.reload(); }
        else throw new Error("Save failed");
    } catch (e) { alert(e.message); saveBtn.innerText = '💾 Save & Add to Menu'; }
}

async function executeCustomScanFromPayload(payload, date) {
    document.getElementById('custom-scan-view').style.display = 'block';
    document.getElementById('custom-scan-empty').style.display = 'none';
    const res = document.getElementById('custom-scan-results');
    res.style.display = 'block';
    res.querySelector('h3').innerText = `Scanning ${payload.app_name}...`;
    const token = localStorage.getItem('t4_access_token');
    const apiRes = await fetch(`${window.T4Config.API_BASE_URL}/stats/scan-adhoc`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ ...payload, date })
    });
    if (!apiRes.ok) throw new Error("Scan failed");
    const data = await apiRes.json();
    renderCustomScanResults(data);
}

function populateTemplates(sel) {
    const token = localStorage.getItem('t4_access_token');
    fetch(`${window.T4Config.API_BASE_URL}/stats/apps`, { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json()).then(apps => {
            if (Array.isArray(apps)) apps.forEach(app => {
                const o = document.createElement('option'); o.value = app.key; o.innerText = app.name; o.dataset.app = JSON.stringify(app); sel.appendChild(o);
            });
        });
}

function fillCustomScanForm(app) {
    openCustomScanModal();
    document.getElementById('m-scan-app-key').value = app.key || '';
    document.getElementById('m-scan-app-name').value = app.name || '';
    document.getElementById('m-scan-base-url').value = app.base_url || '';
    document.getElementById('m-scan-login-path').value = app.login_path || '/login';
    document.getElementById('m-scan-logs-path').value = app.logs_path || '/logs';
    document.getElementById('m-scan-username').value = app.username || '';
}

function renderCustomScanResults(data) {
    document.getElementById('btn-save-app').style.display = 'block';
    const cont = document.getElementById('scan-results-content');
    cont.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'logs-grid';

    const createCol = (title, logs, controlled) => {
        const div = document.createElement('div');
        div.className = `log-group ${controlled ? 'controlled' : 'uncontrolled'}`;
        div.innerHTML = `<h3>${title}</h3>`;
        const list = document.createElement('div');
        list.className = 'log-list';
        if (logs && logs.length) logs.forEach(l => list.appendChild(window.createAccordionLogItem({ message: l, count: 1 }, controlled)));
        else list.innerHTML = '<div class="log-item">None found</div>';
        div.appendChild(list);
        return div;
    };

    grid.appendChild(createCol('Uncontrolled Errors', data.logs, false));
    grid.appendChild(createCol('Controlled Errors', data.controlled, true));
    cont.appendChild(grid);
}
