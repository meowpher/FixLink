document.addEventListener("DOMContentLoaded", () => {
    if (typeof gsap === 'undefined' || typeof Flip === 'undefined') return;

    gsap.registerPlugin(Flip);

    // Simulate a network request for data handoff
    setTimeout(() => {
        const statCards = document.querySelectorAll('.advanced-stat-card');
        
        statCards.forEach(card => {
            const overlay = card.querySelector('.skeleton-overlay');
            const content = card.querySelector('.stat-content');
            
            if (overlay && content) {
                // Record the current state of the card for layout morphing
                const state = Flip.getState(card);
                
                // Swap classes to trigger layout change
                overlay.style.display = 'none';
                content.classList.add('loaded'); // CSS might change height or display
                content.style.opacity = '1';
                content.style.visibility = 'visible';

                // Morph layout smoothly in case the loaded content alters the card's dimensions
                Flip.from(state, {
                    duration: 0.6,
                    ease: "power3.inOut",
                    absolute: true, // Smooths out jumps during height changes
                    onEnter: elements => gsap.fromTo(elements, {opacity: 0, scale: 0.95}, {opacity: 1, scale: 1, duration: 0.4, delay: 0.2}),
                    onComplete: () => {
                        // Notify the dashboard stats script that data is ready to be animated
                        card.dispatchEvent(new CustomEvent('dataLoaded', { bubbles: true }));
                    }
                });
            }
        });
    }, 1200); // 1.2s mock network delay
});
