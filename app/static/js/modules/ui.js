/**
 * Map UI Module - Handles all DOM manipulation, issue chips, and user interaction.
 */

import { fetchAssetsByRoom } from './api.js';

export const DYNAMIC_ISSUE_TYPES = {
    'lift': [
        { value: 'lights', label: 'Lights', icon: 'bi-lightbulb' },
        { value: 'door_stuck', label: 'Door Stuck', icon: 'bi-door-closed' },
        { value: 'lift_not_working', label: 'Lift Not Working', icon: 'bi-arrow-down-up' },
        { value: 'lift_fan', label: 'Lift Fan', icon: 'bi-fan' }
    ],
    'class': [
        { value: 'projector', label: 'Projector / Screen', icon: 'bi-projector' },
        { value: 'power_socket', label: 'Power Socket', icon: 'bi-plug' },
        { value: 'lights', label: 'Lights / Lighting', icon: 'bi-lightbulb' },
        { value: 'fans', label: 'Fans / Ventilation', icon: 'bi-fan' },
        { value: 'chairs', label: 'Chairs / Benches', icon: 'bi-grid-fill' },
        { value: 'tables', label: 'Tables / Podium', icon: 'bi-layout-text-window' },
        { value: 'black_board', label: 'Black / White Board', icon: 'bi-easel' },
        { value: 'left_tv', label: 'Display TV', icon: 'bi-tv' }
    ],
    'lab': [
        { value: 'computers', label: 'Computers / Lab Rig', icon: 'bi-display' },
        { value: 'projector', label: 'Projector / Screen', icon: 'bi-projector' },
        { value: 'ac', label: 'Air Conditioning', icon: 'bi-snow' },
        { value: 'power_socket', label: 'Power Sockets', icon: 'bi-plug' },
        { value: 'lights', label: 'Lights', icon: 'bi-lightbulb' },
        { value: 'tables', label: 'Lab Tables', icon: 'bi-layout-text-window' },
        { value: 'chairs', label: 'Lab Stools / Chairs', icon: 'bi-grid-fill' }
    ],
    'washroom': [
        { value: 'plumbing', label: 'Plumbing / Leak', icon: 'bi-droplet-half' },
        { value: 'water', label: 'No Water Supply', icon: 'bi-water' },
        { value: 'cleanliness', label: 'Sanitation / Cleaning', icon: 'bi-brush' },
        { value: 'toilet', label: 'Flush / Toilet Fixture', icon: 'bi-shield-check' },
        { value: 'toilet_stall', label: 'Door / Lock Issue', icon: 'bi-lock' }
    ],
    'default': [
        { value: 'electrical', label: 'Electrical Issue', icon: 'bi-lightning-charge' },
        { value: 'cleaning', label: 'Cleaning Required', icon: 'bi-brush' },
        { value: 'furniture', label: 'Furniture Damage', icon: 'bi-grid-fill' },
        { value: 'ac', label: 'Air Conditioning', icon: 'bi-snow' },
        { value: 'lights', label: 'Lighting Issue', icon: 'bi-lightbulb' },
        { value: 'other', label: 'Other Facilities', icon: 'bi-tools' }
    ]
};

/**
 * Handle room selection from the map or programmatic trigger.
 * @param {Event|null} event 
 * @param {string} roomNumber 
 * @param {number} roomId 
 * @param {string} roomName 
 * @param {string} roomType 
 */
export function selectRoom(event, roomNumber, roomId, roomName, roomType) {
    // Update hidden input
    const roomInput = document.getElementById('room_id');
    if (roomInput) {
        roomInput.value = roomId;
        roomInput.dispatchEvent(new Event('input', { bubbles: true }));
    }

    const displayName = roomName || roomNumber;
    const typeLabel = (roomType || 'Room').toUpperCase();

    // Update selected room display card
    const display = document.getElementById('selectedRoomDisplay');
    if (display) {
        display.classList.add('room-selected-active');
        display.innerHTML = `
            <div class="room-selected d-flex align-items-center justify-content-between p-2">
                <div class="d-flex align-items-center gap-3">
                    <div class="room-selected-icon-badge" style="width: 44px; height: 44px; border-radius: 12px; background: rgba(37, 99, 235, 0.12); color: var(--mitwpu-blue, #2563eb); display: flex; align-items: center; justify-content: center; font-size: 20px;">
                        <i class="bi bi-door-open-fill"></i>
                    </div>
                    <div class="text-start">
                        <div class="d-flex align-items-center gap-2">
                            <span class="room-number fw-bold" style="font-size: 1.15rem; color: var(--text-main, #0f172a);">${displayName}</span>
                            <span class="badge" style="background: rgba(37, 99, 235, 0.15); color: var(--mitwpu-blue, #2563eb); font-size: 0.72rem; font-weight: 700; text-transform: uppercase;">${typeLabel}</span>
                        </div>
                        <small class="text-success d-flex align-items-center gap-1 mt-0" style="font-size: 0.8rem; font-weight: 600;">
                            <i class="bi bi-check-circle-fill"></i> Ready for issue details
                        </small>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-2 py-1" onclick="window.resetRoomSelection()" title="Change room" aria-label="Change room" style="font-size: 12px;">
                    <i class="bi bi-arrow-repeat me-1"></i>Change
                </button>
            </div>
        `;
    }

    // Defensive Form UI: remove disabled state once a valid room is selected
    const formBody = document.getElementById('reportFormBody');
    if (formBody) {
        formBody.classList.remove('form-disabled');
    }

    // Highlight on map
    document.querySelectorAll('.room-group, .room-poly').forEach(el => el.classList.remove('selected'));
    const roomElements = document.querySelectorAll(`[data-room="${roomNumber}"], [data-room-id="${roomId}"]`);
    roomElements.forEach(el => {
        el.classList.add('selected');
        const poly = el.querySelector('.room-poly');
        if (poly) poly.classList.add('selected');
    });

    // Populate dynamic issue dropdown & quick chips
    updateIssueTypes(roomType || 'default');

    // Smooth scroll to the report form on mobile devices (<= 768px)
    if (window.innerWidth <= 768) {
        const reportForm = document.getElementById('reportForm');
        if (reportForm) {
            const yOffset = -80; // Adjust for sticky header
            const y = reportForm.getBoundingClientRect().top + window.scrollY + yOffset;
            window.scrollTo({ top: y, behavior: 'smooth' });
        }
    }
}

let isIssueDropdownInitialized = false;

/**
 * Initialize custom issue dropdown event listeners.
 */
export function initializeIssueDropdown() {
    if (isIssueDropdownInitialized) return;

    const trigger = document.getElementById('issueDropdownTrigger');
    const menu = document.getElementById('issueDropdownMenu');
    const label = document.getElementById('issueDropdownLabel');
    const select = document.getElementById('issue_type');
    const itemsContainer = document.getElementById('issueDropdownItems');

    if (!trigger || !menu || !select || !itemsContainer) return;

    isIssueDropdownInitialized = true;

    function open() {
        if (trigger.disabled) return;
        menu.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
    }

    function close() {
        menu.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.classList.contains('open') ? close() : open();
    });

    itemsContainer.addEventListener('click', (e) => {
        const item = e.target.closest('.cfd-item');
        if (!item) return;

        const value = item.dataset.value;
        const text = item.textContent.trim();

        label.textContent = text || 'Select Issue Type';

        itemsContainer.querySelectorAll('.cfd-item').forEach(i => i.classList.remove('selected'));
        if (value) item.classList.add('selected');

        select.value = value;
        select.dispatchEvent(new Event('change', { bubbles: true }));

        // Sync quick chips
        syncActiveQuickChip(value);

        close();
    });

    document.addEventListener('click', (e) => {
        if (!trigger.contains(e.target) && !menu.contains(e.target)) close();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') close();
    });
}

/**
 * Sync active state of quick issue chips with chosen value.
 * @param {string} value 
 */
export function syncActiveQuickChip(value) {
    const chips = document.querySelectorAll('.quick-issue-chip');
    chips.forEach(chip => {
        if (chip.dataset.value === value) {
            chip.classList.add('active');
            chip.setAttribute('aria-pressed', 'true');
        } else {
            chip.classList.remove('active');
            chip.setAttribute('aria-pressed', 'false');
        }
    });
}

/**
 * Update the issue type dropdown and render 1-tap quick issue chips based on room category.
 * @param {string} roomType 
 */
export function updateIssueTypes(roomType) {
    const issueSelect = document.getElementById('issue_type');
    if (!issueSelect) return;

    initializeIssueDropdown();

    const normalizedType = (roomType || 'default').toLowerCase();
    const optionsArray = DYNAMIC_ISSUE_TYPES[normalizedType] || DYNAMIC_ISSUE_TYPES['default'];

    // Update native hidden select
    issueSelect.innerHTML = '<option value="">Select Issue Type</option>';
    optionsArray.forEach(issue => {
        const option = document.createElement('option');
        option.value = issue.value;
        option.textContent = issue.label;
        issueSelect.appendChild(option);
    });
    issueSelect.disabled = false;
    issueSelect.value = '';

    // Update custom dropdown UI
    const trigger = document.getElementById('issueDropdownTrigger');
    const label = document.getElementById('issueDropdownLabel');
    const itemsContainer = document.getElementById('issueDropdownItems');

    if (trigger && label && itemsContainer) {
        label.textContent = 'Select Issue Type';
        trigger.disabled = false;

        itemsContainer.innerHTML = '<div class="cfd-item" data-value="" role="option">Select Issue Type</div>';
        optionsArray.forEach(issue => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'cfd-item';
            itemDiv.dataset.value = issue.value;
            itemDiv.setAttribute('role', 'option');
            itemDiv.innerHTML = `<i class="bi ${issue.icon || 'bi-tools'} me-2 opacity-75"></i>${issue.label}`;
            itemsContainer.appendChild(itemDiv);
        });
    }

    // Render 1-tap Quick Issue Chips
    renderQuickChips(optionsArray);
}

/**
 * Render quick clickable issue tags for effortless 1-tap selection on mobile & desktop.
 * @param {Array} optionsArray 
 */
function renderQuickChips(optionsArray) {
    const chipsContainer = document.getElementById('quickIssueChips');
    if (!chipsContainer) return;

    chipsContainer.innerHTML = '';
    const topIssues = optionsArray.slice(0, 6);

    topIssues.forEach(issue => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'quick-issue-chip';
        chip.dataset.value = issue.value;
        chip.setAttribute('aria-pressed', 'false');
        chip.innerHTML = `<i class="bi ${issue.icon || 'bi-tools'}"></i><span>${issue.label}</span>`;

        chip.addEventListener('click', () => {
            const issueSelect = document.getElementById('issue_type');
            const label = document.getElementById('issueDropdownLabel');
            const itemsContainer = document.getElementById('issueDropdownItems');

            if (issueSelect) {
                issueSelect.value = issue.value;
                issueSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (label) {
                label.textContent = issue.label;
            }
            if (itemsContainer) {
                itemsContainer.querySelectorAll('.cfd-item').forEach(i => {
                    i.classList.toggle('selected', i.dataset.value === issue.value);
                });
            }
            syncActiveQuickChip(issue.value);
        });

        chipsContainer.appendChild(chip);
    });
}

/**
 * Clear the current room selection and return to standby state.
 */
export function resetRoomSelection() {
    const roomInput = document.getElementById('room_id');
    const display = document.getElementById('selectedRoomDisplay');

    if (roomInput) {
        roomInput.value = '';
        roomInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // Reinstate defensive disabled state
    const formBody = document.getElementById('reportFormBody');
    if (formBody) {
        formBody.classList.add('form-disabled');
    }

    if (display) {
        display.classList.remove('room-selected-active');
        display.innerHTML = `
            <div class="room-placeholder">
                <i class="bi bi-door-closed"></i>
                <span>No room selected — tap any room on the map above</span>
            </div>
        `;
    }

    document.querySelectorAll('.room-block, .room-group, .room-poly').forEach(block => {
        block.classList.remove('selected');
    });

    // Reset Issue Types dropdown
    const issueSelect = document.getElementById('issue_type');
    const trigger = document.getElementById('issueDropdownTrigger');
    const label = document.getElementById('issueDropdownLabel');
    const itemsContainer = document.getElementById('issueDropdownItems');
    const chipsContainer = document.getElementById('quickIssueChips');

    if (issueSelect) {
        issueSelect.innerHTML = '<option value="">Select a Room First</option>';
        issueSelect.value = '';
        issueSelect.disabled = true;
    }
    if (trigger) trigger.disabled = true;
    if (label) label.textContent = 'Select a Room First';
    if (itemsContainer) itemsContainer.innerHTML = '';
    if (chipsContainer) chipsContainer.innerHTML = '';
}

// Expose resetRoomSelection globally
window.resetRoomSelection = resetRoomSelection;
