class CertificatesView {
    constructor() {
        this.container = document.getElementById('certificates-grid');
        this.loading = document.getElementById('loading');
    }

    async init() {
        try {
            const token = localStorage.getItem('t4_access_token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch(T4Config.getEndpoint('certificates'), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to fetch certificates');

            const data = await response.json();

            // Sort Data: Critical/Error -> Warning -> OK
            // We'll use a numeric priority map
            const priority = {
                'ERROR': 0,
                'CRITICAL': 1,
                'WARNING': 2,
                'OK': 3
            };

            data.sort((a, b) => {
                const pA = priority[a.status] !== undefined ? priority[a.status] : 99;
                const pB = priority[b.status] !== undefined ? priority[b.status] : 99;

                // Primary Sort: Severity
                if (pA !== pB) {
                    return pA - pB;
                }

                // Secondary Sort: Days Left (Ascending) - closer to expiration first
                return a.days_left - b.days_left;
            });

            this.render(data);
        } catch (error) {
            T4Logger.error("Failed to load certificates", error);
            this.loading.innerText = "Error loading certificates. Please try again.";
            this.loading.style.color = "red";
        }
    }

    render(data) {
        this.loading.style.display = 'none';
        this.container.innerHTML = '';

        data.forEach((cert, index) => {
            const card = document.createElement('div');

            // Determine styling based on status
            let statusClass = 'status-ok';
            let cardClass = 'ok';

            if (cert.status === 'CRITICAL' || cert.status === 'ERROR') {
                statusClass = 'status-critical';
                cardClass = 'critical';
            } else if (cert.status === 'WARNING') {
                statusClass = 'status-warning';
                cardClass = 'warning';
            }

            card.className = `cert-card ${cardClass}`;
            card.style.opacity = '0';
            card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;

            card.innerHTML = `
                <div class="cert-header">
                    <div class="cert-hostname">${cert.hostname}</div>
                    <div class="cert-status ${statusClass}">${cert.status}</div>
                </div>
                <div class="cert-details">
                    <p><strong>Days Left:</strong> ${cert.days_left}</p>
                    <p><strong>Expires:</strong> ${cert.expires}</p>
                    <p><strong>Issuer:</strong> ${cert.issuer}</p>
                </div>
            `;

            this.container.appendChild(card);
        });
    }
}

// Add animation keyframes dynamically
const style = document.createElement('style');
style.innerHTML = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Initialize view
document.addEventListener('DOMContentLoaded', () => {
    new CertificatesView().init();
});

/**
 * Logout function
 */
function logout() {
    localStorage.removeItem('t4_access_token');
    window.location.href = '/login';
}
