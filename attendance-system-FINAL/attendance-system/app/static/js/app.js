/* AttendAI — app.js */

// ─── Toast Notifications ───────────────────────────────────────
function showToast(message, type = 'success') {
    const colors = { success: '#28a745', danger: '#dc3545', warning: '#ffc107', info: '#17a2b8' };
    const toast = document.createElement('div');
    toast.className = 'toast show align-items-center text-white border-0';
    toast.style.background = colors[type] || colors.success;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    const container = document.getElementById('toastContainer');
    if (container) {
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
}

// ─── Auto-dismiss flash alerts ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(a => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(a);
            bsAlert.close();
        });
    }, 5000);

    // Tooltip init
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });

    // PWA Install prompt
    setupPWA();
});

// ─── WebSocket real-time attendance updates ────────────────────
let socket = null;
function initSocket() {
    try {
        socket = io({ transports: ['websocket', 'polling'] });
        socket.on('attendance_updated', (data) => {
            showToast(`Attendance updated for course ${data.course_id}`, 'info');
        });
    } catch (e) {
        console.warn('Socket.IO not available:', e);
    }
}

// Only init socket on teacher pages
if (document.body.dataset.role === 'teacher' || document.body.dataset.role === 'admin') {
    initSocket();
}

// ─── Confirm delete helper ─────────────────────────────────────
function confirmDelete(msg) {
    return confirm(msg || 'Are you sure you want to delete this?');
}

// ─── PWA Service Worker ────────────────────────────────────────
function setupPWA() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    }

    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        const banner = document.getElementById('installBanner');
        if (banner) banner.style.display = 'block';
    });

    window.installPWA = () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(() => {
                deferredPrompt = null;
                const banner = document.getElementById('installBanner');
                if (banner) banner.style.display = 'none';
            });
        }
    };
}

// ─── Attendance page helpers ───────────────────────────────────
window.markAll = function(status) {
    document.querySelectorAll(`[id^="${status[0]}_"]`).forEach(r => r.checked = true);
    document.querySelectorAll('[id^="badge_"]').forEach(badge => {
        const sid = badge.id.replace('badge_', '');
        const colors = { present: 'success', absent: 'danger', late: 'warning text-dark' };
        badge.className = `status-indicator badge bg-${colors[status]}`;
        badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    });
};
