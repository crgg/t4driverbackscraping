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

            const response = await fetch(T4Config.getEndpoint('certificates') + '/status', {
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

            // Build action buttons HTML (only for dynamic certificates)
            let actionsHTML = '';
            if (cert.is_dynamic && cert.id) {
                actionsHTML = `
                    <div class="cert-actions">
                        <button class="btn-edit" onclick="editCertificate(${cert.id}, '${cert.hostname}')">✏️ Edit</button>
                        <button class="btn-delete" onclick="deleteCertificate(${cert.id}, '${cert.hostname}')">🗑️ Delete</button>
                    </div>
                `;
            }

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
                ${actionsHTML}
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

    // Enter key support - must be inside DOMContentLoaded to ensure element exists
    const domainInput = document.getElementById('domainInput');
    if (domainInput) {
        domainInput.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                checkCertificate();
            }
        });
    }
});

// --- Modal & Check Logic ---

let currentCheckResult = null; // Store result to save later

function openCheckModal() {
    document.getElementById('checkModal').style.display = 'block';
    document.getElementById('domainInput').value = '';
    document.getElementById('checkResult').style.display = 'none';
    document.getElementById('domainInput').focus();
}

function closeCheckModal() {
    document.getElementById('checkModal').style.display = 'none';
}

// Close modal when clicking outside
window.addEventListener('click', function (event) {
    const modal = document.getElementById('checkModal');
    if (event.target === modal) {
        modal.style.display = "none";
    }
});

async function checkCertificate() {
    const domain = document.getElementById('domainInput').value.trim();
    if (!domain) {
        alert("Please enter a domain");
        return;
    }

    const resultDiv = document.getElementById('checkResult');
    const msgP = document.getElementById('resultMessage');
    const btnSave = document.getElementById('btnSave');

    // Show loading state
    msgP.innerHTML = "Checking...";
    msgP.style.color = "#ccc";
    resultDiv.style.display = 'block';
    btnSave.style.display = 'none';

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(T4Config.getEndpoint('certificates') + '/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ hostname: domain })
        });

        const data = await response.json();

        if (!response.ok) {
            msgP.innerHTML = `Error: ${data.error || 'Unknown error'}`;
            msgP.style.color = "red";
            currentCheckResult = null;
        } else {
            // Update UI with result
            const daysLeft = data.days_left;
            const status = data.status;
            let color = data.color || 'white';

            msgP.innerHTML = `
                <strong style="color:${color}">${status}</strong><br>
                Days Left: <strong>${daysLeft}</strong><br>
                Expires: ${data.expires}<br>
                Issuer: ${data.issuer}
            `;

            // Allow saving if valid result
            if (status !== 'ERROR') {
                btnSave.style.display = 'inline-block';
                currentCheckResult = data;
            } else {
                currentCheckResult = null;
            }
        }
    } catch (e) {
        msgP.innerHTML = `Error: ${e.message}`;
        msgP.style.color = "red";
    }
}

async function saveCertificate() {
    if (!currentCheckResult) return;

    // We save the original hostname typed (or cleaned one returned?)
    // Ideally usage of returned hostname is safer
    const hostname = currentCheckResult.hostname;

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(T4Config.getEndpoint('certificates') + '/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ hostname: hostname })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Certificate saved successfully!");
            closeCheckModal();
            // Refresh list
            new CertificatesView().init();
        } else {
            alert(`Failed to save: ${data.error || data.message}`);
        }
    } catch (e) {
        alert(`Error saving: ${e.message}`);
    }
}

/**
 * Delete a certificate
 */
async function deleteCertificate(certId, hostname) {
    if (!confirm(`Are you sure you want to delete the certificate for "${hostname}"?`)) {
        return;
    }

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(T4Config.getEndpoint('certificates') + `/${certId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            alert("Certificate deleted successfully!");
            // Refresh list
            new CertificatesView().init();
        } else {
            alert(`Failed to delete: ${data.error || data.message}`);
        }
    } catch (e) {
        alert(`Error deleting: ${e.message}`);
    }
}

/**
 * Edit a certificate
 */
function editCertificate(certId, currentHostname) {
    document.getElementById('editModal').style.display = 'block';
    document.getElementById('editHostnameInput').value = currentHostname;
    document.getElementById('editCertId').value = certId;
    document.getElementById('editHostnameInput').focus();
}

/**
 * Close edit modal
 */
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

/**
 * Save edited certificate
 */
async function saveEditedCertificate() {
    const certId = document.getElementById('editCertId').value;
    const newHostname = document.getElementById('editHostnameInput').value.trim();

    if (!newHostname) {
        alert("Please enter a hostname");
        return;
    }

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(T4Config.getEndpoint('certificates') + `/${certId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ hostname: newHostname })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Certificate updated successfully!");
            closeEditModal();
            // Refresh list
            new CertificatesView().init();
        } else {
            alert(`Failed to update: ${data.error || data.message}`);
        }
    } catch (e) {
        alert(`Error updating: ${e.message}`);
    }
}

/**
 * Logout function
 */
function logout() {
    localStorage.removeItem('t4_access_token');
    window.location.href = '/login';
}
