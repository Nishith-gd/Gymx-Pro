/* =========================================================
   GymX Pro — main.js
   Sections:
     1. Dark Mode
     2. Delete Confirm Modal (shared helper)
     3. AJAX Attendance Check-Out
     4. AJAX Notification Mark-Read
     5. Client-side Form Validation
     6. Skeleton Loader (dashboard stat cards)
   ========================================================= */

/* ── 1. Dark Mode ──────────────────────────────────────── */
(function () {
    const STORAGE_KEY = 'gymx-theme';

    function applyTheme(dark) {
        document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
        const btn = document.getElementById('darkModeToggle');
        if (btn) {
            btn.querySelector('i').className = dark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
            btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
            btn.setAttribute('title', dark ? 'Light mode' : 'Dark mode');
        }
    }

    function isDark() {
        return localStorage.getItem(STORAGE_KEY) === 'dark';
    }

    // Apply on page load immediately to avoid flash
    applyTheme(isDark());

    document.addEventListener('DOMContentLoaded', function () {
        // Re-apply in case the toggle button is now in the DOM
        applyTheme(isDark());

        const btn = document.getElementById('darkModeToggle');
        if (btn) {
            btn.addEventListener('click', function () {
                const nowDark = !isDark();
                localStorage.setItem(STORAGE_KEY, nowDark ? 'dark' : 'light');
                applyTheme(nowDark);
            });
        }
    });
})();


/* ── 2. Delete Confirm Modal ────────────────────────────── */
/**
 * Populates and shows the shared #deleteModal.
 * @param {string} url    - The POST URL for the delete action
 * @param {string} name   - Entity name shown in the modal body
 */
function confirmDelete(url, name) {
    const form = document.getElementById('deleteForm');
    const label = document.getElementById('deleteEntityName');
    if (!form || !label) return;
    form.action = url;
    label.textContent = name;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}


/* ── 3. AJAX Attendance Check-Out ───────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    // CSRF token exposed in <meta name="csrf-token">
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    document.querySelectorAll('[data-checkout-id]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const recordId = btn.getAttribute('data-checkout-id');
            const url = btn.getAttribute('data-checkout-url');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking out…';

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.ok) {
                    // Update the row in-place
                    const row = btn.closest('tr');
                    if (row) {
                        // Check-Out column
                        const checkOutCell = row.querySelector('[data-checkout-time]');
                        if (checkOutCell) checkOutCell.textContent = data.check_out;

                        // Duration column
                        const durationCell = row.querySelector('[data-duration]');
                        if (durationCell) durationCell.textContent = data.duration_mins + ' mins';

                        // Replace the button cell
                        const actionCell = btn.closest('td');
                        if (actionCell) actionCell.innerHTML = '<span class="badge bg-secondary">Checked Out</span>';
                    }
                } else {
                    btn.disabled = false;
                    btn.innerHTML = 'Check Out';
                    showToast(data.error || 'Check-out failed.', 'danger');
                }
            })
            .catch(function () {
                btn.disabled = false;
                btn.innerHTML = 'Check Out';
                showToast('Network error. Please try again.', 'danger');
            });
        });
    });
});


/* ── 4. AJAX Notification Mark-Read ─────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    document.querySelectorAll('[data-markread-url]').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const url = btn.getAttribute('data-markread-url');
            btn.disabled = true;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.ok) {
                    // Remove unread highlight from the notification item
                    const item = btn.closest('.list-group-item');
                    if (item) {
                        item.classList.remove('bg-light');
                        btn.closest('.d-flex.gap-2').removeChild(btn.parentElement || btn);
                    }
                } else {
                    btn.disabled = false;
                    showToast(data.error || 'Failed to mark as read.', 'danger');
                }
            })
            .catch(function () {
                btn.disabled = false;
                showToast('Network error.', 'danger');
            });
        });
    });
});


/* ── 5. Client-side Form Validation ─────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    // Bootstrap validation: add .was-validated on submit attempt
    document.querySelectorAll('form.needs-validation').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Password match validation for registration / password change fields
    const pwField = document.getElementById('password');
    const pw2Field = document.getElementById('confirm_password');
    if (pwField && pw2Field) {
        function checkMatch() {
            if (pw2Field.value && pwField.value !== pw2Field.value) {
                pw2Field.setCustomValidity('Passwords do not match.');
            } else {
                pw2Field.setCustomValidity('');
            }
        }
        pwField.addEventListener('input', checkMatch);
        pw2Field.addEventListener('input', checkMatch);
    }
});


/* ── 6. Skeleton Loader for Dashboard Stats ─────────────── */
document.addEventListener('DOMContentLoaded', function () {
    // Briefly show skeleton shimmer on stat cards, then reveal real data
    const statValues = document.querySelectorAll('.stat-value-real');
    if (statValues.length === 0) return;

    // Hide real values briefly
    statValues.forEach(function (el) {
        el.style.opacity = '0';
    });
    const skeletons = document.querySelectorAll('.stat-skeleton');
    skeletons.forEach(function (el) {
        el.classList.add('active');
    });

    // Reveal after a short delay (simulates async load; real data is already there)
    setTimeout(function () {
        skeletons.forEach(function (el) { el.classList.remove('active'); });
        statValues.forEach(function (el) {
            el.style.transition = 'opacity 0.4s ease';
            el.style.opacity = '1';
        });
    }, 400);
});


/* ── Utility: Toast Notification ────────────────────────── */
function showToast(message, type) {
    type = type || 'info';
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const id = 'toast-' + Date.now();
    const iconMap = {
        success: 'bi-check-circle-fill text-success',
        danger:  'bi-x-circle-fill text-danger',
        warning: 'bi-exclamation-triangle-fill text-warning',
        info:    'bi-info-circle-fill text-primary'
    };
    const icon = iconMap[type] || iconMap.info;

    container.insertAdjacentHTML('beforeend',
        '<div id="' + id + '" class="toast align-items-center border-0 show mb-2" role="alert" aria-live="assertive">' +
        '  <div class="d-flex">' +
        '    <div class="toast-body d-flex align-items-center gap-2">' +
        '      <i class="bi ' + icon + '"></i> ' + message +
        '    </div>' +
        '    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
        '  </div>' +
        '</div>'
    );

    setTimeout(function () {
        const el = document.getElementById(id);
        if (el) el.remove();
    }, 5000);
}
