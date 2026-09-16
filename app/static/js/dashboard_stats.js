document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll('.advanced-stat-card');
    if (!cards || cards.length === 0) return;

    function animateCard(card) {
        if (card.dataset.animated === 'true') return;
        card.dataset.animated = 'true';

        const content = card.querySelector('.stat-content');
        if (content) {
            content.classList.add('loaded');
            content.style.opacity = '1';
        }

        const counterEl = card.querySelector('.animated-counter');
        const targetValueStr = card.getAttribute('data-target-value') || "0";
        const isFloat = targetValueStr.includes('.');
        const targetValue = parseFloat(targetValueStr);

        if (counterEl && !isNaN(targetValue)) {
            if (window.gsap) {
                let obj = { val: 0 };
                gsap.to(obj, {
                    val: targetValue,
                    duration: 1.5,
                    ease: "power2.out",
                    onUpdate: () => {
                        counterEl.innerText = isFloat ? obj.val.toFixed(1) : Math.floor(obj.val);
                    }
                });
            } else {
                const start = performance.now();
                const duration = 1200;
                function step(now) {
                    const progress = Math.min((now - start) / duration, 1);
                    const current = targetValue * (1 - Math.pow(1 - progress, 3));
                    counterEl.innerText = isFloat ? current.toFixed(1) : Math.floor(current);
                    if (progress < 1) requestAnimationFrame(step);
                }
                requestAnimationFrame(step);
            }
        }

        const path = card.querySelector('.trend-path');
        if (path) {
            try {
                const pathLength = path.getTotalLength ? path.getTotalLength() : 150;
                path.style.strokeDasharray = pathLength;
                path.style.strokeDashoffset = pathLength;
                path.style.transition = 'stroke-dashoffset 1.2s ease-out';
                requestAnimationFrame(() => {
                    path.style.strokeDashoffset = '0';
                });
            } catch (e) {
                path.style.strokeDashoffset = '0';
            }
        }
    }

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCard(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => observer.observe(card));
    } else {
        cards.forEach(card => animateCard(card));
    }
});
