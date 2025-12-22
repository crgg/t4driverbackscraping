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

        this.initDatePicker();
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
            apps.forEach(app => {
                const item = document.createElement('div');
                item.className = 'sub-nav-item';
                item.innerText = app.name;
                item.onclick = () => this.selectApp(app.key, app.name, item);
                this.appsListContainer.appendChild(item);
            });
        } catch (error) {
            console.error("STATS LOAD ERROR:", error);
            T4Logger.error("Failed to load apps list", error);
            this.appsListContainer.innerHTML = `<div class="sub-nav-item" style="color:red">Error: ${error.message}</div>`;
        }
    }

    selectApp(appKey, appName, element) {
        // UI Update
        document.querySelectorAll('.sub-nav-item').forEach(el => el.classList.remove('active'));
        element.classList.add('active');

        this.currentAppKey = appKey;
        this.pageTitle.innerText = `Stats: ${appName}`;

        // Switch Views
        this.dashboardOverview.style.display = 'none';
        this.feedContainer.style.display = 'none'; // Hide feed when viewing specific app
        this.appViewContainer.style.display = 'block';

        this.loadAppStats(appKey);
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
        const renderList = (list, containerId) => {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            if (list.length === 0) {
                container.innerHTML = '<div class="log-item">No logs found for this date.</div>';
                return;
            }

            list.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-item';
                // matches user request: "2025-12-19 ... - Message (xCount)"
                div.innerHTML = `
                    <span class="log-timestamp">${log.timestamp}</span> — 
                    ${log.message}
                    <span class="log-count">(x${log.count})</span>
                `;
                container.appendChild(div);
            });
        };

        renderList(logs.uncontrolled, 'logs-uncontrolled');
        renderList(logs.controlled, 'logs-controlled');
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
                'Sin errores SQLSTATE en esta fecha' +
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
            text.style.cssText = 'color: #ccc; font-size: 13px; flex: 1;';
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
window.toggleAccordion = function (id) {
    const content = document.getElementById(id);
    const header = document.getElementById('accordion-stats');
    if (content.style.maxHeight) {
        content.style.maxHeight = null;
        header.classList.remove('active');
    } else {
        content.style.maxHeight = content.scrollHeight + "px";
        header.classList.add('active');
        // Lazy load apps if not already
        if (!window.appsLoaded) {
            window.statsManager.loadAppsList();
            window.appsLoaded = true;
        }
    }
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
            const div = document.createElement('div');
            div.className = 'feed-item';
            div.innerHTML = `
                <div style="color: #00f3ff">${item.app}</div>
                <div title="${item.signature}">${item.signature.substring(0, 50)}...</div>
                <div>${new Date(item.timestamp).toLocaleTimeString()}</div>
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
