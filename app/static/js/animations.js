/**
 * FixLink Native High-Performance Animations Engine
 * Hardware-accelerated 60-120fps with zero main-thread blocking
 */
(() => {
    'use strict';
    const initAnimations = () => {
        // 1. Animate main content on load
        const mainContent = document.querySelector(".main-content");
        if (mainContent && typeof mainContent.animate === "function") {
            const anim = mainContent.animate(
                [
                    { opacity: 0, transform: "translateY(8px)" },
                    { opacity: 1, transform: "translateY(0)" }
                ],
                { duration: 280, easing: "cubic-bezier(0.16, 1, 0.3, 1)" }
            );
            anim.onfinish = () => { mainContent.style.transform = "none"; };
        }

        // 2. Animate cards as they enter viewport via IntersectionObserver
        if ("IntersectionObserver" in window) {
            const cardObserver = new IntersectionObserver(
                (entries, observer) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            if (typeof entry.target.animate === "function") {
                                entry.target.animate(
                                    [
                                        { opacity: 0, transform: "translateY(16px)" },
                                        { opacity: 1, transform: "translateY(0)" }
                                    ],
                                    { duration: 400, easing: "cubic-bezier(0.16, 1, 0.3, 1)", fill: "forwards" }
                                );
                            }
                            observer.unobserve(entry.target);
                        }
                    });
                },
                { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
            );

            document.querySelectorAll(".card").forEach((card) => cardObserver.observe(card));
        }

        // 3. Navbar entrance
        const navbar = document.querySelector(".navbar, .nav-capsule");
        if (navbar && typeof navbar.animate === "function") {
            navbar.animate(
                [
                    { opacity: 0, transform: "translateY(-10px)" },
                    { opacity: 1, transform: "translateY(0)" }
                ],
                { duration: 320, delay: 50, easing: "cubic-bezier(0.16, 1, 0.3, 1)", fill: "forwards" }
            );
        }
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            if ("requestIdleCallback" in window) {
                requestIdleCallback(initAnimations);
            } else {
                requestAnimationFrame(initAnimations);
            }
        });
    } else {
        initAnimations();
    }
})();
