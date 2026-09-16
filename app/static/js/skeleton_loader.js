document.addEventListener("DOMContentLoaded", () => {
    const statCards = document.querySelectorAll('.advanced-stat-card');
    if (!statCards || statCards.length === 0) return;

    // Fast, smooth handoff from skeleton shimmer to card content
    setTimeout(() => {
        statCards.forEach(card => {
            const overlay = card.querySelector('.skeleton-overlay');
            const content = card.querySelector('.stat-content');
            
            if (overlay) {
                overlay.style.transition = 'opacity 0.3s ease';
                overlay.style.opacity = '0';
                overlay.style.pointerEvents = 'none';
                setTimeout(() => {
                    overlay.style.display = 'none';
                }, 300);
            }
            if (content) {
                content.classList.add('loaded');
                content.style.opacity = '1';
                content.style.visibility = 'visible';
            }

            // Notify dashboard stats listeners that data is ready to be animated
            card.dispatchEvent(new CustomEvent('dataLoaded', { bubbles: true }));
        });
    }, 200);
});
