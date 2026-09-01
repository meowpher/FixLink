# Design System & UI Guidelines (Design.md)
## Project: FixLink — MIT-WPU Digital Twin Aesthetic & Brand Specifications

---

## 1. Design Philosophy

FixLink adheres to a **Clean Academic High-Tech Digital Twin** design language. It combines the prestige of the MIT World Peace University brand identity with the tactile responsiveness of modern operational cockpits (glassmorphic surfaces, crisp contrast ratios, and responsive vector floor maps).

### Core Pillars
1. **Clutter-Free Spatial Awareness:** Vector floor plans serve as the anchor of the experience. Controls are tucked into slim side panels and headers.
2. **High-Contrast Dark Mode:** In dark mode, dark backgrounds are not muddy gray; they use deep obsidian tones (`#0F1117`) paired with vivid, high-saturation accents (neon greens, cyan blues, vivid ambers, and clean crimsons) to ensure immediate status recognition.
3. **Tactile Micro-Interactions:** Buttons lift slightly on hover (`translateY(-2px)`), copy icons animate with confirmation checkmarks, and rooms glow upon selection.

---

## 2. Color Palette & Token System

### 2.1 Official University Brand Colors
| Token | Hex Value | RGB / HSL | Usage |
| :--- | :--- | :--- | :--- |
| `--mitwpu-blue` | `#0B4D8C` | `rgb(11, 77, 140)` | Primary brand color, headers, action buttons, active navigation states. |
| `--mitwpu-blue-dark` | `#083968` | `rgb(8, 57, 104)` | Hover states for primary buttons and active sidebar highlights. |
| `--mitwpu-blue-light` | `#1A6AB3` | `rgb(26, 106, 179)` | Focus rings, borders, secondary badges. |
| `--mitwpu-red` | `#C8102E` | `rgb(200, 16, 46)` | University crimson accent, urgent warnings. |
| `--lab-teal` | `#20C997` | `rgb(32, 201, 151)` | High-tech accent, laboratory room designations, digital twin active markers. |

### 2.2 Functional Status Tokens
| Semantic Status | Light Mode Hex | Dark Mode Hex | Purpose |
| :--- | :--- | :--- | :--- |
| **Normal / Fixed / Vacant** | `#28A745` | `#2ED573` (Vivid Mint Green) | Operational rooms, resolved tickets, vacant classrooms. |
| **Issue Reported (Open)** | `#DC3545` | `#FF4757` (High-Vis Crimson) | Unassigned issues, broken assets, critical maintenance. |
| **In Progress** | `#FFC107` | `#FFA502` (Vivid Amber) | Technician currently on site, work in progress. |
| **Assigned / Booked** | `#0D6EFD` | `#3498DB` (Electric Blue) | Technician assigned, scheduled lecture session in progress. |

### 2.3 Surface & Layer Tokens (Dark vs Light)
```css
/* Light Mode */
:root {
    --bg-main: #F5F5F5;
    --bg-card: #FFFFFF;
    --bg-surface: #FFFFFF;
    --text-main: #333333;
    --text-muted: #6C757D;
    --border-color: #E9ECEF;
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.12);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.18);
}

/* Dark Mode (OLED Optimized) */
[data-theme="dark"] {
    --bg-base: #0F1117;       /* Main canvas background */
    --bg-surface: #161B27;    /* Elevated cards and panels */
    --bg-overlay: #1E2535;    /* Popups, dropdowns, and modals */
    --text-primary: #F1F5F9;  /* Headings and primary labels */
    --text-body: #CBD5E1;     /* Main paragraph text */
    --text-muted: #94A3B8;    /* Subtitles and secondary info */
    --border-color: rgba(255, 255, 255, 0.1);
    --shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.4);
    --shadow-md: 0 6px 16px rgba(0, 0, 0, 0.5);
    --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.65);
}
```

---

## 3. Typography Hierarchy

FixLink utilizes the native modern system font stack for zero-latency rendering, crisp text rendering on Retina displays, and zero network bandwidth overhead.

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", Arial, sans-serif;
```

### Type Scale
| Role | Size (Desktop) | Size (Mobile) | Weight | Line Height |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Title (`H1`)** | `2.25rem` (36px) | `1.5rem` (24px) | `700` (Bold) | `1.2` |
| **Section Title (`H2`)**| `1.75rem` (28px) | `1.25rem` (20px) | `600` (Semi-Bold)| `1.25` |
| **Component Title (`H3` / `H4`)**| `1.25rem` (20px) | `1.05rem` (17px) | `600` (Semi-Bold)| `1.3` |
| **Body Text** | `0.95rem` (15px) | `0.88rem` (14px) | `400` (Regular) | `1.5` |
| **Small / Meta Data** | `0.80rem` (12.8px) | `0.75rem` (12px) | `500` (Medium) | `1.4` |
| **Micro Labels / Badges**| `0.70rem` (11.2px) | `0.65rem` (10.4px)| `700` (Bold) | `1.1` |

---

## 4. Component Styling Specifications

### 4.1 Digital Twin SVG Styling
- **Light Mode Rooms:**
  - Base Stroke: `1.5px solid #CED4DA`
  - Base Fill: `rgba(240, 243, 246, 0.7)`
  - Hover Fill: `rgba(11, 77, 140, 0.15)` with `stroke: #0B4D8C; stroke-width: 2.5px;`
- **Dark Mode Rooms (Glow Aesthetic):**
  - Base Stroke: `1.5px solid rgba(255, 255, 255, 0.15)`
  - Base Fill: `rgba(255, 255, 255, 0.04)`
  - Hover Fill: `rgba(32, 201, 151, 0.2)` with `stroke: #20C997; stroke-width: 2.5px; filter: drop-shadow(0 0 8px rgba(32, 201, 151, 0.5));`

### 4.2 Interactive Input Fields & Eye Toggle
- Inputs feature `border-radius: 8px;`, `height: 38px;`, and clean borders.
- Password fields use `.password-input-wrapper` with an integrated `.password-toggle-btn` positioned inside the right edge (`padding-right: 42px`) so the toggle eye icon never breaks onto a second line on mobile screens.

### 4.3 Stat & Action Cards
- Border radius: `14px` - `16px`.
- Translucent backdrop filter in dark mode: `backdrop-filter: blur(16px); background: rgba(22, 27, 39, 0.85);`.
- Hover transition: `all 0.25s cubic-bezier(0.4, 0, 0.2, 1)`.
