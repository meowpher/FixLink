/**
 * FixLink Enterprise Cross-Tab Session Guard (Zero-Trust Architecture)
 * Phase 4: Bulletproof Omni-Observer & Socket Kill-Switch
 */
(function () {
    'use strict';

    // 1. Null-Safe Cryptographic Anchor
    const metaTag = document.querySelector('meta[name="tab-guard-id"]');
    const localGuardId = metaTag ? metaTag.content.trim() : null;

    window.SESSION_INVALIDATED = false;

    // 2. Throttle & Validation: 2000ms Date.now() Lock
    let lastVerifyTime = 0;
    const THROTTLE_MS = 2000;
    let isVerifying = false;

    async function verifySessionIntegrity() {
        if (!localGuardId || window.SESSION_INVALIDATED) return;

        const now = Date.now();
        if (now - lastVerifyTime < THROTTLE_MS || isVerifying) {
            return;
        }
        lastVerifyTime = now;
        isVerifying = true;

        try {
            const resp = await originalFetch('/api/auth/status', {
                method: 'GET',
                cache: 'no-store',
                headers: {
                    'Accept': 'application/json',
                    'X-Tab-Guard-ID': localGuardId
                }
            });

            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    invalidateSession('Authentication state expired or rejected by server.');
                }
                return;
            }

            const data = await resp.json();
            if (data) {
                // If API guard_id does not match localGuardId or user is not authenticated
                if (!data.authenticated || (data.guard_id && data.guard_id !== localGuardId)) {
                    invalidateSession('Session mismatch: An account switch was detected in another tab.');
                }
            }
        } catch (err) {
            // Transient network error, allow graceful retry on next interaction
        } finally {
            isVerifying = false;
        }
    }

    // 3. WebSocket & Real-Time Kill-Switch + UI Lockdown
    function invalidateSession(reasonText) {
        if (window.SESSION_INVALIDATED) return;
        window.SESSION_INVALIDATED = true;

        console.warn('[SessionGuard] Critical Session Invalidation:', reasonText);

        // A. WebSocket Kill-Switch
        try {
            if (window.socket && typeof window.socket.disconnect === 'function') {
                window.socket.disconnect();
            }
        } catch (e) {}

        try {
            if (window.pusher && typeof window.pusher.disconnect === 'function') {
                window.pusher.disconnect();
            }
        } catch (e) {}

        try {
            if (window.eventSource && typeof window.eventSource.close === 'function') {
                window.eventSource.close();
            }
            if (window.sseSource && typeof window.sseSource.close === 'function') {
                window.sseSource.close();
            }
        } catch (e) {}

        // B. Clear All Active Timers and Pollers
        try {
            let maxTimerId = setTimeout(function () {}, 0);
            for (let i = 0; i < maxTimerId; i++) {
                clearTimeout(i);
                clearInterval(i);
            }
        } catch (e) {}

        // C. Apply disabled=true to all inputs, buttons, selects, textareas
        try {
            document.querySelectorAll('input, button, select, textarea').forEach(el => {
                el.disabled = true;
            });
        } catch (e) {}

        // D. Render Static Bootstrap Modal (Zero Bypass)
        renderLockoutModal(reasonText);
    }

    function renderLockoutModal(reasonText) {
        if (document.getElementById('sessionConflictModal')) return;

        const modalContainer = document.createElement('div');
        modalContainer.id = 'sessionConflictModal';
        modalContainer.style.cssText = [
            'position: fixed',
            'top: 0',
            'left: 0',
            'width: 100vw',
            'height: 100vh',
            'background: rgba(15, 23, 42, 0.85)',
            'backdrop-filter: blur(14px)',
            '-webkit-backdrop-filter: blur(14px)',
            'z-index: 9999999',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'padding: 1.25rem',
            'font-family: system-ui, -apple-system, sans-serif'
        ].join(';');

        modalContainer.innerHTML = `
            <div class="modal-dialog modal-dialog-centered" style="max-width: 440px; width: 100%; margin: 0;">
                <div class="modal-content border-0 rounded-4 shadow-lg p-4 text-center" style="background: var(--bg-card, #ffffff); color: var(--text-main, #0f172a); border: 1px solid rgba(255,255,255,0.12);">
                    <div style="width: 68px; height: 68px; border-radius: 20px; background: rgba(239, 68, 68, 0.12); color: #ef4444; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 18px;">
                        <i class="bi bi-shield-lock-fill"></i>
                    </div>
                    <h5 class="fw-bold mb-2" style="font-size: 1.25rem; letter-spacing: -0.3px;">Session Conflict Detected</h5>
                    <p class="text-muted small mb-4" style="line-height: 1.55; font-size: 0.88rem;">
                        ${reasonText || 'A new login or account switch occurred in another tab. This tab has been locked to prevent state corruption.'}
                    </p>
                    <div class="d-flex flex-column gap-2">
                        <button type="button" id="btnGuardSyncReload" class="btn btn-primary rounded-pill py-2.5 fw-semibold d-flex align-items-center justify-content-center gap-2" style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border: none;">
                            <i class="bi bi-arrow-clockwise"></i>
                            <span>Reload to Sync Account</span>
                        </button>
                        <a href="/logout" class="btn btn-outline-secondary rounded-pill py-2 small fw-semibold" style="text-decoration: none;">
                            <i class="bi bi-box-arrow-right me-1"></i>Sign Out
                        </a>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modalContainer);

        const reloadBtn = document.getElementById('btnGuardSyncReload');
        if (reloadBtn) {
            reloadBtn.disabled = false; // Keep reload button enabled
            reloadBtn.addEventListener('click', function () {
                window.location.reload();
            });
        }
    }

    // 4. Anti-Spam Form Injector
    document.addEventListener('submit', function (event) {
        if (window.SESSION_INVALIDATED) {
            event.preventDefault();
            event.stopPropagation();
            alert('Action blocked: Your session was invalidated in another tab. Please reload.');
            return false;
        }

        const form = event.target;
        if (localGuardId && form && form.tagName === 'FORM') {
            let hiddenInput = form.querySelector('input[name="X-Tab-Guard-ID"]');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'X-Tab-Guard-ID';
                form.appendChild(hiddenInput);
            }
            hiddenInput.value = localGuardId;
        }
    }, true);

    // 5. Omni-Network Proxy
    // A. Proxy window.fetch
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        if (window.SESSION_INVALIDATED) {
            return Promise.reject(new Error('Request blocked by Cross-Tab Session Guard (Session Invalidated).'));
        }

        let [resource, config] = args;
        config = config || {};
        config.headers = config.headers || {};

        if (localGuardId) {
            if (config.headers instanceof Headers) {
                config.headers.set('X-Tab-Guard-ID', localGuardId);
            } else if (Array.isArray(config.headers)) {
                config.headers.push(['X-Tab-Guard-ID', localGuardId]);
            } else {
                config.headers['X-Tab-Guard-ID'] = localGuardId;
            }
        }

        try {
            const response = await originalFetch.call(this, resource, config);

            // Header mismatch check
            const respGuardId = response.headers.get('X-Tab-Guard-ID');
            if (respGuardId && localGuardId && respGuardId !== localGuardId) {
                invalidateSession('Server session conflict: active account switched in another tab.');
            }

            // 403 Session Conflict check
            if (response.status === 403) {
                try {
                    const cloned = response.clone();
                    cloned.json().then(data => {
                        if (data && data.error === 'session_conflict') {
                            invalidateSession('Session conflict: request rejected by server.');
                        }
                    }).catch(() => {});
                } catch (e) {}
            }

            return response;
        } catch (error) {
            throw error;
        }
    };

    // B. Override XMLHttpRequest.prototype.open
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        this._guardUrl = url;
        const result = originalOpen.call(this, method, url, ...rest);
        if (localGuardId) {
            try {
                this.setRequestHeader('X-Tab-Guard-ID', localGuardId);
            } catch (e) {}
        }
        return result;
    };

    XMLHttpRequest.prototype.send = function (body) {
        if (window.SESSION_INVALIDATED) {
            console.warn('[SessionGuard] Blocked XHR request due to invalidated session.');
            return;
        }

        this.addEventListener('load', () => {
            try {
                const respGuardId = this.getResponseHeader('X-Tab-Guard-ID');
                if (respGuardId && localGuardId && respGuardId !== localGuardId) {
                    invalidateSession('Server session conflict: active account switched.');
                }
                if (this.status === 403) {
                    try {
                        const data = JSON.parse(this.responseText);
                        if (data && data.error === 'session_conflict') {
                            invalidateSession('Session conflict: request rejected by server.');
                        }
                    } catch (e) {}
                }
            } catch (e) {}
        });

        return originalSend.call(this, body);
    };

    // 6. Event Binding: visibilitychange, focus, pageshow
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') {
            verifySessionIntegrity();
        }
    });

    window.addEventListener('focus', function () {
        verifySessionIntegrity();
    });

    window.addEventListener('pageshow', function (event) {
        verifySessionIntegrity();
    });

    // Cross-tab real-time sync (BroadcastChannel & storage)
    try {
        if (typeof BroadcastChannel !== 'undefined') {
            const bc = new BroadcastChannel('fixlink_session_guard_channel');
            bc.onmessage = function (event) {
                if (event && event.data && event.data.tabGuardId && event.data.tabGuardId !== localGuardId) {
                    invalidateSession('Session switched in another tab.');
                }
            };
        }
    } catch (e) {}

    window.addEventListener('storage', function (event) {
        if (event.key === 'fixlink_active_session_anchor' && event.newValue) {
            try {
                const sessionData = JSON.parse(event.newValue);
                if (sessionData && sessionData.tabGuardId && sessionData.tabGuardId !== localGuardId) {
                    invalidateSession('Session switched in another tab.');
                }
            } catch (e) {}
        }
    });

    // Initial integrity check on load
    if (localGuardId) {
        verifySessionIntegrity();
    }
})();
