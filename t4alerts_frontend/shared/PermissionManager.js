/**
 * PermissionManager - Utility for managing user permissions
 * Handles JWT token decoding and permission checking
 */

const PermissionManager = {
    /**
     * Decode JWT token and extract payload
     * @param {string} token - JWT token
     * @returns {object|null} - Decoded payload or null if invalid
     */
    decodeJWT(token) {
        try {
            if (!token) return null;

            const parts = token.split('.');
            if (parts.length !== 3) return null;

            const payload = parts[1];
            const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
            return JSON.parse(decoded);
        } catch (error) {
            console.error('Failed to decode JWT:', error);
            return null;
        }
    },

    /**
     * Get current user's JWT payload from localStorage
     * @returns {object|null} - JWT payload or null
     */
    getCurrentUserPayload() {
        const token = localStorage.getItem('t4_access_token');
        return this.decodeJWT(token);
    },

    /**
     * Check if current user is an admin
     * @returns {boolean} - True if admin, false otherwise
     */
    isAdmin() {
        const payload = this.getCurrentUserPayload();
        return payload && payload.role === 'admin';
    },

    /**
     * Get current user's role
     * @returns {string} - User role ('admin' or 'user')
     */
    getRole() {
        const payload = this.getCurrentUserPayload();
        return payload ? payload.role : 'user';
    },

    /**
     * Get list of current user's permissions
     * @returns {array} - Array of permission strings
     */
    getPermissions() {
        const payload = this.getCurrentUserPayload();
        return payload && payload.permissions ? payload.permissions : [];
    },

    /**
     * Check if current user has a specific permission
     * Admins automatically have all permissions
     * @param {string} permissionName - The permission to check
     * @returns {boolean} - True if user has permission, false otherwise
     */
    hasPermission(permissionName) {
        // Admins have all permissions
        if (this.isAdmin()) {
            return true;
        }

        const permissions = this.getPermissions();
        return permissions.includes(permissionName);
    },

    /**
     * Get current user's email
     * @returns {string|null} - User email or null
     */
    getUserEmail() {
        const payload = this.getCurrentUserPayload();
        return payload ? payload.email : null;
    },

    /**
     * Get current user's ID
     * @returns {number|null} - User ID or null
     */
    getUserId() {
        const payload = this.getCurrentUserPayload();
        return payload ? payload.sub : null;
    },

    /**
     * Check if token is expired
     * @returns {boolean} - True if expired, false otherwise
     */
    isTokenExpired() {
        const payload = this.getCurrentUserPayload();
        if (!payload || !payload.exp) return true;

        const now = Math.floor(Date.now() / 1000);
        return now >= payload.exp;
    },

    /**
     * Log user permissions for debugging
     */
    logPermissions() {
        const payload = this.getCurrentUserPayload();
        if (payload) {
            console.log('=== User Permissions ===');
            console.log('Email:', payload.email);
            console.log('Role:', payload.role);
            console.log('Permissions:', payload.permissions);
            console.log('Is Admin:', this.isAdmin());
            console.log('======================');
        } else {
            console.log('No valid token found');
        }
    }
};

// Make it available globally
window.PermissionManager = PermissionManager;
