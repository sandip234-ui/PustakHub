# PustakHub UI & Theme Design System

## 1. Overview & Architecture
PustakHub implements a complete, token-based Light/Dark/System theme system designed for maximum visual polish, high-contrast accessibility (WCAG 2.1 AA compliant), responsive consistency, and fluid micro-interactions.

The theme system is built upon **CSS custom properties (tokens)** defined in `frontend/src/index.css`, dynamically controlled by `ThemeContext` (`frontend/src/context/ThemeContext.jsx`), persisted to `localStorage`, and shielded against Flash of Unstyled Content (FOUC) through a synchronous early-bootstrap script in `frontend/index.html`.

---

## 2. Design Tokens Reference

### Core Color Palette (CSS Variables)

| Token Name | Light Theme Value | Dark Theme Value | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| `--bg` | `#f8fafc` (Slate-50) | `#0a0d14` (Deep obsidian) | Root app background |
| `--bg-surface` | `#ffffff` | `#111622` (Rich dark slate) | Card & panel background |
| `--bg-elevated` | `#f1f5f9` (Slate-100) | `#171f30` (Elevated layer) | Hover states, table headers, dropdowns |
| `--bg-subtle` | `#e2e8f0` (Slate-200) | `#1e293b` (Slate-800) | Inactive tabs, disabled inputs, badges |
| `--border` | `rgba(0, 0, 0, 0.08)` | `rgba(255, 255, 255, 0.08)` | Standard card/divider border |
| `--border-strong` | `rgba(0, 0, 0, 0.16)` | `rgba(255, 255, 255, 0.16)` | Active border, modal outlines |
| `--text-primary` | `#0f172a` (Slate-900) | `#f1f5f9` (Slate-100) | High-emphasis headers and primary text |
| `--text-secondary`| `#475569` (Slate-600) | `#94a3b8` (Slate-400) | Secondary body copy and descriptors |
| `--text-muted` | `#64748b` (Slate-500) | `#64748b` (Slate-500) | Placeholders, timestamps, micro-copy |
| `--primary` | `#4f46e5` (Indigo-600) | `#6366f1` (Indigo-500) | Brand primary accents and CTA buttons |
| `--primary-hover`| `#4338ca` (Indigo-700) | `#4f46e5` (Indigo-600) | Hover state for primary buttons |
| `--primary-soft` | `rgba(79, 70, 229, 0.08)` | `rgba(99, 102, 241, 0.12)`| Accent badges, active nav pills |
| `--accent` | `#06b6d4` (Cyan-500) | `#22d3ee` (Cyan-400) | Secondary highlights, metrics accents |
| `--success` | `#10b981` (Emerald-500) | `#10b981` (Emerald-500) | Positive feedback, active badges |
| `--warning` | `#f59e0b` (Amber-500) | `#f59e0b` (Amber-500) | Overdue warnings, alerts |
| `--danger` | `#ef4444` (Rose-500) | `#f43f5e` (Rose-500) | Errors, destructive actions, fines |

---

## 3. Light / Dark / System Modes & Anti-FOUC

### Theme Resolution Logic
1. **Light Mode**: Forces `light` class on `document.documentElement` and disables dark variable tokens.
2. **Dark Mode**: Forces `dark` class on `document.documentElement` and enables rich dark tokens.
3. **System Mode**: Dynamically binds a `prefers-color-scheme: dark` media query listener and applies the host operating system's theme preference automatically.

### Persistence & Storage Key
- Stored key: `pustakhub_theme` in browser `localStorage`.
- Default preference: `system` (or fallback to `dark`).

### Anti-FOUC Execution
In `frontend/index.html`, an inline synchronous `<script>` executes immediately inside `<head>` prior to DOM rendering or stylesheet loading:
```html
<script>
  (function() {
    try {
      const stored = localStorage.getItem('pustakhub_theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = stored === 'light' ? 'light' : (stored === 'dark' ? 'dark' : (prefersDark ? 'dark' : 'light'));
      document.documentElement.classList.add(theme);
    } catch (e) {
      document.documentElement.classList.add('dark');
    }
  })();
</script>
```
This eliminates all flash-of-unstyled-content during hard reloads across both light and dark modes.

---

## 4. Dashboard Architecture & Metrics Verification

### Role-Specific Dashboard Views
- **ADMIN / LIBRARIAN**:
  - Live circulation KPIs (Total Titles, Active Borrowings, Overdue Loans, Pending Fines).
  - Quick Circulation Actions (Issue Book modal trigger, Book Catalog shortcut, Fine Management).
  - Live Library Activity Stream (realtime event subscriptions).
  - Audit Trail overview (staff only).
- **STUDENT / PATRON**:
  - Personal Loan Status (My Active Loans, Overdue Items, Outstanding Fines).
  - Quick Book Search & Reservation actions.
  - Personal History & Due Date Notifications.
- **GUEST / PUBLIC**:
  - Public catalog exploration, search hero, call to register/login.

### Data Integrity Guarantee
All statistics are populated directly from real, backend REST endpoints:
- `GET /api/v1/circulation/stats`
- `GET /api/v1/circulation/borrowings`
- `GET /api/v1/fines`
- `GET /api/v1/catalog/books`
- `GET /api/v1/audit/logs`

No fake trends, synthetic sparklines, or hardcoded mock percentages are rendered.

---

## 5. Animation Strategy & External UI Stack

### Libraries
- **`lucide-react`**: Provides clean, consistent, scalable iconography with unified stroke widths (1.5px / 1.75px / 2px) across navigation, tables, badges, action buttons, and stat panels.
- **`motion` (Framer Motion)**: Powers smooth page transitions, floating modal entries, accordion reveals, and responsive menu animations with hardware-accelerated transforms.

### Hover.dev-Inspired Design Enhancements
- **Bento Grids**: Hierarchical, modular dashboard cards with subtle borders and gentle surface elevations.
- **Micro-Glows & Radiant Badges**: Glow badges and accent borders (`box-shadow: 0 0 15px -3px rgba(99, 102, 241, 0.15)`).
- **Smooth Elevation on Hover**: Cards elevate slightly (`translateY(-2px)`) with softened shadow transitions on pointer focus.

---

## 6. Accessibility & Responsive Standards

- **Contrast Ratios**: Standard text meets a minimum contrast ratio of 4.5:1 against surfaces in both Light and Dark modes.
- **Focus Rings**: Accessible focus indicators (`focus-visible:ring-2 focus-visible:ring-indigo-500`) applied to all interactive controls.
- **Responsive Breakpoints**:
  - `390px` (Mobile portrait): Single-column stacked layouts, condensed tables, bottom-sheet style overlays, full-width modal triggers.
  - `768px` (Tablet): Two-column stat grids, drawer navigation.
  - `1024px` (Small desktop / Laptop): Standard bento grid dashboard, expanded sidebar/navbar.
  - `1280px` - `1440px` (Large display): Fluid container bounds with optimal content padding.
