document.addEventListener("DOMContentLoaded", () => {
    const curtain = document.getElementById("page-transition-curtain");
    if (typeof gsap === 'undefined' || !curtain) return;

    // We no longer intercept route clicks.
    // The curtain effect is strictly bound to the theme toggle switch.

    window.performThemeCurtainTransition = function(isDark, onSwitchThemeCallback) {
        // Drop curtain
        gsap.to(curtain, {
            scaleY: 1,
            duration: 0.6,
            ease: "power3.inOut",
            transformOrigin: "top",
            onComplete: () => {
                // Swap the theme behind the curtain
                if (typeof onSwitchThemeCallback === 'function') {
                    onSwitchThemeCallback(isDark);
                }

                // Update curtain color dynamically if needed based on the new theme
                // (It usually inherits via CSS variables automatically once body is updated)

                // Lift curtain
                gsap.to(curtain, {
                    scaleY: 0,
                    duration: 0.6,
                    ease: "power3.inOut",
                    transformOrigin: "bottom"
                });
            }
        });
    };
});
