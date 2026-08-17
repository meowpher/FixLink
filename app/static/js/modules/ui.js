/**
 * Map UI Module - Handles all DOM manipulation and user interaction.
 */

import { fetchAssetsByRoom } from './api.js';

export const DYNAMIC_ISSUE_TYPES = {
    'lift': [
        { value: 'lights', label: 'Lights' },
        { value: 'door_stuck', label: 'Door stuck' },
        { value: 'lift_not_working', label: 'Lift not working' },
        { value: 'lift_fan', label: 'Lift fan' }
    ],
    'class': [
        { value: 'chairs', label: 'Chairs' },
        { value: 'tables', label: 'Tables' },
        { value: 'power_socket', label: 'Power socket' },
        { value: 'projector', label: 'Projector' },
        { value: 'projector_white_screen', label: 'Projector White Screen' },
        { value: 'black_board', label: 'Black Board' },
        { value: 'left_tv', label: 'Left TV' },
        { value: 'right_tv', label: 'Right TV' },
        { value: 'fans', label: 'Fans' },
        { value: 'lights', label: 'Lights' }
    ],
    'lab': [
        { value: 'tables', label: 'Tables' },
        { value: 'chairs', label: 'Chairs' },
        { value: 'computers', label: 'Computers' },
        { value: 'projector', label: 'Projector' },
        { value: 'projector_white_screen', label: 'Projector White Screen' },
        { value: 'lights', label: 'Lights' },
        { value: 'ac', label: 'AC' },
        { value: 'fans', label: 'Fans' }
    ],
    'washroom': [
        { value: 'toilet', label: 'Toilet' },
        { value: 'toilet_stall', label: 'Toilet stall' },
        { value: 'water', label: 'Water' },
        { value: 'plumbing', label: 'Plumbing' },
        { value: 'cleanliness', label: 'Cleanliness' }
    ],
    'default': [
        { value: 'electrical', label: 'Electrical Issue' },
        { value: 'cleaning', label: 'Cleaning Required' },
        { value: 'furniture', label: 'Furniture Damage' },
        { value: 'ac', label: 'Air Conditioning' },
        { value: 'lights', label: 'Lighting' },
        { value: 'other', label: 'Other' }
    ]
};

/**
 * Handle room selection from the map.
 * @param {string} roomNumber 
 * @param {number} roomId 
 * @param {string} roomName 
 * @param {string} roomType 
 */
export function selectRoom(event, roomNumber, roomId, roomName, roomType) {
    // Update hidden input
    const roomInput = document.getElementById('room_id');
    if (roomInput) roomInput.value = roomId;

    const displayName = roomName || roomNumber;

    // Update display
    const display = document.getElementById('selectedRoomDisplay');
    if (display) {
        display.innerHTML = `
            <div class="room-selected">
                <div class="room-selected-header">
                    <i class="bi bi-check-circle-fill"></i>
                    <span class="room-number">${displayName}</span>
                </div>
                <small class="room-selected-sub">Selected</small>
            </div>
        `;
    }

    // Highlight on map
    document.querySelectorAll('.room-group, .room-poly').forEach(el => el.classList.remove('selected'));
    const roomGroup = document.querySelector(`g[data-room="${roomNumber}"]`);
    if (roomGroup) {
        roomGroup.classList.add('selected');
        const poly = roomGroup.querySelector('.room-poly');
        if (poly) poly.classList.add('selected');
    }

    // Load dynamic fields
    updateIssueTypes(roomType || 'unknown');
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
 * Update the issue type dropdown based on room category.
 * @param {string} roomType 
 */
export function updateIssueTypes(roomType) {
    const issueSelect = document.getElementById('issue_type');
    if (!issueSelect) return;

    initializeIssueDropdown();

    const optionsArray = DYNAMIC_ISSUE_TYPES[roomType] || DYNAMIC_ISSUE_TYPES['default'];

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

    // Update custom animated dropdown UI
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
            itemDiv.textContent = issue.label;
            itemsContainer.appendChild(itemDiv);
        });
    }
}

/**
 * Clear the current room selection.
 */
export function resetRoomSelection() {
    const roomInput = document.getElementById('room_id');
    const display = document.getElementById('selectedRoomDisplay');

    if (roomInput) roomInput.value = '';
    if (display) {
        display.innerHTML = `
            <div class="room-placeholder">
                <i class="bi bi-door-open"></i>
                <span>No room selected</span>
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

    if (issueSelect) {
        issueSelect.innerHTML = '<option value="">Select a Room First</option>';
        issueSelect.value = '';
        issueSelect.disabled = true;
    }
    if (trigger) trigger.disabled = true;
    if (label) label.textContent = 'Select a Room First';
    if (itemsContainer) itemsContainer.innerHTML = '';
}
