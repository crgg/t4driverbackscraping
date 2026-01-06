// T4 Alerts v2.1 Dashboard Script
// Now includes Stats Manager with Accordion Support

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
                // Return to overview if no state or root /errors/
                const pathParts = window.location.pathname.split('/');
                const pathAppKey = pathParts[2]; // /errors/APP_KEY

                if (pathAppKey) {
                    // If manually navigated back to a URL with app key but no state object
                    // We'll let loadAppsList handle it or just reload
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
            // Using debug endpoint to bypass auth for testing
            const response = await fetch(T4Config.getEndpoint('stats_apps_debug'));
            const data = await response.json();

            // The debug endpoint returns {status, count, apps}
            const apps = data.apps || data;

            console.log("APPS LOADED:", apps);

            this.appsListContainer.innerHTML = '';

            // Check for initial URL routing
            const pathParts = window.location.pathname.split('/');
            // Expected format: /errors/APP_KEY
            const initialAppKey = pathParts.length > 2 && pathParts[1] === 'errors' ? pathParts[2] : null;
            let initialAppFound = false;

            apps.forEach(app => {
                const item = document.createElement('div');
                item.className = 'sub-nav-item';
                item.innerText = app.name;

                // If this is the app from URL, mark it found
                if (initialAppKey && app.key === initialAppKey) {
                    item.classList.add('active'); // Pre-highlight
                    initialAppFound = true;
                }

                item.onclick = () => this.selectApp(app.key, app.name, item);
                this.appsListContainer.appendChild(item);
            });

            // If we have an initial app key from URL, load it
            if (initialAppFound) {
                const appName = apps.find(a => a.key === initialAppKey).name;
                this.selectApp(initialAppKey, appName, document.querySelector(`.sub-nav-item.active`), false);
            }

        } catch (error) {
            console.error("STATS LOAD ERROR:", error);
            T4Logger.error("Failed to load apps list", error);
            this.appsListContainer.innerHTML = `<div class="sub-nav-item" style="color:red">Error: ${error.message}</div>`;
        }
    }

    selectApp(appKey, appName, element, updateHistory = true) {
        // UI Update
        document.querySelectorAll('.sub-nav-item').forEach(el => el.classList.remove('active'));
        if (element) {
            element.classList.add('active');
        } else {
            // Try to find the element if not passed (e.g. from popstate)
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

        // Switch Views
        this.dashboardOverview.style.display = 'none';
        this.feedContainer.style.display = 'none'; // Hide feed when viewing specific app
        const historyView = document.getElementById('view-error-history');
        if (historyView) historyView.style.display = 'none';

        this.appViewContainer.style.display = 'block';

        // Update URL
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
    }

    async loadAppStats(appKey) {
        const loadingEl = document.getElementById('loading');
        loadingEl.style.display = 'block';
        loadingEl.innerHTML = '🔄 Scraping logs in real-time... (this may take 3-5 seconds)';

        try {
            // TEMPORARY: Using debug endpoint without JWT until auth is fixed
            // const token = localStorage.getItem('t4_access_token');
            // const baseUrl = T4Config.getEndpoint('stats_view');
            // const response = await fetch(`${baseUrl}/${appKey}?date=${this.currentDate}`, {
            //     headers: { 'Authorization': `Bearer ${token}` }
            // });

            // Using debug endpoint (no auth needed)
            const baseUrl = 'http://localhost:5001/api/stats/debug/view';
            const startTime = Date.now();

            const response = await fetch(`${baseUrl}/${appKey}?date=${this.currentDate}`);

            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            console.log(`⏱️ Scraping took ${elapsed} seconds`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // ENHANCED LOGGING FOR DEBUGGING
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`✅ Stats loaded for: ${appKey}`);
            console.log(`📅 Date: ${this.currentDate}`);
            console.log(`⏱️  Scraping time: ${elapsed}s`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('📊 UNCONTROLLED ERRORS:');
            console.log(`   Total unique signatures: ${data.logs.uncontrolled.length}`);
            if (data.logs.uncontrolled.length > 0) {
                console.log('   First 3 errors:');
                data.logs.uncontrolled.slice(0, 3).forEach((log, idx) => {
                    console.log(`     ${idx + 1}. [${log.timestamp}] ${log.message.substring(0, 60)}... (x${log.count})`);
                });
            } else {
                console.log('   ⚠️  No uncontrolled errors found for this date');
            }
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('📊 CONTROLLED ERRORS:');
            console.log(`   Total unique signatures: ${data.logs.controlled.length}`);
            if (data.logs.controlled.length > 0) {
                console.log('   First 3 errors:');
                data.logs.controlled.slice(0, 3).forEach((log, idx) => {
                    console.log(`     ${idx + 1}. [${log.timestamp}] ${log.message.substring(0, 60)}... (x${log.count})`);
                });
            } else {
                console.log('   ⚠️  No controlled errors found for this date');
            }
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`📈 SQL Stats: ${data.stats.sql_errors} SQL errors, ${data.stats.non_sql_errors} non-SQL errors`);
            console.log(`🔍 Data source: ${data.source || 'unknown'}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            this.renderLogs(data.logs);
            this.renderStatsChart(data.stats);
        } catch (error) {
            console.error('❌ Stats load error:', error);
            T4Logger.error("Failed to load app stats", error);
            document.getElementById('logs-uncontrolled').innerHTML =
                `<div style="color: red; padding: 20px;">
                    <strong>Error loading stats</strong><br>
                    ${error.message}<br><br>
                    <em>Make sure the backend is running and the app credentials are configured.</em>
                </div>`;
        } finally {
            loadingEl.style.display = 'none';
            loadingEl.innerHTML = 'Fetching data...'; // Reset for next time
        }
    }

    renderLogs(logs) {
        const renderList = (list, containerId, isControlled) => {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            if (list.length === 0) {
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
        row.className = 'history-item'; // Reuses existing table styles

        const summary = document.createElement('div');
        summary.className = 'history-summary';
        // Override grid layout for this specific view to maximize space
        summary.style.display = 'flex';
        summary.style.alignItems = 'center';
        summary.style.gap = '15px';

        // Timestamp - Extract precise time from message if possible (fixes 00:00:00 issue)
        let displayTimestamp = log.timestamp;
        const timeMatch = (log.message || '').match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
        if (timeMatch) {
            displayTimestamp = timeMatch[1];
        }

        const dateEl = document.createElement('div');
        dateEl.className = 'history-date';
        dateEl.style.minWidth = '140px';
        dateEl.innerText = displayTimestamp;

        // Message Preview
        const previewEl = document.createElement('div');
        previewEl.className = 'history-preview';
        previewEl.style.flex = '1';
        previewEl.innerText = escapeHtml(log.message);
        if (isControlled) previewEl.style.color = '#aaa';

        // Count Badge
        const countEl = document.createElement('div');
        countEl.className = 'app-badge'; // Reuse badge style
        countEl.style.background = isControlled ? 'rgba(255, 191, 0, 0.1)' : 'rgba(255, 0, 85, 0.1)';
        countEl.style.color = isControlled ? '#ffbf00' : '#ff0055';
        countEl.style.borderColor = isControlled ? 'rgba(255, 191, 0, 0.3)' : 'rgba(255, 0, 85, 0.3)';
        countEl.innerText = `x${log.count}`;

        // === 3-DOT MENU LOGIC ===
        const menuContainer = document.createElement('div');
        menuContainer.className = 'menu-container';

        const menuBtn = document.createElement('button');
        menuBtn.className = 'menu-btn';
        menuBtn.innerHTML = '&#8942;'; // Vertical ellipsis
        menuBtn.title = 'Options';

        const dropdown = document.createElement('div');
        dropdown.className = 'menu-dropdown';

        // Use a data attribute to store the message safely.
        // We need to escape double quotes for the attribute value.
        const safeMessage = log.message.replace(/"/g, '&quot;');

        dropdown.innerHTML = `
            <button class="menu-item" 
                    data-full-content="${safeMessage}"
                    onclick="sendErrorEmail(event, '${displayTimestamp}', this)">
                📧 Send Email
            </button>
        `;

        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent accordion toggle

            // Close other open menus
            document.querySelectorAll('.menu-dropdown.show').forEach(d => {
                if (d !== dropdown) d.classList.remove('show');
            });

            dropdown.classList.toggle('show');
        });

        // Close menu when clicking elsewhere
        window.addEventListener('click', (e) => {
            if (!menuContainer.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        menuContainer.appendChild(menuBtn);
        menuContainer.appendChild(dropdown);
        // =========================

        summary.appendChild(dateEl);
        summary.appendChild(previewEl);
        summary.appendChild(countEl);
        summary.appendChild(menuContainer);

        // Detail View (Accordion)
        const detail = document.createElement('div');
        detail.className = 'history-detail';
        detail.innerHTML = `
            <div class="history-detail-content">
                <pre class="code-block">${escapeHtml(log.message)}</pre>
            </div>
        `;

        // Toggle Logic
        summary.addEventListener('click', (e) => {
            // Ignore clicks on menu
            if (menuContainer.contains(e.target)) return;

            const isOpen = row.classList.contains('active');

            // Optional: Close others in the same container? 
            // Let's keep multiple open support for comparison

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

        // Prepare data for bar chart
        const sqlstateData = stats.sqlstate_distribution || [];

        // Check if there are any SQLSTATE errors
        if (sqlstateData.length === 0) {
            // Destroy existing chart if any
            if (window.currentSqlChart) {
                window.currentSqlChart.destroy();
                window.currentSqlChart = null;
            }

            // Show simple message
            container.style.height = 'auto'; // Collapse height when empty
            container.innerHTML =
                '<div style="color: #888; text-align: center; padding: 40px 20px; font-size: 14px;">' +
                'No SQLSTATE errors found for this date' +
                '</div>' +
                '<canvas id="sqlChart"></canvas>';
            return;
        }

        // If there IS data, make sure we have a clean canvas
        // First, destroy any existing chart
        if (window.currentSqlChart) {
            window.currentSqlChart.destroy();
            window.currentSqlChart = null;
        }

        // Ensure container only has the canvas (remove any fallback messages)
        container.style.height = '650px'; // Restore tall height for chart
        container.innerHTML = '<canvas id="sqlChart"></canvas>';

        // Get fresh canvas context
        const ctx = document.getElementById('sqlChart').getContext('2d');

        const labels = sqlstateData.map(item => item.sqlstate);
        const counts = sqlstateData.map(item => item.count);

        // Generate distinct colors for each SQLSTATE
        const colors = this.generateColors(labels.length);

        window.currentSqlChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Ocurrencias',
                    data: counts,
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace('0.7', '1')), // Full opacity for border
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribución de errores aparecidos durante el día',
                        color: '#fff',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: false  // Disable built-in legend, we'll create custom one
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: Math.max(...counts), // Use exact max value, no +1
                        ticks: {
                            color: '#ccc',
                            stepSize: Math.max(1, Math.ceil(Math.max(...counts) / 4)), // Max 5 ticks (0 + 4 steps)
                            callback: function (value) {
                                if (Number.isInteger(value)) {
                                    return value;
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: 'Cantidad de ocurrencias',
                            color: '#ccc',
                            font: { size: 13 }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ccc',
                            maxRotation: 45,
                            minRotation: 45,
                            font: { size: 11 }
                        },
                        title: {
                            display: true,
                            text: 'Código SQLSTATE',
                            color: '#ccc',
                            font: { size: 13 },
                            align: 'center'  // Center the title horizontally
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Create custom legend in a separate container
        this.renderCustomLegend(labels, counts, colors);
    }

    renderCustomLegend(labels, counts, colors) {
        // Create or get legend container
        let legendContainer = document.getElementById('sqlstate-legend');
        if (!legendContainer) {
            // Create new legend container next to the chart
            const statsView = document.getElementById('view-stats');
            legendContainer = document.createElement('div');
            legendContainer.id = 'sqlstate-legend';
            legendContainer.className = 'chart-card small';
            legendContainer.innerHTML = '<h3 style="margin-top: 0; color: #ccc; font-size: 14px;">SQLSTATE Codes</h3><div id="legend-items"></div>';
            statsView.appendChild(legendContainer);
        }

        const itemsContainer = document.getElementById('legend-items');
        itemsContainer.innerHTML = '';

        labels.forEach((label, i) => {
            const item = document.createElement('div');
            item.style.cssText = 'display: flex; align-items: center; margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 5px;';

            const colorBox = document.createElement('div');
            colorBox.style.cssText = `width: 20px; height: 20px; background: ${colors[i]}; border: 2px solid ${colors[i].replace('0.7', '1')}; border-radius: 3px; margin-right: 10px; flex-shrink: 0;`;

            const text = document.createElement('span');
            text.style.cssText = 'color: #ccc; font-size: 13px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;';
            text.title = label; // Show full text on hover
            text.textContent = label;

            const count = document.createElement('span');
            count.style.cssText = 'color: #00f3ff; font-weight: bold; font-size: 14px; margin-left: 10px;';
            count.textContent = `×${counts[i]}`;

            item.appendChild(colorBox);
            item.appendChild(text);
            item.appendChild(count);
            itemsContainer.appendChild(item);
        });
    }

    // Helper function to generate distinct colors
    generateColors(count) {
        const baseColors = [
            'rgba(255, 0, 85, 0.7)',    // Neon Red
            'rgba(0, 243, 255, 0.7)',   // Neon Blue
            'rgba(188, 19, 254, 0.7)',  // Neon Purple
            'rgba(255, 215, 0, 0.7)',   // Gold
            'rgba(50, 205, 50, 0.7)',   // Lime Green
            'rgba(255, 105, 180, 0.7)', // Hot Pink
            'rgba(0, 255, 127, 0.7)',   // Spring Green
            'rgba(255, 140, 0, 0.7)',   // Dark Orange
            'rgba(138, 43, 226, 0.7)',  // Blue Violet
            'rgba(255, 20, 147, 0.7)',  // Deep Pink
        ];

        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
        return colors;
    }
}

// Global functions for HTML interaction
window.toggleAccordion = async function (id) {
    const content = document.getElementById(id);
    const header = document.getElementById('accordion-stats');

    // If it's open, close it
    if (content.style.maxHeight) {
        content.style.maxHeight = null;
        header.classList.remove('active');
        return;
    }

    // It is opening
    header.classList.add('active');

    // 1. Lazy load apps if not already loaded
    if (!window.appsLoaded) {
        // Show loading state if needed, or just await
        if (window.statsManager) {
            await window.statsManager.loadAppsList();
            window.appsLoaded = true;
        }
    }

    // 2. Set height AFTER content is definitely there
    // We can use a slight timeout or just set it now that await is done
    content.style.maxHeight = content.scrollHeight + "px";
};

window.switchTab = function (tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    document.getElementById('view-logs').style.display = tabName === 'logs' ? 'flex' : 'none';
    document.getElementById('view-stats').style.display = tabName === 'stats' ? 'grid' : 'none';
};

class DashboardView {
    constructor() {
        // Initialize Stats Manager only (no ErrorAnalyzer needed)
    }

    async init() {
        // Show overview by default (hidden initially, shown when needed)
        document.getElementById('dashboard-overview').style.display = 'none';
        document.getElementById('feed-container').style.display = 'none';

        // Initialize Stats Manager
        window.statsManager = new StatsManager();

        console.log('Dashboard initialized successfully');
    }

    renderOverview(data) {
        // Reuse render logic for main dashboard
        // Note: We need to define renderBarChart/renderDonutChart similar to before
        // For brevity in this replace, assuming those methods exist or we re-instantiate them.
        // Actually, to avoid breaking, I should encompass the full original logic + new stats.

        // ... (Re-implementing chart rendering for overview)
        this.renderBarChart(data.barData);
        this.renderDonutChart(data.donutData);
        this.renderFeed(data.feedData);
    }

    renderBarChart(data) {
        const ctx = document.getElementById('barChart').getContext('2d');
        // ... (chart config same as before) ...
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(i => i.label),
                datasets: [{
                    label: 'Errors',
                    data: data.map(i => i.value),
                    backgroundColor: '#00f3ff'
                }]
            },
            options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    }

    renderDonutChart(data) {
        const ctx = document.getElementById('donutChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(i => i.label),
                datasets: [{
                    data: data.map(i => i.value),
                    backgroundColor: ['#ff0055', '#00f3ff', '#bc13fe']
                }]
            }
        });
    }

    renderFeed(data) {
        const container = document.getElementById('feed-list');
        container.innerHTML = '';
        data.forEach(item => {
            // Try to extract precise time from signature/content if timestamp is just the date
            let displayTime = new Date(item.timestamp).toLocaleTimeString();
            const timeMatch = (item.signature || '').match(/(\d{2}:\d{2}:\d{2})/);
            if (timeMatch) {
                displayTime = timeMatch[1];
            }

            const div = document.createElement('div');
            div.className = 'feed-item';
            div.innerHTML = `
                <div style="color: #00f3ff">${item.app}</div>
                <div title="${item.signature}">${item.signature.substring(0, 50)}...</div>
                <div>${displayTime}</div>
                <div><span style="color:#ff0055">${item.recurrence}</span></div>
             `;
            container.appendChild(div);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Current date display (moved from view logic to global init)
    document.getElementById('current-date').innerText = new Date().toLocaleDateString();
    new DashboardView().init();
});

// --- ERROR HISTORY MODULE ---
// --- ERROR HISTORY MODULE ---
window.historyData = [];
window.historySort = { col: 'first_seen', asc: false }; // Default sort by date desc

window.loadErrorHistory = async function () {
    const historyList = document.getElementById('history-list');
    const loading = document.getElementById('history-loading');

    historyList.innerHTML = '';
    loading.style.display = 'block';

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(`${window.T4Config.getEndpoint('error_history')}?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load history');
        }

        const data = await response.json();
        window.historyData = data; // Store globally for sorting

        loading.style.display = 'none';

        if (window.historyData.length === 0) {
            historyList.innerHTML = '<div style=\"text-align:center; padding: 20px; color:#888;\">No historical errors found.</div>';
            return;
        }

        renderHistory();

    } catch (err) {
        console.error(err);
        loading.style.display = 'none';
        historyList.innerHTML = `<div style="color:red; padding:20px;">Error: ${err.message}</div>`;
    }
};

window.sortHistory = function (col) {
    // If clicking same column, toggle direction
    if (window.historySort.col === col) {
        window.historySort.asc = !window.historySort.asc;
    } else {
        window.historySort.col = col;
        window.historySort.asc = true; // Default asc for new col
    }
    renderHistory();
};

window.renderHistory = function () {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';

    // Sort Data
    const { col, asc } = window.historySort;
    window.historyData.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];

        // Handling nulls
        if (valA == null) valA = "";
        if (valB == null) valB = "";

        // Case insensitive string sort
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return asc ? -1 : 1;
        if (valA > valB) return asc ? 1 : -1;
        return 0;
    });

    // Update Headers (Arrows)
    ['app_name', 'first_seen'].forEach(c => {
        const arrowEl = document.getElementById(`sort-${c}`);
        if (arrowEl) {
            arrowEl.innerText = '';
            if (col === c) {
                arrowEl.innerText = asc ? '▲' : '▼';
            }
        }
    });

    // Render Items
    window.historyData.forEach(item => {
        const row = document.createElement('div');
        row.className = 'history-item';

        // Convert ISO date to local time
        // item.first_seen comes as "2025-12-29T15:30:00" (ISOish)
        // If it was naive UTC from backend, new Date(item.first_seen + 'Z') might be needed if no Z provided.
        // Assuming backend sends simplistic ISO. Let's try parsing it directly.
        // If backend sends "2025-12-29T15:00:00", browser assumes local unless Z present.
        // Actually, best practice is to treat backend dates as UTC if not specified.
        // However, standard DB timestamp often lacks timezone.
        // Let's assume the string from backend IS valid for Date constructor.

        let displayDate = item.first_seen;

        // Content-based override for consistency
        // If the error content has a timestamp, use it for display
        const contentTimeMatch = (item.error_content || '').match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
        try {
            if (contentTimeMatch) {
                displayDate = contentTimeMatch[1];
            } else if (item.first_seen) {
                const d = new Date(item.first_seen);
                // Format: YYYY-MM-DD HH:MM:SS
                displayDate = d.toLocaleString('sv-SE'); // ISO-like format locally
            }
        } catch (e) { console.error("Date parse error", e); }

        const summary = document.createElement('div');
        summary.className = 'history-summary';
        summary.innerHTML = `
            <div><span class=\"app-badge\">${escapeHtml(item.app_name)}</span></div>
            <div class=\"history-date\">${displayDate}</div>
            <div class=\"history-preview\">${escapeHtml(item.error_content)}</div>
        `;

        // Detail
        const detail = document.createElement('div');
        detail.className = 'history-detail';
        detail.innerHTML = `
            <div class=\"history-detail-content\">
                    <pre class=\"code-block\">${escapeHtml(item.error_content)}</pre>
                </div>
            `;

        // Accordion Click
        summary.addEventListener('click', () => {
            const isOpen = row.classList.contains('active');

            // Close all others (optional)
            document.querySelectorAll('.history-item.active').forEach(r => {
                r.classList.remove('active');
                r.querySelector('.history-detail').style.maxHeight = null;
            });

            if (!isOpen) {
                row.classList.add('active');
                detail.style.maxHeight = detail.scrollHeight + "px";
            }
        });

        row.appendChild(summary);
        row.appendChild(detail);
        historyList.appendChild(row);
    });

};

// Helper for XSS prevention
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// --- GLOBAL SCAN MODULE ---
window.scanAllApps = async function () {
    const dateInput = document.getElementById('history-scan-date');
    const statusDiv = document.getElementById('scan-status');
    const dateVal = dateInput.value || new Date().toISOString().split('T')[0];

    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '⚡ Scanning all apps... this takes a while...';
    statusDiv.style.color = 'var(--neon-blue)';

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(window.T4Config.getEndpoint('error_history_scan'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ date: dateVal })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Scan failed');
        }

        // Success
        statusDiv.innerHTML = `✅ Scan Complete! processed ${result.total_critical_errors_processed} errors. Refreshing list...`;
        statusDiv.style.color = 'var(--accent-green)';

        // Reload history to show new items
        setTimeout(() => {
            window.loadErrorHistory();
        }, 1000);

    } catch (err) {
        console.error(err);
        statusDiv.innerHTML = `❌ Error: ${err.message}`;
        statusDiv.style.color = 'var(--neon-red)';
    }
};

// Initialize date picker on load
document.addEventListener('DOMContentLoaded', () => {
    const d = new Date().toISOString().split('T')[0];
    const picker = document.getElementById('history-scan-date');
    if (picker && !picker.value) picker.value = d;
});

// --- EMAIL NOTIFICATION MODULE ---
// --- EMAIL MODAL MODULE ---
// Friendly Names Mapping (Matches Backend Config)
const APP_NAMES = {
    "driverapp_goto": "DRIVERAPP - GO 2 LOGISTICS",
    "goexperior": "DRIVERAPP - GOEXPERIOR",
    "klc": "T4APP - KLC",
    "accuratecargo": "T4APP - ACCURATECARGO",
    "broker_goto": "BROKERAPP - GO 2 LOGISTICS",
    "klc_crossdock": "CROSSDOCK - KLC",
    "t4tms_backend": "T4TMS - BACKEND"
};

// --- AUTH HELPER ---
window.handleAuthError = function (response) {
    if (response.status === 401) {
        openSessionExpiredModal();
        return true; // handled
    }
    return false; // not handled
};

window.openSessionExpiredModal = function () {
    document.getElementById('session-expired-modal').style.display = 'flex';
};

window.redirectToLogin = function () {
    // Determine login URL based on environment or hardcode
    // Usually it's just /login or the root
    window.location.href = '/login.html'; // Assuming there is a login page
};


// --- EMAIL MODAL MODULE ---
// State to hold current email context
window.currentEmailContext = null;

window.openEmailModal = function (event, timestamp, btn) {
    if (event) event.stopPropagation();

    // Close dropdown
    if (btn) btn.closest('.menu-dropdown').classList.remove('show');

    // Get error content from DATA ATTRIBUTE
    // We decode it because it is URI encoded to be attribute-safe
    let rawContent = "Error content not found.";
    const encodedContent = btn.getAttribute('data-full-content');

    if (encodedContent) {
        try {
            rawContent = decodeURIComponent(encodedContent);
        } catch (e) {
            console.error("Failed to decode error content", e);
            rawContent = "Error decoding content.";
        }
    }

    const appKey = window.statsManager.currentAppKey;

    // Resolve friendly name
    // If not found in map, fallback to appKey (maybe capitalized)
    const friendlyName = APP_NAMES[appKey] || appKey.replace(/_/g, ' ').toUpperCase();

    // Extract time from rawContent if possible to match what user sees
    let emailTimestamp = timestamp;
    const timeMatch = rawContent.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
    if (timeMatch) {
        emailTimestamp = timeMatch[1];
    }

    // Save context for submission
    window.currentEmailContext = { appKey, timestamp: emailTimestamp };

    // Pre-fill Modal
    document.getElementById('email-to').value = '';
    document.getElementById('email-subject').value = `Manual Alert: Error in ${friendlyName}`;
    document.getElementById('email-body').value =
        `MANUAL ALERT TRIGGERED

Application: ${friendlyName}
Time: ${emailTimestamp}

Error Content:
--------------------------------------------------
${rawContent}
--------------------------------------------------`;

    // Show Modal
    document.getElementById('email-modal').style.display = 'flex';
};

window.closeEmailModal = function () {
    document.getElementById('email-modal').style.display = 'none';
    window.currentEmailContext = null;

    const btn = document.getElementById('btn-submit-email');
    btn.innerHTML = 'Send Email';
    btn.disabled = false;
};

window.submitErrorEmail = async function () {
    const btn = document.getElementById('btn-submit-email');
    const recipients = document.getElementById('email-to').value;
    const subject = document.getElementById('email-subject').value;
    const bodyText = document.getElementById('email-body').value;

    if (!recipients) {
        alert("Please enter at least one recipient.");
        return;
    }

    // --- HTML FORMATTING LOGIC ---
    // Convert the plain text to the requested HTML format
    let htmlBody = escapeHtml(bodyText); // First, safety escape

    // Restore newlines as <br> placeholder
    htmlBody = htmlBody.replace(/\n/g, '<br>');

    // Apply bold to specific headers (MANUAL ALERT TRIGGERED)
    htmlBody = htmlBody.replace(/(MANUAL ALERT TRIGGERED)/g, '<strong>$1</strong>');

    // Apply Blue to metadata lines (Application: ..., Time: ...)
    htmlBody = htmlBody.replace(/(Application:.*?)<br>/g, '<span style="color: blue;">$1</span><br>');
    htmlBody = htmlBody.replace(/(Time:.*?)<br>/g, '<span style="color: blue;">$1</span><br>');

    // Apply Red & Bold to Error Content (Everything after the separator)
    if (htmlBody.includes('Error Content:')) {
        const parts = htmlBody.split('Error Content:');
        const preContent = parts[0];
        const postContent = parts[1];

        // We wrap postContent in div to ensure style applies to all of it
        htmlBody = `${preContent}
            <strong style="color: red;">Error Content:${postContent}</strong>`;
    }

    // Wrap in a div for global font
    htmlBody = `<div style="font-family: sans-serif; font-size: 14px; color: #000;">${htmlBody}</div>`;
    // -----------------------------

    btn.innerHTML = '⏳ Sending...';
    btn.disabled = true;

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(window.T4Config.getEndpoint('stats_send_email'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                recipients: recipients,
                subject: subject,
                body: htmlBody, // Send formatted HTML
                app_key: window.currentEmailContext ? window.currentEmailContext.appKey : null
            })
        });

        // Auth Check
        if (window.handleAuthError(response)) {
            btn.innerHTML = '⚠️ Session Expired';
            btn.disabled = false;
            return;
        }

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to send email');
        }

        // Success
        btn.innerHTML = '✅ Sent!';
        setTimeout(() => {
            closeEmailModal();
        }, 1000);

    } catch (err) {
        console.error(err);
        btn.innerHTML = '❌ Error';
        alert(`Failed to send email: ${err.message}`);
        btn.disabled = false;
    }
};

// Update the onclick handler in the dropdown to use openEmailModal
// We need to Monkey Patch or re-define sendErrorEmail to redirect to openEmailModal
// to avoid rewriting the big createAccordionLogItem function again if possible.
window.sendErrorEmail = window.openEmailModal;

// ===== CUSTOM SCAN HANDLER =====
document.addEventListener('DOMContentLoaded', () => {
    const customScanForm = document.getElementById('custom-scan-form');
    if (customScanForm) {
        customScanForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await executeCustomScan();
        });
    }
});

async function executeCustomScan() {
    const btn = document.getElementById('btn-start-scan');
    const resultsContainer = document.getElementById('custom-scan-results');

    // Get form values
    const baseUrl = document.getElementById('scan-base-url').value.trim();
    const loginPath = document.getElementById('scan-login-path').value.trim();
    const logsPath = document.getElementById('scan-logs-path').value.trim();
    const username = document.getElementById('scan-username').value;
    const password = document.getElementById('scan-password').value;
    const date = document.getElementById('scan-date').value;

    // Disable button
    btn.disabled = true;
    btn.innerHTML = '⏳ Scanning...';

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(`${window.T4Config.API_BASE_URL}/stats/scan-adhoc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                base_url: baseUrl,
                login_path: loginPath,
                logs_path: logsPath,
                username: username,
                password: password,
                date: date
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Scan failed');
        }

        const data = await response.json();
        console.log('Custom scan completed', data);

        // Show results container
        resultsContainer.style.display = 'block';

        // Render results using existing table rendering logic
        renderCustomScanResults(data);

        btn.innerHTML = '✅ Scan Complete';
        setTimeout(() => {
            btn.innerHTML = '🚀 Start Scan';
            btn.disabled = false;
        }, 2000);

    } catch (error) {
        console.error('Custom scan error:', error);
        alert(`Scan failed: ${error.message}`);
        btn.innerHTML = '🚀 Start Scan';
        btn.disabled = false;
    }
}

function renderCustomScanResults(data) {
    const resultsContainer = document.getElementById('custom-scan-results');

    // Clear previous results
    resultsContainer.innerHTML = '<h3>Scan Results</h3>';

    // Create containers for each error type
    const uncontrolledContainer = document.createElement('div');
    uncontrolledContainer.className = 'error-section';
    uncontrolledContainer.innerHTML = '<h4>Errors</h4>';

    const controlledContainer = document.createElement('div');
    controlledContainer.className = 'error-section';
    controlledContainer.innerHTML = '<h4>Errors (controlled)</h4>';

    // Render uncontrolled errors
    if (data.logs && data.logs.length > 0) {
        const uncontrolledList = document.createElement('div');
        uncontrolledList.className = 'logs-list';
        data.logs.forEach(logStr => {
            // Convert string to object expected by createAccordionLogItem
            const logObj = {
                message: logStr,
                count: 1,
                timestamp: '' // Function will extract timestamp from message
            };
            uncontrolledList.appendChild(window.createAccordionLogItem(logObj, false));
        });
        uncontrolledContainer.appendChild(uncontrolledList);
    } else {
        uncontrolledContainer.innerHTML += '<p>No uncontrolled errors found ✅</p>';
    }

    // Render controlled errors
    if (data.controlled && data.controlled.length > 0) {
        const controlledList = document.createElement('div');
        controlledList.className = 'logs-list';
        data.controlled.forEach(logStr => {
            // Convert string to object expected by createAccordionLogItem
            const logObj = {
                message: logStr,
                count: 1,
                timestamp: '' // Function will extract timestamp from message
            };
            controlledList.appendChild(window.createAccordionLogItem(logObj, true));
        });
        controlledContainer.appendChild(controlledList);
    } else {
        controlledContainer.innerHTML += '<p>No controlled errors found ✅</p>';
    }

    resultsContainer.appendChild(uncontrolledContainer);
    resultsContainer.appendChild(controlledContainer);
}

window.executeCustomScan = executeCustomScan;

// Expose to window
window.scanAllApps = window.scanAllApps;
window.sendErrorEmail = window.sendErrorEmail;
window.submitErrorEmail = window.submitErrorEmail;
window.closeEmailModal = window.closeEmailModal;

