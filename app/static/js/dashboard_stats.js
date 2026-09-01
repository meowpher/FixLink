document.addEventListener("DOMContentLoaded", () => {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    document.querySelectorAll('.advanced-stat-card').forEach(card => {
        // Setup ScrollTrigger for each card
        ScrollTrigger.create({
            trigger: card,
            start: "top 90%", // Trigger when the top of the card is 90% down the viewport
            once: true, // Only animate once
            onEnter: () => {
                const content = card.querySelector('.stat-content');
                if (content && !content.classList.contains('loaded')) {
                    // Wait for skeleton morph if it hasn't loaded yet
                    card.addEventListener('dataLoaded', () => animateCard(card), { once: true });
                } else {
                    animateCard(card);
                }
            }
        });
    });

    function animateCard(card) {
        const counterEl = card.querySelector('.animated-counter');
        const targetValueStr = card.getAttribute('data-target-value') || "0";
        const isFloat = targetValueStr.includes('.');
        const targetValue = parseFloat(targetValueStr);

        if (counterEl && !isNaN(targetValue)) {
            let obj = { val: 0 };
            gsap.to(obj, {
                val: targetValue,
                duration: 2.5,
                ease: "power2.out",
                onUpdate: () => {
                    counterEl.innerText = isFloat ? obj.val.toFixed(1) : Math.floor(obj.val);
                }
            });
        }

        const path = card.querySelector('.trend-path');
        if (path) {
            // Generate a random dynamic-looking path for the mock graph
            const points = [
                [0, 25],
                [20, 25 - Math.random() * 20],
                [40, 25 - Math.random() * 20],
                [60, 25 - Math.random() * 20],
                [80, 25 - Math.random() * 20],
                [100, 5 + Math.random() * 10]
            ];
            const d = `M${points[0][0]},${points[0][1]} C${points[1][0]},${points[1][1]} ${points[2][0]},${points[2][1]} ${points[3][0]},${points[3][1]} S${points[4][0]},${points[4][1]} ${points[5][0]},${points[5][1]}`;
            path.setAttribute('d', d);

            // Calculate length to animate dashoffset properly
            const pathLength = path.getTotalLength() || 150;
            path.style.strokeDasharray = pathLength;
            path.style.strokeDashoffset = pathLength;

            gsap.to(path, {
                strokeDashoffset: 0,
                duration: 2,
                ease: "power2.out",
                delay: 0.2 // slight delay after numbers start
            });
        }
    }
});
