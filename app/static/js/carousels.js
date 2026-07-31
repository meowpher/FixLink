document.addEventListener("DOMContentLoaded", () => {
    if (typeof gsap === 'undefined' || typeof Draggable === 'undefined') return;

    const stackContainer = document.getElementById("cardStackContainer");
    if (!stackContainer) return;

    const cards = gsap.utils.toArray(".stack-card");
    if (cards.length === 0) return;

    // Initial arrangement of the card stack for 3D Coverflow
    cards.forEach((card, i) => {
        gsap.set(card, {
            zIndex: cards.length - i,
            scale: 1 - (i * 0.05),
            y: i * 20,
            z: -i * 50,
            rotationX: i * 5,
            opacity: 1 - (i * 0.25)
        });
    });

    let isAnimating = false;

    // We make the top card draggable
    function initDraggable() {
        const topCard = cards[0];
        
        Draggable.create(topCard, {
            type: "x,y",
            edgeResistance: 0.8,
            bounds: stackContainer,
            onDragStart: function() {
                isAnimating = true;
                // Add a slight lift effect when grabbing
                gsap.to(topCard, { scale: 1.05, rotationX: -10, duration: 0.2, ease: "power2.out" });
            },
            onDrag: function() {
                // Add tilt based on drag position for 3D feel
                gsap.to(topCard, {
                    rotationY: this.x * 0.05,
                    rotationX: -this.y * 0.05 - 10,
                    duration: 0.1
                });
            },
            onDragEnd: function() {
                // If dragged past a threshold, swipe it away
                if (Math.abs(this.x) > 100 || Math.abs(this.y) > 80) {
                    const dirX = this.x > 0 ? window.innerWidth : -window.innerWidth;
                    const dirY = this.y > 0 ? window.innerHeight : -window.innerHeight;
                    
                    gsap.to(topCard, {
                        x: dirX * 0.5,
                        y: dirY * 0.5,
                        opacity: 0,
                        rotation: this.x * 0.1,
                        rotationY: this.x * 0.1,
                        duration: 0.5,
                        ease: "power2.in",
                        onComplete: () => {
                            // Move top card to the back of the array
                            cards.push(cards.shift());
                            
                            // Reorder DOM to match array
                            stackContainer.prepend(topCard);
                            
                            // Reset the swiped card's styles
                            gsap.set(topCard, { x: 0, y: 0, rotation: 0, rotationX: 0, rotationY: 0, z: 0 });
                            
                            // Animate all cards to their new positions
                            reorderCards();
                        }
                    });
                } else {
                    // Snap back with spring physics
                    gsap.to(topCard, {
                        x: 0,
                        y: 0,
                        rotation: 0,
                        rotationX: 0,
                        rotationY: 0,
                        scale: 1,
                        duration: 0.8,
                        ease: "elastic.out(1, 0.4)", // Spring physics!
                        onComplete: () => { isAnimating = false; }
                    });
                }
            }
        });
    }

    function reorderCards() {
        // Kill existing draggables to re-init on the new top card
        Draggable.get(cards[cards.length - 1])?.kill(); // the one that was just swiped
        
        cards.forEach((card, i) => {
            gsap.to(card, {
                zIndex: cards.length - i,
                scale: 1 - (i * 0.05),
                y: i * 20,
                z: -i * 50,
                x: 0, // Reset X position
                rotationX: i * 5,
                rotationY: 0,
                opacity: 1 - (i * 0.25),
                duration: 0.6,
                ease: "back.out(1.2)", // Spring physics!
                onComplete: () => {
                    if (i === 0) {
                        isAnimating = false;
                        initDraggable(); // Re-init on the new top card
                    }
                }
            });
        });
    }

    // Initialize
    initDraggable();
});
