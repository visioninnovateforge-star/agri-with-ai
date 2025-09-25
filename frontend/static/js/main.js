// Main JavaScript for Agriculture Insights Platform

// Global functions and utilities
window.AgriInsights = {
    // API utilities
    api: {
        baseURL: '/api',
        
        async request(endpoint, options = {}) {
            const token = localStorage.getItem('token');
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),
                    ...options.headers
                },
                ...options
            });
            return response.json();
        }
    },

    // Chart utilities
    charts: {
        createChart(ctx, config) {
            return new Chart(ctx, config);
        }
    },

    // Form utilities
    forms: {
        serialize(form) {
            const formData = new FormData(form);
            return Object.fromEntries(formData);
        }
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Agriculture Insights Platform initialized');
});