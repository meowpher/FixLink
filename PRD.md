# Product Requirement Document (PRD)
## Project: FixLink — MIT-WPU Vyas Building Digital Twin & Smart Maintenance Tracker

---

## 1. Executive Summary
**FixLink** is a campus facility management system and interactive digital twin designed specifically for the Vyas Building at Dr. Vishwanath Karad MIT World Peace University (MIT-WPU), Pune. 

FixLink bridges the gap between campus occupants (students, faculty, staff) and facility maintenance teams by replacing manual, slow complaint registers with an interactive, SVG-based digital twin map, QR code room detection, instant ticket routing, SLA tracking, and faculty classroom management.

---

## 2. Problem Statement & Solution

### 2.1 The Problem
- **Delayed Maintenance:** Broken projectors, faulty air conditioners, lab equipment failures, and washroom hygiene issues take days or weeks to resolve because reporting relies on physical registers or disconnected emails.
- **Ambiguous Location & Asset Details:** Technicians often receive vague reports (e.g., *"3rd floor light not working"*) without knowing the specific room number, fixture ID, or severity.
- **Zero Visibility & Accountability:** Students and faculty receive no feedback on whether their complaint was reviewed, who was assigned, or when it will be fixed.
- **Classroom Clashes & Schedule Blindness:** Faculty members struggle to find vacant lecture halls or labs for ad-hoc sessions, while facility managers lack real-time visibility into building occupancy.

### 2.2 The Solution
FixLink delivers a unified digital twin platform:
1. **Interactive Vector Digital Twin:** Visualizes all 8 floors of the Vyas building with vector SVG layouts that dynamically change colors based on room status (Vacant, Occupied, Issue Reported, In Progress, Fixed).
2. **Instant QR / Direct Reporting:** Users scan a QR code at any room entrance or pick a room on the map to pre-fill the room number, select the issue type, attach a photo, and receive an instant tracked Ticket Reference.
3. **Automated Ticket Assignment & Technician Workflow:** Issues are categorized and routed to specialized technicians (Electrical, Plumbing, AV/IT, Carpentry, HVAC) with built-in SLA timers, complexity tiers, and photo proof upon resolution.
4. **Faculty Timetable & Reservation Hub:** Faculty can sync personal teaching schedules, reserve vacant rooms for ad-hoc lectures with clash detection, and import master timetables via CSV.
5. **Real-Time WebSockets & Notifications:** Instant multi-screen synchronization via Pusher, in-app notification toasts, and audio cues for active tickets and assignments.

---

## 3. Target Users & Personas

| Persona | Primary Goal | Key Touchpoints |
| :--- | :--- | :--- |
| **Students & Campus Visitors** | Report classroom or washroom issues quickly without complex friction. | QR Code entry, Mobile Report page, Ticket Reference modal, Bug report modal. |
| **Faculty Members** | View teaching schedule, check room availability across Vyas floors, book vacant rooms for extra classes, import timetable. | Faculty Portal (`/faculty`), Interactive Agenda, Timetable CSV Sync, Room Tracker. |
| **Maintenance Technicians (Professionals)** | View assigned work orders, accept tasks, track job timers (SLA), request assistance, upload fix proof. | Professional Dashboard (`/professional/dashboard`), Task Details, Camera Upload. |
| **Facility Admins** | Oversee building health, assign technicians, monitor active work orders, review history, manage rooms & assets. | Admin Dashboard (`/admin`), Live Status Map, Room Assignment Panel, User Manager. |
| **Super Admins / Developers** | System configuration, database migrations, security audits, global user roles, telemetry. | Super Admin Developer Dashboard (`/superadmin`). |

---

## 4. Core Features & Capabilities

### 4.1 Digital Twin & Interactive Status Map
- **Multi-Floor Vector Layouts:** SVG-rendered architectural floor plans for Ground Floor through 7th Floor.
- **Live Room State Coloring:** Normal (Green/Neutral), Issue Reported (Red), In Progress (Amber), Assigned (Blue).
- **Interactive Gestures:** Two-finger mobile pinch-to-zoom (0.6x to 4.5x), drag pan, double-tap zoom toggle, and desktop scroll zoom.
- **Deep-Linking:** URL parameters (`?floor=4&room=VY401`) immediately auto-select, zoom, and highlight target rooms with a pulsating glow.

### 4.2 Maintenance Issue Reporting
- **Room Auto-Detection:** Automatically detects room from QR URL (`/report?room=VY402`).
- **Validated Input Controls:** Student PRN verification, MIT-WPU email restriction (`@mitwpu.edu.in`), and camera photo attachment.
- **Reference Tracking:** Generates unique integer Ticket IDs (`#1042`) with one-click clipboard copy.

### 4.3 Technician (Professional) Operations
- **Specialization Matching:** Categorization into Electrician, Plumber, IT/AV Tech, Carpenter, HVAC.
- **Job Lifecycle:** Accept Task $\rightarrow$ Start Timer $\rightarrow$ Set Complexity (Low/Medium/High) $\rightarrow$ Complete with Photo Proof or Cancel with Reason.
- **Collaborative Help Requests:** Technicians can dispatch a help call to request backup from other available technicians in the building.

### 4.4 Faculty Portal & Room Scheduling
- **Weekly Agenda View:** Chronological view of lectures, practicals, and ad-hoc sessions.
- **Ad-Hoc Class Reservation:** Select floor, room, and time window with automated clash prevention against master timetables.
- **CSV Master Timetable Import:** Client-side CSV dry-run parsing and database commit for academic schedule loading.

### 4.5 Administrative Oversight & Analytics
- **Live Floor Status Map with Slide-out Control:** View active issues per room and dispatch technicians in two clicks.
- **Analytical Metrics:** Mean Time to Resolution (MTTR), SLA compliance rate, top failing assets, and volume trends.
- **User Role Management:** Add, edit, verify, promote, or suspend user accounts across Student, Faculty, and Admin tiers.

---

## 5. Non-Functional Requirements & Constraints

1. **Performance & Speed:** Lighthouse Score $\ge$ 95; First Contentful Paint (FCP) $\le$ 1.5s; Largest Contentful Paint (LCP) $\le$ 2.5s.
2. **Mobile-First Responsiveness:** Fully responsive interface optimized for iOS Safari and Android Chrome down to 360px width.
3. **Theme Adaptability:** Complete dual-theme support (Light Mode and OLED Dark Mode `#0F1117`) with no un-styled elements or harsh contrast breaks.
4. **Security & Data Integrity:**
   - Strict CSRF token validation on all POST/PUT/DELETE forms and AJAX requests.
   - HTTP-only, SameSite Lax session cookies.
   - Password encryption using PBKDF2 with SHA-256 via Werkzeug.
   - SQL Injection protection through SQLAlchemy ORM parameter binding.

---

## 6. Success Criteria & KPIs

- **Report Time:** $\le 30$ seconds for a student to report an issue via QR code.
- **Assignment Velocity:** $\le 10$ minutes median time from ticket submission to technician assignment.
- **Mean Time to Resolution (MTTR):** Decreased by 45% compared to paper-based maintenance registers.
- **Faculty Scheduling Friction:** Zero double-booking conflicts across lecture halls in the Vyas building.
- **System Uptime & Stability:** 99.9% uptime during university operating hours (07:00 – 21:00 IST).
