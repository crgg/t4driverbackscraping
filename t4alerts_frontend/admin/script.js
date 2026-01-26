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
        // Use ApiClient to fetch users
        const data = await ApiClient.get('/admin/users');

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

        // Note: ApiClient already handles 401/422 redirects automatically
        // So we only reach here for other errors (500, network issues, etc.)
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

    // Actions column
    const tdActions = document.createElement('td');
    tdActions.className = 'actions-cell';
    const changePasswordBtn = document.createElement('button');
    changePasswordBtn.className = 'btn-change-password';
    changePasswordBtn.textContent = '🔑 Change Password';
    changePasswordBtn.onclick = () => openChangePasswordModal(user);
    tdActions.appendChild(changePasswordBtn);
    tr.appendChild(tdActions);

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

        // Send update to backend using ApiClient
        const data = await ApiClient.put(`/admin/users/${userId}/permissions`, {
            permissions: newPermissions
        });

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

        // Extract error message from API response if available
        const errorMessage = error.response?.data?.msg || error.message;
        showToast(`Error: ${errorMessage}`, 'error');

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

/**
 * Open create user modal
 */
function openCreateUserModal() {
    const modal = document.getElementById('createUserModal');
    document.getElementById('createUserForm').reset();
    modal.style.display = 'flex';
}

/**
 * Close create user modal
 */
function closeCreateUserModal() {
    const modal = document.getElementById('createUserModal');
    modal.style.display = 'none';
    document.getElementById('createUserForm').reset();
}

/**
 * Handle create user form submission
 */
async function handleCreateUser(event) {
    event.preventDefault();
    
    const email = document.getElementById('newUserEmail').value.trim();
    const password = document.getElementById('newUserPassword').value;
    const confirmPassword = document.getElementById('newUserConfirmPassword').value;
    const role = document.getElementById('newUserRole').value;
    
    // Validate passwords match
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    // Validate password length
    if (password.length < 4) {
        showToast('Password must be at least 4 characters long', 'error');
        return;
    }
    
    // Validate email
    if (!email || !email.includes('@')) {
        showToast('Please enter a valid email address', 'error');
        return;
    }
    
    try {
        T4Logger.info(`Creating new user: ${email} with role: ${role}`);
        
        // Send request to backend
        const data = await ApiClient.post('/admin/users', {
            email: email,
            password: password,
            role: role
        });
        
        T4Logger.info(`✅ User created successfully: ${email}`);
        showToast(`User ${email} created successfully`, 'success');
        
        // Close modal
        closeCreateUserModal();
        
        // Reload users list
        await loadUsers();
        
    } catch (error) {
        T4Logger.error(`Failed to create user: ${error.message}`);
        
        // Extract error message from API response if available
        const errorMessage = error.response?.data?.msg || error.response?.data?.error || error.message;
        showToast(`Error: ${errorMessage}`, 'error');
    }
}

/**
 * Open change password modal
 */
let currentPasswordUserId = null;

function openChangePasswordModal(user) {
    currentPasswordUserId = user.id;
    const modal = document.getElementById('changePasswordModal');
    const userEmail = document.getElementById('modalUserEmail');
    
    userEmail.textContent = `User: ${user.email}`;
    document.getElementById('changePasswordForm').reset();
    
    modal.style.display = 'flex';
}

/**
 * Close change password modal
 */
function closeChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    modal.style.display = 'none';
    currentPasswordUserId = null;
    document.getElementById('changePasswordForm').reset();
}

/**
 * Handle change password form submission
 */
async function handleChangePassword(event) {
    event.preventDefault();
    
    if (!currentPasswordUserId) {
        showToast('Error: No user selected', 'error');
        return;
    }
    
    const password = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validate passwords match
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    // Validate password length
    if (password.length < 4) {
        showToast('Password must be at least 4 characters long', 'error');
        return;
    }
    
    try {
        T4Logger.info(`Changing password for user ${currentPasswordUserId}`);
        
        // Send request to backend
        await ApiClient.put(`/admin/users/${currentPasswordUserId}/password`, {
            password: password
        });
        
        T4Logger.info(`✅ Password changed successfully for user ${currentPasswordUserId}`);
        showToast('Password changed successfully', 'success');
        
        // Close modal
        closeChangePasswordModal();
        
    } catch (error) {
        T4Logger.error(`Failed to change password: ${error.message}`);
        
        // Extract error message from API response if available
        const errorMessage = error.response?.data?.msg || error.message;
        showToast(`Error: ${errorMessage}`, 'error');
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const createModal = document.getElementById('createUserModal');
    const passwordModal = document.getElementById('changePasswordModal');
    
    if (event.target === createModal) {
        closeCreateUserModal();
    }
    if (event.target === passwordModal) {
        closeChangePasswordModal();
    }
}
