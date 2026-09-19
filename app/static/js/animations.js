/**
 * FixLink Native High-Performance Animations Engine
 * Uses native Web Animations API (WAAPI) and IntersectionObserver
 * 0 external network requests, hardware-accelerated 60-120fps
 */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Animate main content on load
    const mainContent = document.querySelector(".main-content");
    if (mainContent && typeof mainContent.animate === "function") {
        mainContent.animate(
            [
                { opacity: 0, transform: "translateY(16px)" },
                { opacity: 1, transform: "translateY(0)" }
            ],
            {
                duration: 500,
                easing: "cubic-bezier(0.16, 1, 0.3, 1)",
                fill: "forwards"
            }
        );
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
                                    { opacity: 0, transform: "translateY(24px)" },
                                    { opacity: 1, transform: "translateY(0)" }
                                ],
                                {
                                    duration: 500,
                                    easing: "cubic-bezier(0.16, 1, 0.3, 1)",
                                    fill: "forwards"
                                }
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

    // 3. Micro-animations for buttons on hover
    const buttons = document.querySelectorAll(".btn");
    buttons.forEach((btn) => {
        btn.addEventListener("mouseenter", () => {
            if (typeof btn.animate === "function") {
                btn.animate(
                    [
                        { transform: "scale(1)" },
                        { transform: "scale(1.025)" }
                    ],
                    { duration: 180, fill: "forwards", easing: "ease-out" }
                );
            }
        });
        btn.addEventListener("mouseleave", () => {
            if (typeof btn.animate === "function") {
                btn.animate(
                    [
                        { transform: "scale(1.025)" },
                        { transform: "scale(1)" }
                    ],
                    { duration: 180, fill: "forwards", easing: "ease-out" }
                );
            }
        });
    });

    // 4. Navbar entrance
    const navbar = document.querySelector(".navbar, .nav-capsule");
    if (navbar && typeof navbar.animate === "function") {
        navbar.animate(
            [
                { opacity: 0, transform: "translateY(-14px)" },
                { opacity: 1, transform: "translateY(0)" }
            ],
            {
                duration: 400,
                delay: 100,
                easing: "cubic-bezier(0.16, 1, 0.3, 1)",
                fill: "forwards"
            }
        );
    }
});
