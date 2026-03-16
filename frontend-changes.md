# Frontend Changes

## Dark/Light Mode Toggle Button

### What was added

A theme toggle button positioned fixed in the top-right corner of the screen that switches between dark mode (default) and light mode.

### Files changed

**`frontend/index.html`**
- Added a `<button id="themeToggle">` element directly inside `<body>`, before the main `.container`
- Contains two inline SVGs: a sun icon (visible in dark mode) and a moon icon (visible in light mode)
- `aria-label` set to "Toggle light/dark mode" for accessibility

**`frontend/style.css`**
- Added `body.light-mode` CSS variables block with a light color palette (white/slate backgrounds, dark text)
- Added a blanket `transition` on `body *` for smooth color changes across all elements (0.3s ease)
- Added `.theme-toggle` styles: 42px circular button, fixed top-right, matching surface/border colors, hover scale + blue border effect, focus ring
- Added icon visibility rules: `.icon-sun` shown by default (dark mode), `.icon-moon` shown when `body.light-mode` is present

**`frontend/script.js`**
- Added an IIFE `initTheme()` at the top that reads `localStorage('theme')` and applies `light-mode` class on page load (prevents flash of wrong theme)
- Added `setupThemeToggle()` function: toggles `body.light-mode` class, persists preference to `localStorage`, updates `aria-label` dynamically
- Called `setupThemeToggle()` from `DOMContentLoaded` handler

### Design decisions
- Dark mode is the default (matches the existing dark aesthetic)
- Sun icon shown in dark mode → click to go light; moon icon shown in light mode → click to go dark
- Preference persisted in `localStorage` so it survives page refreshes
- Smooth 0.3s CSS transitions on background/border/color for all elements
- Button is keyboard-navigable with visible focus ring (matches existing `--focus-ring` variable)

---

## Light Theme Variant

### What was added

A complete, accessible light theme that overrides all relevant CSS custom properties and fixes hardcoded dark-only colors.

### Files changed

**`frontend/style.css`** — `body.light-mode` block enhanced with:

**Color palette (all WCAG AA compliant):**
| Token | Value | Usage |
|---|---|---|
| `--background` | `#f1f5f9` | Page background (slate-100) |
| `--surface` | `#ffffff` | Cards, sidebar, bubbles |
| `--surface-hover` | `#e2e8f0` | Hover states |
| `--text-primary` | `#0f172a` | Body text (contrast 15:1 on white) |
| `--text-secondary` | `#475569` | Labels, meta text (contrast 6.5:1 on white) |
| `--border-color` | `#cbd5e1` | Dividers and borders |
| `--primary-color` | `#1d4ed8` | Links, buttons, accents |
| `--primary-hover` | `#1e40af` | Darkened hover for primary |
| `--welcome-bg` | `#eff6ff` | Welcome message tinted blue background |

**Targeted element overrides** (hardcoded dark values replaced):
- `code` / `pre` blocks: use `#e2e8f0` background with `#1e293b` text (instead of `rgba(0,0,0,0.2)`)
- `pre` blocks: gain a `1px` border for definition
- Assistant message bubble: gets a `border` + subtle `box-shadow` (otherwise invisible white-on-white)
- Welcome message: uses `--welcome-bg` tinted background + lighter shadow
- Scrollbars: override track/thumb/hover to slate grays
- Error messages: red tones adjusted to `#b91c1c` (dark red, readable on white)
- Success messages: green tones adjusted to `#15803d`
- Source pills and stat items: use `--background` to maintain contrast hierarchy

---

## Theme Switching via `data-theme` Attribute

### What changed

Migrated the theme-switching mechanism from a `body.light-mode` CSS class to a `data-theme="light"` attribute on the `<html>` element — the standard, semantic pattern for CSS custom property theming.

### Files changed

**`frontend/style.css`**
- All `body.light-mode` selectors replaced with `[data-theme="light"]`
- Placing the selector on the root `<html>` element gives it the widest possible CSS scope, matching any descendant regardless of nesting

**`frontend/script.js`**
- IIFE `initTheme()`: now calls `document.documentElement.setAttribute('data-theme', 'light')` instead of toggling a class on `body`
- `setupThemeToggle()`:
  - Reads current theme via `html.getAttribute('data-theme')` (explicit check, no class)
  - Activates light: `html.setAttribute('data-theme', 'light')`
  - Deactivates light: `html.removeAttribute('data-theme')` (falls back to `:root` dark defaults)
  - Syncs `aria-label` on both page load and each click

### Why `data-theme` over a class
- Semantic: an attribute communicates intent ("this element has a theme setting") better than an arbitrary class
- Conventional: matches the pattern used by popular design systems (e.g. shadcn/ui, Radix, Tailwind `dark:` mode)
- Easier to query: `document.documentElement.getAttribute('data-theme')` is unambiguous vs checking for one class among many
