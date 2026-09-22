document.addEventListener('DOMContentLoaded', () => {
    // Determine user role and ID from DOM or meta tags if available,
    // otherwise fallback to fetching notifications anyway (endpoint validates session).
    
    const notifBadge = document.getElementById('notificationBadge') || document.getElementById('mobileNotifBadge') || document.getElementById('msbNotifDot');
    const notifList = document.getElementById('notificationList') || document.getElementById('mobileNotificationList');
    const markAllBtn = document.getElementById('markAllReadBtn') || document.getElementById('mobileMarkAllReadBtn');
    
    if (!notifBadge || !notifList) return;

    // Fetch initial notifications
    fetchNotifications();

    // Setup Pusher for live notification updates
    if (typeof pusher !== 'undefined') {
        const currentUserId = document.querySelector('meta[name="current-user-id"]')?.content;
        
        // Listen for admin events
        const adminChannel = pusher.subscribe('admin-notifications');
        adminChannel.bind('new-event-request', (data) => {
            // Show toast and refresh list
            showNotificationToast('New Event Request', data.title);
            fetchNotifications();
        });

        // Listen for faculty events if applicable
        if (currentUserId && currentUserId !== 'null') {
            const facultyChannel = pusher.subscribe(`faculty-${currentUserId}-alerts`);
            facultyChannel.bind('notification-received', (data) => {
                showNotificationToast('Notification Update', data.message);
                fetchNotifications();
            });
        }
    }

    if (markAllBtn) {
        markAllBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/notifications/mark-all-read', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
                });
                if (res.ok) fetchNotifications();
            } catch (err) {
                console.error('Failed to mark all as read:', err);
            }
        });
    }

    async function fetchNotifications() {
        try {
            const res = await fetch('/api/notifications/recent');
            const result = await res.json();
            
            if (result.success) {
                updateBadge(result.unread_count);
                renderNotificationList(result.data);
            }
        } catch (err) {
            console.error('Failed to fetch notifications:', err);
        }
    }

    function updateBadge(count) {
        // Update Desktop Badge
        const deskBadge = document.getElementById('notificationBadge');
        if (deskBadge) {
            if (count > 0) {
                deskBadge.textContent = count > 99 ? '99+' : count;
                deskBadge.classList.remove('d-none');
            } else {
                deskBadge.classList.add('d-none');
            }
        }
        
        // Update Mobile Sidebar Dot
        const msbDot = document.getElementById('msbNotifDot');
        if (msbDot) {
            if (count > 0) msbDot.classList.remove('d-none');
            else msbDot.classList.add('d-none');
        }
        
        // Update Mobile Topbar Badge
        const mobBadge = document.getElementById('mobileNotifBadge');
        if (mobBadge) {
            if (count > 0) {
                mobBadge.textContent = count > 99 ? '99+' : count;
                mobBadge.classList.remove('d-none');
            } else {
                mobBadge.classList.add('d-none');
            }
        }
    }

    function renderNotificationList(notifications) {
        notifList.innerHTML = '';
        
        if (notifications.length === 0) {
            notifList.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <i class="bi bi-bell-slash fs-3 d-block mb-2"></i>
                    <small>No notifications right now.</small>
                </div>
            `;
            return;
        }

        notifications.forEach(notif => {
            const item = document.createElement('div');
            item.className = `p-3 border-bottom ${notif.is_read ? 'bg-white' : 'bg-light'}`;
            item.style.cursor = 'pointer';
            
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-1">
                    <strong class="text-dark" style="font-size: 0.85rem;">${notif.title}</strong>
                    ${!notif.is_read ? '<span class="badge bg-primary" style="font-size: 0.5rem;">NEW</span>' : ''}
                </div>
                <div class="text-muted" style="font-size: 0.8rem;">${notif.message}</div>
                <div class="text-secondary mt-1" style="font-size: 0.7rem;">
                    ${new Date(notif.created_at).toLocaleString()}
                </div>
            `;
            
            item.addEventListener('click', async () => {
                if (!notif.is_read) {
                    try {
                        await fetch(`/api/notifications/${notif.id}/mark-read`, {
                            method: 'POST',
                            headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
                        });
                        fetchNotifications();
                    } catch (e) {
                        console.error('Mark read failed', e);
                    }
                }
                if (notif.link) {
                    window.location.href = notif.link;
                }
            });
            
            notifList.appendChild(item);
        });
    }

    function showNotificationToast(title, message) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 4000,
                timerProgressBar: true,
                icon: 'info',
                title: title,
                text: message,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                }
            });
        }
    }
});
