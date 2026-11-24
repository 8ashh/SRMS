// Main JavaScript for MITS Academic Analytics & SRMS

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const appSidebar = document.getElementById('appSidebar');

    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
        });
    }

    // 2. Initialize Bootstrap Tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // 3. Auto-dismiss flash alerts after 5 seconds
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            if (alert && alert.parentElement) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            }
        }, 5000);
    });
});

// Confirmation helper for destructive actions (e.g. deletion)
function confirmDelete(message) {
    return confirm(message || "Are you sure you want to delete this record? This action cannot be undone.");
}
