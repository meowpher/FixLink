/**
 * Map Rendering Module - Handles all SVG floor plan generation and interactivity.
 */

import { selectRoom } from './ui.js';

// Attach to window so SVG onclick and global callers work
window.selectRoom = selectRoom;

export function renderFloorMap(container, rooms, floorLevel, isAdmin = false, isReport = false) {
    const svgUrl = `/static/images/floors/VY${floorLevel}.svg`;
    renderDynamicSVGFloor(container, rooms, floorLevel, svgUrl, isAdmin, isReport);
}

/**
 * Dynamic SVG Layout
 * Fetches the raw SVG file and makes room elements interactive based on IDs
 */
export function renderDynamicSVGFloor(container, rooms, floorLevel, svgUrl, isAdmin = false, isReport = false) {
    container.innerHTML = `<div class="vyas-floor-map svg-container" style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100%;"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

    fetch(svgUrl)
        .then(response => {
            if (!response.ok) throw new Error("SVG not found");
            return response.text();
        })
        .then(svgContent => {
            container.innerHTML = `<div class="vyas-floor-map svg-container interactive-map-wrapper">${svgContent}</div>`;
            const svgDoc = container.querySelector('svg');
            if (!svgDoc) return;

            svgDoc.classList.add('interactive-map');
            svgDoc.style.width = 'auto';
            svgDoc.style.height = '98%';
            svgDoc.style.maxHeight = '950px';
            svgDoc.style.display = 'block';
            svgDoc.style.margin = '0 auto';
            svgDoc.style.transformOrigin = 'center center';
            svgDoc.style.transition = 'transform 0.15s ease-out';
            
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

            // Disable pointer-events on background & decorative outline paths so clicks are not intercepted
            svgDoc.querySelectorAll('#Background, #Map_Outlines, #Interior_outlines, #Design, g[id^="Map_"], g[id^="Interior_"]').forEach(el => {
                el.style.pointerEvents = 'none';
            });

            // Disable pointer-events on text labels inside rooms so clicks hit the room container
            svgDoc.querySelectorAll('[id$="_label"], [id$="_label_container"], [id*="_label"], text, tspan').forEach(el => {
                el.style.pointerEvents = 'none';
            });

            // Process Rooms from database
            rooms.forEach(room => {
                const roomNum = room.number;
                const roomId = room.id;
                const type = room.room_type || 'class';
                const isIssue = room.status === 'issue';
                const isInProgress = room.status === 'in-progress';
                const isAssigned = room.status === 'assigned';
                const roomName = (room.name || roomNum).replace(/'/g, "\\'");

                // Locate container or shape element in SVG (supports exact, lower, and upper case)
                let containerEl = svgDoc.querySelector(`[id="${roomNum}_container"]`) ||
                                  svgDoc.querySelector(`[id="${roomNum.toLowerCase()}_container"]`) ||
                                  svgDoc.querySelector(`[id="${roomNum.toUpperCase()}_container"]`) ||
                                  svgDoc.querySelector(`[id="${roomNum}"]`)?.closest('g[id$="_container"]') ||
                                  svgDoc.querySelector(`[id="${roomNum.toLowerCase()}"]`)?.closest('g[id$="_container"]') ||
                                  svgDoc.querySelector(`[id="${roomNum.toUpperCase()}"]`)?.closest('g[id$="_container"]');
                let shapeEl = svgDoc.querySelector(`[id="${roomNum}"]`) ||
                              svgDoc.querySelector(`[id="${roomNum.toLowerCase()}"]`) ||
                              svgDoc.querySelector(`[id="${roomNum.toUpperCase()}"]`);

                // Fallback for lifts (e.g., VY0Lift1 -> lift_1_container / lift_1)
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

                // If only shape exists without a container, use its parent group or use shape directly
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
                    // Set classes and attributes on container
                    containerEl.classList.add('room-group');
                    containerEl.setAttribute('data-room', roomNum);
                    containerEl.setAttribute('data-room-id', roomId);
                    containerEl.style.pointerEvents = 'all';

                    if (shapeEl && shapeEl !== containerEl) {
                        shapeEl.classList.add('room-poly', 'svg-room-interactive');
                        shapeEl.setAttribute('data-room', roomNum);
                        shapeEl.setAttribute('data-room-id', roomId);
                        shapeEl.style.pointerEvents = 'all';
                    } else {
                        containerEl.classList.add('room-poly', 'svg-room-interactive');
                    }

                    // Apply type fill classes
                    const targetForFill = (shapeEl && shapeEl !== containerEl) ? shapeEl : containerEl;
                    if (type === 'class') targetForFill.classList.add('fill-blue');
                    else if (type === 'lab') targetForFill.classList.add('fill-teal');
                    else if (type === 'washroom') targetForFill.classList.add('fill-red');
                    else if (type === 'faculty') targetForFill.classList.add('fill-orange');
                    else if (type === 'lift') targetForFill.classList.add('fill-pink');
                    else if (type === 'kitchen') targetForFill.classList.add('fill-orange');
                    else if (type === 'canteen' || roomNum.toLowerCase() === 'encave') {
                        targetForFill.classList.add('fill-darkgreen');
                        targetForFill.style.setProperty('fill', '#023F24', 'important');
                        if (shapeEl) shapeEl.style.setProperty('fill', '#023F24', 'important');
                        if (containerEl) {
                            const label = containerEl.querySelector('[id$="_label"], text, path:not(#encave)');
                            if (label) label.style.setProperty('fill', '#ffffff', 'important');
                        }
                    }
                    else if (type === 'meeting' || type === 'meeting_room' || type === 'conference' || type === 'conference_room') {
                        targetForFill.classList.add('fill-purple');
                    } else if (type === 'unavailable') {
                        targetForFill.style.opacity = '0.5';
                    }

                    if (isAdmin) {
                        if (isIssue) targetForFill.classList.add('has-issue');
                        else if (isInProgress) targetForFill.classList.add('in-progress');
                        else if (isAssigned) targetForFill.classList.add('assigned');
                    }

                    // Check interactivity:
                    // In reporting mode (isReport), all rooms can be reported
                    // In admin mode, all rooms are interactable
                    // In faculty mode, non-bookable types (washroom, lift) are disabled
                    const isInteractable = isAdmin || isReport || !['washroom', 'lift', 'stairs'].includes(type);

                    if (isInteractable) {
                        containerEl.classList.add('interactive');
                        containerEl.classList.remove('room-disabled');
                        containerEl.style.cursor = 'pointer';
                        if (shapeEl) shapeEl.style.cursor = 'pointer';

                        // Attach event listener to container
                        containerEl.onclick = (e) => {
                            if (e) {
                                e.stopPropagation();
                            }
                            if (typeof window.selectRoom === 'function') {
                                window.selectRoom(e, roomNum, roomId, roomName, type);
                            }
                        };
                    } else {
                        containerEl.classList.add('room-disabled');
                        containerEl.classList.remove('interactive');
                        containerEl.style.cursor = 'default';
                        if (shapeEl) shapeEl.style.cursor = 'default';
                    }

                    // Add Admin Indicator Dots if needed
                    if (isAdmin && (isIssue || isInProgress || isAssigned)) {
                        try {
                            const bbox = (shapeEl || containerEl).getBBox();
                            const radius = 6;
                            const cx = bbox.x + bbox.width - radius - 3;
                            const cy = bbox.y + radius + 3;
                            let circleFill = isIssue ? '#dc3545' : (isInProgress ? '#ffc107' : '#0d6efd');
                            
                            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                            circle.setAttribute('cx', cx);
                            circle.setAttribute('cy', cy);
                            circle.setAttribute('r', radius);
                            circle.setAttribute('fill', circleFill);
                            circle.setAttribute('stroke', 'white');
                            circle.setAttribute('stroke-width', '1.5');
                            circle.style.pointerEvents = 'none';
                            
                            if (containerEl.parentNode) {
                                containerEl.parentNode.insertBefore(circle, containerEl.nextSibling);
                            }
                        } catch (e) {
                            console.warn('Could not add admin indicator to', roomNum, e);
                        }
                    }
                }
            });

            handleAutoSelect(container);
            setupMapZoomAndPan(container, svgDoc);
        })
        .catch(err => {
            console.error('Error loading SVG map:', err);
            container.innerHTML = `<div class="alert alert-danger">Failed to load floor map: ${err.message}</div>`;
        });
}

function setupMapZoomAndPan(container, svgDoc) {
    let scale = 1.0;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;

    svgDoc.style.transformOrigin = 'center center';
    svgDoc.style.transition = 'transform 0.05s ease-out';

    const badge = document.getElementById('mapZoomLevelBadge');

    function applyTransform() {
        svgDoc.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
        if (badge) badge.textContent = `${Math.round(scale * 100)}%`;
    }

    const btnIn = document.getElementById('btnMapZoomIn');
    const btnOut = document.getElementById('btnMapZoomOut');
    const btnReset = document.getElementById('btnMapZoomReset');

    if (btnIn) {
        btnIn.onclick = (e) => {
            e.preventDefault();
            scale = Math.min(scale + 0.25, 4.0);
            applyTransform();
        };
    }
    if (btnOut) {
        btnOut.onclick = (e) => {
            e.preventDefault();
            scale = Math.max(scale - 0.25, 0.6);
            if (scale <= 1.0) { panX = 0; panY = 0; }
            applyTransform();
        };
    }
    if (btnReset) {
        btnReset.onclick = (e) => {
            e.preventDefault();
            scale = 1.0;
            panX = 0;
            panY = 0;
            applyTransform();
        };
    }

    // Ctrl + Scroll Zoom / Trackpad pinch
    container.addEventListener('wheel', (e) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (e.deltaY < 0) {
                scale = Math.min(scale + 0.15, 4.0);
            } else {
                scale = Math.max(scale - 0.15, 0.6);
                if (scale <= 1.0) { panX = 0; panY = 0; }
            }
            applyTransform();
        }
    }, { passive: false });

    // Desktop Mouse Drag to Pan when zoomed
    container.addEventListener('mousedown', (e) => {
        if (e.target.closest('.room-group') || scale <= 1.0) return;
        isDragging = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        container.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        applyTransform();
    });

    window.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            container.style.cursor = '';
        }
    });

    // ── Mobile Touch Support: Pinch to Zoom & Finger Pan ──
    let initialPinchDist = 0;
    let initialScale = 1.0;
    let touchMidX = 0;
    let touchMidY = 0;
    let touchPanStartX = 0;
    let touchPanStartY = 0;
    let isTouchPanning = false;
    let touchStartPanX = 0;
    let touchStartPanY = 0;
    let lastTapTime = 0;

    const calcDist = (t1, t2) => Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    const calcMid = (t1, t2) => ({
        x: (t1.clientX + t2.clientX) / 2,
        y: (t1.clientY + t2.clientY) / 2
    });

    container.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            // Two fingers: Pinch Zoom
            e.preventDefault();
            initialPinchDist = calcDist(e.touches[0], e.touches[1]);
            initialScale = scale;
            const mid = calcMid(e.touches[0], e.touches[1]);
            touchMidX = mid.x;
            touchMidY = mid.y;
            touchStartPanX = panX;
            touchStartPanY = panY;
        } else if (e.touches.length === 1) {
            const now = Date.now();
            if (now - lastTapTime < 300) {
                // Double-tap: Zoom in or reset
                e.preventDefault();
                if (scale > 1.2) {
                    scale = 1.0;
                    panX = 0;
                    panY = 0;
                } else {
                    scale = 2.0;
                }
                applyTransform();
                lastTapTime = 0;
                return;
            }
            lastTapTime = now;

            if (scale > 1.05 && !e.target.closest('.room-group')) {
                // Single finger drag to pan when already zoomed in
                isTouchPanning = true;
                touchPanStartX = e.touches[0].clientX - panX;
                touchPanStartY = e.touches[0].clientY - panY;
            }
        }
    }, { passive: false });

    container.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2 && initialPinchDist > 0) {
            e.preventDefault();
            const currentDist = calcDist(e.touches[0], e.touches[1]);
            const zoomRatio = currentDist / initialPinchDist;
            scale = Math.min(Math.max(initialScale * zoomRatio, 0.6), 4.5);

            const mid = calcMid(e.touches[0], e.touches[1]);
            panX = touchStartPanX + (mid.x - touchMidX);
            panY = touchStartPanY + (mid.y - touchMidY);

            if (scale <= 0.85) {
                panX = 0;
                panY = 0;
            }
            applyTransform();
        } else if (e.touches.length === 1 && isTouchPanning && scale > 1.05) {
            e.preventDefault();
            panX = e.touches[0].clientX - touchPanStartX;
            panY = e.touches[0].clientY - touchPanStartY;
            applyTransform();
        }
    }, { passive: false });

    container.addEventListener('touchend', (e) => {
        if (e.touches.length < 2) {
            initialPinchDist = 0;
        }
        if (e.touches.length === 0) {
            isTouchPanning = false;
        }
    });

    container.addEventListener('touchcancel', () => {
        initialPinchDist = 0;
        isTouchPanning = false;
    });
}

function handleAutoSelect(container) {
    if (typeof preSelectedRoom !== 'undefined' && preSelectedRoom) {
        const roomEl = container.querySelector(`[data-room-id="${preSelectedRoom}"]`);
        if (roomEl) {
            roomEl.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
    }
}
