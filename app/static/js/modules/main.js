/**
 * Map Main Module - Application entry point and coordination.
 */

import * as api from './api.js';
import * as render from './render.js';
import * as ui from './ui.js';

document.addEventListener('DOMContentLoaded', () => {

    // Defer heavy DOM manipulation (like SVG rendering) to avoid blocking initial paint and causing forced reflows
    const runHeavyInit = () => {
        initializeFloorMap();
        initializeReportForm();
        initializeValidation();
        ui.initializeIssueDropdown();
    };

    if ('requestIdleCallback' in window) {
        requestIdleCallback(runHeavyInit, { timeout: 1000 });
    } else {
        setTimeout(runHeavyInit, 100);
    }
});

/**
 * Initialize floor selection and map loading.
 */
function initializeFloorMap() {
    const floorSelect = document.getElementById('floorSelect');
    const floorMapContainer = document.getElementById('floorMapContainer');
    if (!floorSelect || !floorMapContainer) return;

    let hasLoadedInitialData = false;

    floorSelect.addEventListener('change', async function () {
        const floorId = this.value;
        const option = this.options[this.selectedIndex];
        
        if (!floorId) {
            renderPlaceholder(floorMapContainer);
            return;
        }

        try {
                if (!hasLoadedInitialData && window.initialRoomsData && floorId == window.preSelectedFloor) {
                hasLoadedInitialData = true;
                render.renderFloorMap(floorMapContainer, window.initialRoomsData, option.dataset.level, false, true);
            } else {
                renderLoading(floorMapContainer);
                const rooms = await api.fetchRoomsByFloor(floorId);
                render.renderFloorMap(floorMapContainer, rooms, option.dataset.level, false, true);
            }
        } catch (error) {
            renderError(floorMapContainer, error.message);
        }
    });

    // Handle pre-selection (Flask injection)
    if (typeof window.preSelectedFloor !== 'undefined' && window.preSelectedFloor) {
        floorSelect.value = window.preSelectedFloor;
        floorSelect.dispatchEvent(new Event('change'));
    }
}

/**
 * Initialize maintenance report form submission.
 */
function initializeReportForm() {
    const reportForm = document.getElementById('reportForm');
    if (!reportForm) return;

    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        const formData = new FormData(reportForm);

        try {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span style="display:flex;align-items:center;justify-content:center;gap:0.5rem"><i class="bi bi-hourglass-split"></i>Submitting...</span>';
            }

            const response = await fetch(reportForm.action, {
                method: 'POST',
                body: formData,
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                }
            });

            const data = await response.json();

            if (data.success) {
                if (window.showSuccessModal) window.showSuccessModal(data.ticket_id);
                reportForm.reset();
                ui.resetRoomSelection();
            } else {
                if (window.showErrors) window.showErrors(data.errors || [data.error]);
            }
        } catch (error) {
            console.error('Submission error:', error);
            if (window.showErrors) window.showErrors(['Project could not be submitted. Check network.']);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span style="display:flex;align-items:center;justify-content:center;gap:0.5rem"><i class="bi bi-send-fill"></i>Submit Report</span>';
            }
        }
    });
}

/**
 * Basic validation hooks.
 */
function initializeValidation() {
    const prnInput = document.getElementById('prn');
    if (prnInput) {
        prnInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
}

// Visual Helpers

function renderPlaceholder(container) {
    container.innerHTML = `
        <div class="floor-map-placeholder">
            <i class="bi bi-building display-1 text-muted"></i>
            <p class="mt-3">Select a floor to view the interactive map</p>
        </div>
    `;
}

function renderLoading(container) {
    container.innerHTML = `
        <div class="floor-map-placeholder">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-3">Loading floor plan...</p>
        </div>
    `;
}

function renderError(container, message) {
    container.innerHTML = `
        <div class="floor-map-placeholder">
            <i class="bi bi-exclamation-triangle display-1 text-danger"></i>
            <p class="mt-3">Error: ${message}</p>
        </div>
    `;
}
