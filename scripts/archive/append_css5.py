import os

css_path = r'd:\FixLink-V1\app\static\css\style.css'

css = """
/* ============================================
   MOBILE CARD DECLUTTER SYSTEM
   ============================================ */
@media (max-width: 767px) {
    .mobile-card-list {
        display: flex !important;
        flex-direction: column;
        gap: 8px;
        margin-top: 1rem;
    }

    .mc-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    /* Top Row */
    .mc-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
    }
    .mc-id-title {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .mc-id {
        font-size: 13px;
        font-weight: 600;
        color: var(--mitwpu-blue);
    }
    .mc-title {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
        word-break: break-word;
    }
    .mc-status .badge {
        font-size: 10px;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 6px;
    }

    /* Body Lines */
    .mc-desc {
        font-size: 12px;
        font-weight: 400;
        color: var(--text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .mc-person-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        background: var(--bg-overlay);
        padding: 6px 8px;
        border-radius: 8px;
    }
    .mc-person-left {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
    }
    .mc-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: var(--mitwpu-blue);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 600;
        flex-shrink: 0;
    }
    .mc-person-info {
        display: flex;
        flex-direction: column;
        min-width: 0;
    }
    .mc-name {
        font-size: 12px;
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .mc-meta {
        font-size: 10px;
        color: var(--text-muted);
    }
    .mc-pill {
        font-size: 10px;
        font-weight: 500;
        background: var(--border-subtle);
        color: var(--text-secondary);
        padding: 2px 6px;
        border-radius: 4px;
        flex-shrink: 0;
    }

    /* Bottom Row */
    .mc-bottom {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 4px;
        padding-top: 8px;
        border-top: 1px dashed var(--border-subtle);
    }
    .mc-date {
        font-size: 11px;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .mc-actions {
        display: flex;
        gap: 5px;
    }
    
    /* 34x34 Action Buttons Rule */
    .mc-btn {
        width: 34px !important;
        height: 34px !important;
        min-height: 34px !important;
        border-radius: 10px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        border: none !important;
    }
    .mc-btn svg, .mc-btn i {
        font-size: 14px !important;
        width: 14px !important;
        height: 14px !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Strict Colors */
    .mc-btn-view { background: #E0F7FA !important; color: #00838F !important; }
    .mc-btn-update { background: #FFF8E1 !important; color: #F57F17 !important; }
    .mc-btn-resolve { background: #E8F5E9 !important; color: #2E7D32 !important; }
    .mc-btn-locate { background: #E8EAF6 !important; color: #3949AB !important; }
    .mc-btn-delete { background: #FFEBEE !important; color: #C62828 !important; }

    /* For dark mode overrides */
    [data-theme="dark"] .mc-btn-view { background: rgba(0, 131, 143, 0.2) !important; color: #4DD0E1 !important; }
    [data-theme="dark"] .mc-btn-update { background: rgba(245, 127, 23, 0.2) !important; color: #FFD54F !important; }
    [data-theme="dark"] .mc-btn-resolve { background: rgba(46, 125, 50, 0.2) !important; color: #81C784 !important; }
    [data-theme="dark"] .mc-btn-locate { background: rgba(57, 73, 171, 0.2) !important; color: #7986CB !important; }
    [data-theme="dark"] .mc-btn-delete { background: rgba(198, 40, 40, 0.2) !important; color: #E57373 !important; }

    /* Hide standard desktop tables */
    .desktop-table-container {
        display: none !important;
    }
}

/* Ensure mobile cards are hidden on desktop */
@media (min-width: 768px) {
    .mobile-card-list {
        display: none !important;
    }
}
"""

with open(css_path, 'a', encoding='utf-8') as f:
    f.write(css)

print("Mobile Card CSS appended")
