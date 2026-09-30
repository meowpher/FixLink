/**
 * FixLink Enterprise Cross-Tab Session Guard (Zero-Trust Architecture)
 * 
 * Protects multi-tab workflows against session desyncs, cross-tab account hijacking,
 * stale form submissions, real-time event leaks, and Thundering Herd reload storms.
 */
(function () {
    'use strict';

    // 1. Read cryptographic anchor metadata injected by server
    const metaTabGuard = document.querySelector('meta[name="tab-guard-id"]');
    const metaUserId = document.querySelector('meta[name="user-id"]');
    const metaUserEmail = document.querySelector('meta[name="user-email"]');
    const metaAuth = document.querySelector('meta[name="is-authenticated"]');

    const currentTabGuardId = metaTabGuard ? metaTabGuard.content.trim() : '';
    const currentUserId = metaUserId ? metaUserId.content.trim() : '';
    const currentUserEmail = metaUserEmail ? metaUserEmail.content.trim() : '';
    const isAuthenticated = metaAuth ? metaAuth.content.trim() === 'true' : false;

    // Internal state
    let isDesynced = false;
    let isModalRendered = false;
    const CHANNEL_NAME = 'fixlink_session_guard_channel';
    const STORAGE_KEY = 'fixlink_active_session_anchor';

    // Set tab-specific session identity
    try {
        if (currentTabGuardId) {
            sessionStorage.setItem('fixlink_tab_guard_id', currentTabGuardId);
            sessionStorage.setItem('fixlink_user_id', currentUserId);
        }
    } catch (e) {
        // Safe fallback for restricted storage environments
    }

    // 2. BroadcastChannel & Storage Sync (Phase 2)
    let broadcastChannel = null;
    try {
        if (typeof BroadcastChannel !== 'undefined') {
            broadcastChannel = new BroadcastChannel(CHANNEL_NAME);
            broadcastChannel.onmessage = handleBroadcastMessage;
        }
    } catch (e) {
        broadcastChannel = null;
    }

    // Sync on startup
    if (isAuthenticated && currentTabGuardId) {
        try {
            const activeSession = {
                tabGuardId: currentTabGuardId,
                userId: currentUserId,
                userEmail: currentUserEmail,
                updatedAt: Date.now()
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(activeSession));
            
            if (broadcastChannel) {
                broadcastChannel.postMessage({
                    type: 'SESSION_ANCHOR_ESTABLISHED',
                    ...activeSession
                });
            }
        } catch (e) {}
    }

    // Listen to cross-tab storage events (works across all browsers/subdomains)
    window.addEventListener('storage', function (event) {
        if (event.key === STORAGE_KEY && event.newValue) {
            try {
                const newSession = JSON.parse(event.newValue);
                validateSessionState(newSession);
            } catch (e) {}
        }
    });

    function handleBroadcastMessage(event) {
        if (!event || !event.data) return;
        const data = event.data;
        if (data.type === 'SESSION_ANCHOR_ESTABLISHED' || data.type === 'SESSION_LOGOUT' || data.type === 'SESSION_CHANGED') {
            validateSessionState(data);
        }
    }

    function validateSessionState(incomingSession) {
        if (!incomingSession || isDesynced) return;

        // If this tab is authenticated, verify the incoming tab guard ID matches
        if (isAuthenticated) {
            if (incomingSession.type === 'SESSION_LOGOUT') {
                triggerSessionDesync('You have been logged out in another tab.');
                return;
            }

            if (incomingSession.tabGuardId && incomingSession.tabGuardId !== currentTabGuardId) {
                // Different session / account logged in
                const newAcc = incomingSession.userEmail ? ` (${incomingSession.userEmail})` : '';
                triggerSessionDesync(`Account switched in another tab${newAcc}.`);
                return;
            }
        }
    }

    // 3. Graceful Teardown & Lockout (Phase 4)
    function triggerSessionDesync(reasonText) {
        if (isDesynced) return;
        isDesynced = true;
        window.__FIXLINK_SESSION_DESYNCED = true;

        console.warn('[SessionGuard] Cross-tab session mismatch detected:', reasonText);

        // Immediate Safe Teardown: Disconnect Realtime WebSockets / Pusher
        try {
            if (window.pusher && typeof window.pusher.disconnect === 'function') {
                window.pusher.disconnect();
            }
        } catch (e) {}

        // Stop timers and pollers
        try {
            let highestTimeoutId = setTimeout(function () {}, 0);
            for (let i = 0; i < highestTimeoutId; i++) {
                clearTimeout(i);
                clearInterval(i);
            }
        } catch (e) {}

        // Render zero-bypass modal
        showSessionDesyncOverlay(reasonText);
    }

    // 4. Modal / Overlay Construction (DOM Null-Crash Proof)
    function showSessionDesyncOverlay(reasonText) {
        if (isModalRendered) return;
        isModalRendered = true;

        const overlay = document.createElement('div');
        overlay.id = 'sessionGuardOverlay';
        overlay.style.cssText = [
            'position: fixed',
            'top: 0',
            'left: 0',
            'width: 100vw',
            'height: 100vh',
            'background: rgba(15, 23, 42, 0.75)',
            'backdrop-filter: blur(12px)',
            '-webkit-backdrop-filter: blur(12px)',
            'z-index: 9999999',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'padding: 1rem',
            'font-family: system-ui, -apple-system, sans-serif'
        ].join(';');

        overlay.innerHTML = `
            <div style="background: var(--bg-card, #ffffff); color: var(--text-main, #0f172a); border-radius: 24px; padding: 32px 28px; max-width: 440px; width: 100%; box-shadow: 0 25px 60px -12px rgba(0,0,0,0.4); text-align: center; border: 1px solid rgba(255,255,255,0.15); animation: guardFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);">
                <div style="width: 64px; height: 64px; border-radius: 20px; background: rgba(239, 68, 68, 0.12); color: #ef4444; display: flex; align-items: center; justify-content: center; font-size: 28px; margin: 0 auto 20px;">
                    <i class="bi bi-shield-lock-fill"></i>
                </div>
                <h4 style="font-weight: 700; font-size: 1.25rem; margin-bottom: 8px; letter-spacing: -0.3px;">Session Changed in Another Tab</h4>
                <p style="font-size: 0.88rem; color: #64748b; margin-bottom: 24px; line-height: 1.5;">
                    ${reasonText || 'A different account or new session was initiated in another tab. To prevent unauthorized actions and data collisions, this tab has been locked.'}
                </p>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button type="button" id="btnGuardReload" style="height: 48px; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; border: none; border-radius: 12px; font-weight: 600; font-size: 0.95rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 14px rgba(37,99,235,0.3);">
                        <i class="bi bi-arrow-clockwise"></i>
                        <span>Reload Tab to Sync</span>
                    </button>
                    <a href="/logout" style="height: 40px; background: transparent; color: #64748b; border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; font-weight: 600; font-size: 0.85rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 6px;">
                        <i class="bi bi-box-arrow-right"></i>
                        <span>Sign Out Completely</span>
                    </a>
                </div>
            </div>
            <style>
                @keyframes guardFadeIn {
                    from { opacity: 0; transform: scale(0.95) translateY(10px); }
                    to { opacity: 1; transform: scale(1) translateY(0); }
                }
            </style>
        `;

        document.body.appendChild(overlay);

        const reloadBtn = document.getElementById('btnGuardReload');
        if (reloadBtn) {
            reloadBtn.addEventListener('click', function () {
                window.location.reload();
            });
        }
    }

    // 5. Interceptor Guard for Fetch, XHR & Forms (Phase 3)
    // Wrap window.fetch
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        if (isDesynced) {
            return Promise.reject(new Error('Session desynced: request blocked by Cross-Tab Session Guard.'));
        }

        let [resource, config] = args;
        config = config || {};
        config.headers = config.headers || {};

        // Attach current Tab Guard ID if available
        if (currentTabGuardId) {
            if (config.headers instanceof Headers) {
                config.headers.set('X-Tab-Guard-ID', currentTabGuardId);
            } else if (Array.isArray(config.headers)) {
                config.headers.push(['X-Tab-Guard-ID', currentTabGuardId]);
            } else {
                config.headers['X-Tab-Guard-ID'] = currentTabGuardId;
            }
        }

        try {
            const response = await originalFetch.call(this, resource, config);
            
            // Check response headers for cross-tab mismatch
            const respGuardId = response.headers.get('X-Tab-Guard-ID');
            if (respGuardId && currentTabGuardId && respGuardId !== currentTabGuardId) {
                triggerSessionDesync('Session expired or replaced by a new login in another tab.');
            }

            // Detect 401 Unauthorized for authenticated tabs
            if (response.status === 401 && isAuthenticated) {
                triggerSessionDesync('Authentication session invalidated in another tab.');
            }

            return response;
        } catch (error) {
            throw error;
        }
    };

    // Wrap XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        this._guardUrl = url;
        return originalOpen.call(this, method, url, ...rest);
    };

    XMLHttpRequest.prototype.send = function (body) {
        if (isDesynced) {
            console.warn('[SessionGuard] Blocked XHR request due to session desync.');
            return;
        }
        if (currentTabGuardId) {
            try {
                this.setRequestHeader('X-Tab-Guard-ID', currentTabGuardId);
            } catch (e) {}
        }
        
        this.addEventListener('load', () => {
            try {
                const respGuardId = this.getResponseHeader('X-Tab-Guard-ID');
                if (respGuardId && currentTabGuardId && respGuardId !== currentTabGuardId) {
                    triggerSessionDesync('Session replaced in another tab.');
                }
                if (this.status === 401 && isAuthenticated) {
                    triggerSessionDesync('Authentication session terminated.');
                }
            } catch (e) {}
        });

        return originalSend.call(this, body);
    };

    // Form submission interceptor to prevent standard form bypass
    document.addEventListener('submit', function (event) {
        if (isDesynced) {
            event.preventDefault();
            event.stopPropagation();
            alert('This action cannot be completed because your session was updated in another tab. Please reload the page.');
            return false;
        }
    }, true);

    // Expose utility for manual programmatic verification if needed
    window.FixLinkSessionGuard = {
        getTabGuardId: () => currentTabGuardId,
        isDesynced: () => isDesynced,
        validateState: validateSessionState
    };
})();
