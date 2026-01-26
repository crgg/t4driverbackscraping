/**
 * Admin Panel JavaScript
 * Handles user listing and permission management
 */

let allUsers = [];

// Check if user is admin on page load
document.addEventListener('DOMContentLoaded', async () => {
    T4Logger.info("Admin panel loaded");

    // Check authentication
    const token = localStorage.getItem('t4_access_token');
    if (!token) {
        T4Logger.warn("No token found, redirecting to login");
        window.location.href = '/login';
        return;
    }

    // Check if user is admin
    if (!PermissionManager.isAdmin()) {
        T4Logger.warn("Non-admin user attempted to access admin panel");
        showToast("Access Denied: Admin privileges required", "error");
        setTimeout(() => {
            window.location.href = '/menu';
        }, 2000);
        return;
    }

    // Load users
    await loadUsers();
});

/**
 * Load all users from the backend
 */
async function loadUsers() {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const usersTable = document.getElementById('usersTable');

    // Show loading
    loadingState.style.display = 'flex';
    errorState.style.display = 'none';
    usersTable.style.display = 'none';

    try {
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(`${T4Config.API_BASE_URL}/admin/users`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            // Handle auth errors (expired or invalid token)
            if (response.status === 401 || response.status === 422) {
                T4Logger.warn("Session expired or invalid, redirecting to login");
                localStorage.removeItem('t4_access_token');
                window.location.href = '/login';
                return;
            }

            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        allUsers = data.users || [];

        T4Logger.info(`Loaded ${allUsers.length} users`);

        // Render users
        renderUsers();

        // Show table
        loadingState.style.display = 'none';
        usersTable.style.display = 'block';

    } catch (error) {
        T4Logger.error(`Failed to load users: ${error.message}`);

        loadingState.style.display = 'none';
        errorState.style.display = 'block';
    }
}

/**
 * Render users in the table
 */
function renderUsers() {
    const tbody = document.getElementById('usersTableBody');
    const userCount = document.getElementById('userCount');

    // Update count
    userCount.textContent = `${allUsers.length} user${allUsers.length !== 1 ? 's' : ''}`;

    // Clear existing rows
    tbody.innerHTML = '';

    // Create rows
    allUsers.forEach(user => {
        const row = createUserRow(user);
        tbody.appendChild(row);
    });
}

/**
 * Create a table row for a user
 */
function createUserRow(user) {
    const tr = document.createElement('tr');

    // Email
    const tdEmail = document.createElement('td');
    tdEmail.textContent = user.email;
    tr.appendChild(tdEmail);

    // Role
    const tdRole = document.createElement('td');
    const roleBadge = document.createElement('span');
    roleBadge.className = `role-badge role-${user.role}`;
    roleBadge.textContent = user.role.toUpperCase();
    tdRole.appendChild(roleBadge);
    tr.appendChild(tdRole);

    // Created date
    const tdDate = document.createElement('td');
    tdDate.className = 'date-cell';
    tdDate.textContent = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';
    tr.appendChild(tdDate);

    // Certificates permission
    const tdCerts = document.createElement('td');
    tdCerts.className = 'permission-toggle';
    const certsToggle = createToggle(
        user.id,
        'view_certificates',
        user.has_certificates_access,
        user.role === 'admin'
    );
    tdCerts.appendChild(certsToggle);
    tr.appendChild(tdCerts);

    // Errors permission
    const tdErrors = document.createElement('td');
    tdErrors.className = 'permission-toggle';
    const errorsToggle = createToggle(
        user.id,
        'view_errors',
        user.has_errors_access,
        user.role === 'admin'
    );
    tdErrors.appendChild(errorsToggle);
    tr.appendChild(tdErrors);

    return tr;
}

/**
 * Create a toggle switch for a permission
 */
function createToggle(userId, permissionName, isGranted, isAdmin) {
    const label = document.createElement('label');
    label.className = 'toggle-switch';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = isGranted;
    input.disabled = isAdmin; // Admins always have all permissions

    if (!isAdmin) {
        input.addEventListener('change', (e) => {
            handlePermissionToggle(userId, permissionName, e.target.checked);
        });
    }

    const span = document.createElement('span');
    span.className = 'toggle-slider';

    label.appendChild(input);
    label.appendChild(span);

    return label;
}

/**
 * Handle permission toggle change
 */
async function handlePermissionToggle(userId, permissionName, isGranted) {
    T4Logger.info(`Toggling ${permissionName} for user ${userId}: ${isGranted}`);

    try {
        // Find the user
        const user = allUsers.find(u => u.id === userId);
        if (!user) {
            throw new Error('User not found');
        }

        // Build new permissions array
        let newPermissions = [...user.permissions];

        if (isGranted) {
            // Add permission if not already present
            if (!newPermissions.includes(permissionName)) {
                newPermissions.push(permissionName);
            }
        } else {
            // Remove permission
            newPermissions = newPermissions.filter(p => p !== permissionName);
        }

        // Send update to backend
        const token = localStorage.getItem('t4_access_token');
        const response = await fetch(`${T4Config.API_BASE_URL}/admin/users/${userId}/permissions`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                permissions: newPermissions
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.msg || 'Failed to update permissions');
        }

        const data = await response.json();

        // Update local user data
        const userIndex = allUsers.findIndex(u => u.id === userId);
        if (userIndex !== -1) {
            allUsers[userIndex] = {
                ...allUsers[userIndex],
                permissions: newPermissions,
                has_certificates_access: newPermissions.includes('view_certificates'),
                has_errors_access: newPermissions.includes('view_errors')
            };
        }

        T4Logger.info(`✅ Permissions updated for user ${userId}`);
        showToast(`Permissions updated for ${user.email}`, 'success');

    } catch (error) {
        T4Logger.error(`Failed to update permissions: ${error.message}`);
        showToast(`Error: ${error.message}`, 'error');

        // Reload users to reset UI state
        await loadUsers();
    }
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;

    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
