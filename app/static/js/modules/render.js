/**
 * Map Rendering Module - Handles all SVG floor plan generation, interactive caching, zoom/pan, tooltips, and A11y.
 */

import { selectRoom } from './ui.js';

// Attach to window so SVG onclick and global callers work
window.selectRoom = selectRoom;

// In-memory SVG Cache for 0ms floor plan switching
const svgCache = new Map();

// Map Zoom/Pan state
let currentZoom = 1;
let currentPanX = 0;
let currentPanY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

export function renderFloorMap(container, rooms, floorLevel, isAdmin = false, isReport = false) {
    const svgUrl = `/static/images/floors/VY${floorLevel}.svg`;
    renderDynamicSVGFloor(container, rooms, floorLevel, svgUrl, isAdmin, isReport);
}

/**
 * Dynamic SVG Layout
 * Fetches/caches the raw SVG file and makes room elements interactive based on IDs
 */
export function renderDynamicSVGFloor(container, rooms, floorLevel, svgUrl, isAdmin = false, isReport = false) {
    // Reset zoom & pan on new floor load
    currentZoom = 1;
    currentPanX = 0;
    currentPanY = 0;
    updateMapTransform(container);

    if (svgCache.has(svgUrl)) {
        setupSVGMap(container, svgCache.get(svgUrl), rooms, floorLevel, isAdmin, isReport);
        return;
    }

    container.innerHTML = `
        <div class="vyas-floor-map svg-container" style="display: flex; flex-direction: column; justify-content: center; align-items: center; width: 100%; height: 100%; min-height: 400px;">
            <div class="spinner-border text-primary" role="status" style="width: 2.5rem; height: 2.5rem;">
                <span class="visually-hidden">Loading floor map...</span>
            </div>
            <p class="mt-3 text-muted fw-semibold small">Loading Floor ${floorLevel} plan...</p>
        </div>
    `;

    fetch(svgUrl)
        .then(response => {
            if (!response.ok) throw new Error("SVG not found");
            return response.text();
        })
        .then(svgContent => {
            svgCache.set(svgUrl, svgContent);
            setupSVGMap(container, svgContent, rooms, floorLevel, isAdmin, isReport);
        })
        .catch(err => {
            container.innerHTML = `
                <div class="floor-map-placeholder text-center p-4">
                    <i class="bi bi-exclamation-triangle display-2 text-warning mb-3"></i>
                    <h5 class="fw-bold">Floor Map Unavailable</h5>
                    <p class="text-muted small">Could not load visual map for Floor ${floorLevel}. You can still select from available rooms.</p>
                </div>
            `;
        });
}

function setupSVGMap(container, svgContent, rooms, floorLevel, isAdmin, isReport) {
    container.innerHTML = `
        <div class="vyas-floor-map svg-container interactive-map-wrapper" id="svgMapWrapper" style="width: 100%; height: 100%; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; user-select: none;">
            ${svgContent}
        </div>
    `;

    const svgWrapper = container.querySelector('#svgMapWrapper');
    const svgDoc = container.querySelector('svg');
    if (!svgDoc || !svgWrapper) return;

    svgDoc.classList.add('interactive-map');
    svgDoc.style.width = 'auto';
    svgDoc.style.height = '98%';
    svgDoc.style.maxHeight = '950px';
    svgDoc.style.display = 'block';
    svgDoc.style.margin = '0 auto';
    svgDoc.style.transformOrigin = 'center center';
    svgDoc.style.transition = 'transform 0.15s ease-out';
    svgDoc.style.pointerEvents = 'none';

    // Add Glow Filter if not exists
    if (!svgDoc.querySelector('defs filter#glow')) {
        const defs = svgDoc.querySelector('defs') || document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        if (!svgDoc.querySelector('defs')) svgDoc.prepend(defs);
        defs.innerHTML += `
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
        `;
    }

    // Disable pointer-events on background & decorative outline paths
    svgDoc.querySelectorAll('#Background, #Map_Outlines, #Interior_outlines, #Design, g[id^="Map_"], g[id^="Interior_"]').forEach(el => {
        el.style.pointerEvents = 'none';
    });

    // Disable pointer-events on text labels inside rooms so clicks hit the room container
    svgDoc.querySelectorAll('[id$="_label"], [id$="_label_container"], [id*="_label"], text, tspan').forEach(el => {
        el.style.pointerEvents = 'none';
    });

    const tooltipEl = document.getElementById('roomMapTooltip');

    // Process Rooms from database
    rooms.forEach(room => {
        const roomNum = room.number;
        const roomId = room.id;
        const type = room.room_type || 'class';
        const isIssue = room.status === 'issue';
        const isInProgress = room.status === 'in-progress';
        const isAssigned = room.status === 'assigned';
        const roomName = (room.name || roomNum).replace(/'/g, "\\'");
        const roomTitle = room.name ? `${room.name} (${roomNum})` : roomNum;

        let containerEl = svgDoc.querySelector(`[id="${roomNum}_container"]`) ||
                          svgDoc.querySelector(`[id="${roomNum.toLowerCase()}_container"]`) ||
                          svgDoc.querySelector(`[id="${roomNum.toUpperCase()}_container"]`) ||
                          svgDoc.querySelector(`[id="${roomNum}"]`)?.closest('g[id$="_container"]') ||
                          svgDoc.querySelector(`[id="${roomNum.toLowerCase()}"]`)?.closest('g[id$="_container"]') ||
                          svgDoc.querySelector(`[id="${roomNum.toUpperCase()}"]`)?.closest('g[id$="_container"]');
        let shapeEl = svgDoc.querySelector(`[id="${roomNum}"]`) ||
                      svgDoc.querySelector(`[id="${roomNum.toLowerCase()}"]`) ||
                      svgDoc.querySelector(`[id="${roomNum.toUpperCase()}"]`);

        // Fallback for lifts
        if (!containerEl && !shapeEl && (type === 'lift' || roomNum.toLowerCase().includes('lift'))) {
            const liftMatch = roomNum.match(/Lift(\d+)/i);
            if (liftMatch) {
                const num = liftMatch[1];
                containerEl = svgDoc.querySelector(`[id="lift_${num}_container"]`) ||
                              svgDoc.querySelector(`[id="Lift_${num}_container"]`) ||
                              svgDoc.querySelector(`[id="lift_${num}"]`)?.closest('g');
                shapeEl = svgDoc.querySelector(`[id="lift_${num}"]`) || 
                          svgDoc.querySelector(`[id="Lift_${num}"]`) || 
                          containerEl?.querySelector('rect, path');
            }
        }

        if (!containerEl && shapeEl) {
            if (shapeEl.tagName.toLowerCase() === 'g') {
                containerEl = shapeEl;
            } else if (shapeEl.parentElement && shapeEl.parentElement.tagName.toLowerCase() === 'g' && shapeEl.parentElement !== svgDoc && !shapeEl.parentElement.id.startsWith('VY')) {
                containerEl = shapeEl.parentElement;
            } else {
                containerEl = shapeEl;
            }
        }

        if (!shapeEl && containerEl) {
            shapeEl = containerEl.querySelector('rect, path:not([id*="_label"])') || containerEl;
        }

        if (containerEl) {
            if (shapeEl && containerEl.children) {
                Array.from(containerEl.children).forEach(child => {
                    if (child !== shapeEl) {
                        if (!child.id || !child.id.includes('_label')) {
                            child.setAttribute('id', (child.id || roomNum) + '_label');
                        }
                        child.classList.add('room-label');
                        child.style.pointerEvents = 'none';
                    }
                });
            }

            containerEl.classList.add('room-group', 'interactive-room');
            containerEl.setAttribute('data-room', roomNum);
            containerEl.setAttribute('data-room-id', roomId);
            containerEl.setAttribute('data-room-type', type);
            containerEl.setAttribute('data-room-name', roomName);
            containerEl.setAttribute('tabindex', '0');
            containerEl.setAttribute('role', 'button');
            containerEl.setAttribute('aria-label', `Room ${roomTitle}, Type: ${type}. Click to report issue.`);
            containerEl.style.pointerEvents = 'auto';
            containerEl.style.cursor = 'pointer';

            if (shapeEl && shapeEl !== containerEl) {
                shapeEl.classList.add('room-poly', 'svg-room-interactive', 'interactive-room');
                shapeEl.setAttribute('data-room', roomNum);
                shapeEl.setAttribute('data-room-id', roomId);
                shapeEl.style.pointerEvents = 'auto';
            } else {
                containerEl.classList.add('room-poly', 'svg-room-interactive');
            }

            if (shapeEl) {
                shapeEl.removeAttribute('fill');
                shapeEl.removeAttribute('stroke');
                shapeEl.removeAttribute('style');
            }

            // Status Classes
            if (isIssue) {
                containerEl.classList.add('has-issue', 'status-issue');
                if (shapeEl) shapeEl.classList.add('has-issue', 'status-issue');
            } else if (isInProgress) {
                containerEl.classList.add('status-in-progress');
                if (shapeEl) shapeEl.classList.add('status-in-progress');
            } else if (isAssigned) {
                containerEl.classList.add('status-assigned');
                if (shapeEl) shapeEl.classList.add('status-assigned');
            }

            // Click Handler
            const clickHandler = (e) => {
                if (isPanning) return;
                e.stopPropagation();
                selectRoom(e, roomNum, roomId, roomName, type);
            };

            containerEl.addEventListener('click', clickHandler);
            if (shapeEl && shapeEl !== containerEl) {
                shapeEl.addEventListener('click', clickHandler);
            }

            // Keyboard accessibility (Enter / Space)
            containerEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectRoom(e, roomNum, roomId, roomName, type);
                }
            });

            // Hover Tooltip
            if (tooltipEl) {
                containerEl.addEventListener('mouseenter', (e) => {
                    const statusText = isIssue ? '⚠️ Open Issue' : (isInProgress ? '🔧 In Progress' : '✅ Operational');
                    tooltipEl.innerHTML = `<strong>${roomTitle}</strong><span class="tooltip-type">${type.toUpperCase()}</span><span class="tooltip-status">${statusText}</span>`;
                    tooltipEl.style.display = 'block';
                    tooltipEl.style.opacity = '1';
                });

                containerEl.addEventListener('mousemove', (e) => {
                    const mapRect = container.getBoundingClientRect();
                    const x = e.clientX - mapRect.left + 14;
                    const y = e.clientY - mapRect.top - 12;
                    tooltipEl.style.transform = `translate3d(${x}px, ${y}px, 0)`;
                });

                containerEl.addEventListener('mouseleave', () => {
                    tooltipEl.style.opacity = '0';
                    setTimeout(() => {
                        if (tooltipEl.style.opacity === '0') tooltipEl.style.display = 'none';
                    }, 150);
                });
            }
        }
    });

    // Auto-select room if requested
    if (typeof window.preSelectedRoom !== 'undefined' && window.preSelectedRoom) {
        const targetRoom = rooms.find(r => r.id == window.preSelectedRoom);
        if (targetRoom) {
            selectRoom(null, targetRoom.number, targetRoom.id, targetRoom.name, targetRoom.room_type);
        }
    }

    // Initialize Map Zoom & Pan Listeners
    initZoomAndPan(container, svgWrapper, svgDoc);
}

/**
 * Initialize Zoom & Pan gestures for mobile pinch and desktop dragging.
 */
function initZoomAndPan(container, wrapper, svgDoc) {
    // Zoom in / out buttons
    const btnZoomIn = document.getElementById('mapZoomIn');
    const btnZoomOut = document.getElementById('mapZoomOut');
    const btnZoomReset = document.getElementById('mapZoomReset');

    if (btnZoomIn) {
        btnZoomIn.onclick = () => {
            currentZoom = Math.min(currentZoom + 0.25, 2.5);
            updateMapTransform(container);
        };
    }
    if (btnZoomOut) {
        btnZoomOut.onclick = () => {
            currentZoom = Math.max(currentZoom - 0.25, 0.75);
            updateMapTransform(container);
        };
    }
    if (btnZoomReset) {
        btnZoomReset.onclick = () => {
            currentZoom = 1;
            currentPanX = 0;
            currentPanY = 0;
            updateMapTransform(container);
        };
    }
}

function updateMapTransform(container) {
    const svg = container ? container.querySelector('svg') : document.querySelector('.interactive-map');
    if (svg) {
        svg.style.transform = `translate(${currentPanX}px, ${currentPanY}px) scale(${currentZoom})`;
    }
}
