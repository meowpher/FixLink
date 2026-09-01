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
            svgDoc.style.width = '100%';
            svgDoc.style.height = '100%';
            
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
                    else if (type === 'canteen' || roomNum.toLowerCase() === 'encave') targetForFill.classList.add('fill-darkgreen');
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
        })
        .catch(err => {
            console.error('Error loading SVG map:', err);
            container.innerHTML = `<div class="alert alert-danger">Failed to load floor map: ${err.message}</div>`;
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
