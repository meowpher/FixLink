# Application Flow & UX Architecture (AppFlow)
## Project: FixLink — Interaction Models and User Journeys

---

## 1. Global Navigation & Layout Architecture

FixLink features an adaptive dual-navigation model tailored for both Desktop workstations and Mobile devices.

```
+-------------------------------------------------------------------------+
|                              Desktop View                               |
|  [Logo: MIT-WPU FixLink] [Home] [Report] [Status Map] [Faculty] [Theme] |
+-------------------------------------------------------------------------+

+-------------------------------------------------------------------------+
|                              Mobile View                                |
|  Top Header:    [FixLink Logo]                   [Bug Icon] [Theme Icon] |
|  Main Body:     [Active View / Form / Responsive Interactive SVG Map]   |
|  Bottom Nav:    [Home]     [Report]     [Map]     [Faculty]     [Profile]|
+-------------------------------------------------------------------------+
```

### 1.1 Responsive Mobile Header & Bottom Navigation
- **Mobile Top Bar (`#mobile-top-bar`):** Displays the MIT-WPU FixLink brand on the left and quick-action icon controls on the right:
  - **Theme Toggle Button:** One-tap switch between Light and OLED Dark mode.
  - **Bug Report Button (`#mobileBugBtn`):** Instantly triggers the floating Bug Report modal without leaving the current workflow.
- **Mobile Bottom Navigation:** Fixed bottom navigation bar providing primary tap targets for Home, Issue Reporting, Status Map, Faculty Schedule, and Account Profile.

---

## 2. Core User Flows & Journeys

### 2.1 Student / Visitor: Issue Reporting Flow
```mermaid
flowchart TD
    A[User Scans Room QR Code] -->|URL: /report?room=VY402| B[Report Page Loads]
    C[User Enters /report manually] --> D[User Selects Floor on Interactive SVG Map]
    D --> E[User Clicks Target Room on Map]
    E --> B
    B --> F[Room Detected & Highlighted]
    F --> G[Select Issue Type: Projector, Light, AC, PC, Hygiene]
    G --> H[Enter Description & Optional Photo Attachment]
    H --> I[Input Verified Student PRN & MIT-WPU Email]
    I --> J[Click 'Submit Report']
    J --> K{AJAX Validation}
    K -->|Success| L[Display 'Thank You!' Modal with #TicketId]
    K -->|Failure| M[Show Inline Field Validation Error Alert]
    L --> N[Copy Ticket ID to Clipboard]
    L --> O[Option to Submit Another or Close]
```

### 2.2 Facility Admin: Dispatch & Status Monitoring Flow
```mermaid
flowchart TD
    A[Admin Logs in via /login] --> B[Admin Dashboard]
    B --> C[View Live KPI Cards: Open, In Progress, Fixed, Overdue]
    B --> D[Open Live Status Map /admin/status-map]
    D --> E[Select Floor from Sidebar]
    E --> F[Interactive Digital Twin Renders]
    F -->|Red Room Highlighted| G[Click Room Polygon]
    G --> H[Slide-out Drawer: Room Details & Active Tickets]
    H --> I[Click 'Assign Technician']
    I --> J[Select Available Technician by Category]
    J --> K[System Emits Pusher WebSocket Event]
    K --> L[Room State Transitions to 'Assigned' - Blue Stroke]
```

### 2.3 Technician (Professional): Work Order Lifecycle Flow
```mermaid
flowchart TD
    A[Technician Logs in /professional/dashboard] --> B[View Task Queue]
    B --> C{Pusher Alert: New Task Assigned}
    C --> D[Review Room, Issue Type, and Reporter Photo]
    D --> E[Tap 'Start Job']
    E --> F[Select Task Complexity: Low, Medium, High]
    F --> G[SLA Countdown Timer Begins]
    G --> H{Need Backup?}
    H -->|Yes| I[Tap 'Request Help' - Alerts Other Technicians]
    H -->|No| J[Perform Maintenance Fix]
    J --> K[Capture & Upload Completion Photo Proof]
    K --> L[Tap 'Resolve Issue']
    L --> M[Ticket Marked 'Fixed', Map Updated to Green]
```

### 2.4 Faculty Portal: Timetable & Classroom Booking Flow
```mermaid
flowchart TD
    A[Faculty Logs in /faculty] --> B[Upcoming Agenda Dashboard]
    B --> C[View Today's Scheduled Lectures]
    B --> D[Need Ad-Hoc Lecture Room?]
    D --> E[Tap 'Book a Class']
    E --> F[Select Date, Time Window, & Capacity]
    F --> G{Clash Detection Engine}
    G -->|Conflict Detected| H[Highlight Clashing Timetable Slot]
    G -->|Available| I[Confirm Reservation]
    I --> J[Room Occupancy Marked Occupied on Status Map]
    B --> K[Tap 'Import Timetable']
    K --> L[Upload Department CSV File]
    L --> M[Run Dry-Run Preview & Error Checker]
    M --> N[Confirm & Commit Schedule to Database]
```

---

## 3. UI State Transitions & Feedback

| Component | Default State | Hover / Active State | Error State | Loading State |
| :--- | :--- | :--- | :--- | :--- |
| **SVG Room Polygon** | Low opacity fill (15%) with distinct boundary stroke. | Glow highlight (35% opacity), stroke expands to 3px. | Red flashing outline if critical issue open. | Shimmer skeleton loader across floor map container. |
| **Submit Buttons** | Solid MIT-WPU Blue pill button. | Darker shade, slight upward translateY(-2px). | Disabled with alert banner above form. | Rotating spinner with text "Submitting...". |
| **Status Badge** | Compact pill with status icon. | Tooltip displaying technician name or deadline. | Red `#dc3545` badge with warning icon. | Pulsing opacity badge during background sync. |
| **Ticket Reference Card** | Centered rounded card with `#0000`. | `#1042` with one-tap clipboard copy button. | `#----` fallback (zero `#undefined`). | Shimmer pulse before response parse. |
