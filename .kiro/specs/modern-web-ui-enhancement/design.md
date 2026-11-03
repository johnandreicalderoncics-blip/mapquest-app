# Design Document: Modern Web UI Enhancement

## Overview

This design document specifies the technical architecture for transforming the MapQuest web frontend into a modern, Google Maps-inspired interface. The enhancement maintains the existing Flask/Jinja2/vanilla JavaScript stack while introducing a comprehensive design system, smooth animations, and responsive layouts across all screen sizes.

### Design Goals

1. **Visual Excellence**: Implement a modern design system with professional color palette, typography, and spacing
2. **Smooth Interactions**: Create 60fps animations using CSS transforms and hardware acceleration
3. **Universal Accessibility**: Ensure WCAG 2.1 AA compliance with comprehensive keyboard navigation and ARIA support
4. **Responsive Design**: Provide optimal experiences across mobile (≤768px), tablet (768-1024px), and desktop (>1024px) viewports
5. **Performance**: Maintain sub-100ms interaction response times and smooth scrolling
6. **Maintainability**: Use modular CSS architecture and well-structured JavaScript modules

### Technical Constraints

- **Backend**: Flask with Jinja2 templates (no changes to Python backend)
- **Frontend**: Vanilla JavaScript (no frameworks), modern CSS features
- **Map Library**: Leaflet.js 1.9.4 (existing)
- **Browser Support**: Modern browsers with CSS Grid, Custom Properties, and ES6 support
- **No Build Step**: All assets loaded directly, no compilation required

### Integration Points

The design integrates with existing system components:

- `backend/services.py`: Provides route data via `get_route()` function
- `backend/formatting.py`: Formats distances, times, and fuel estimates
- `templates/index.html`: Jinja2 template for server-side rendering
- `static/style.css`: CSS styling (complete replacement)
- `static/app.js`: JavaScript enhancements (significant expansion)

## Architecture

### High-Level Architecture

The modern web UI enhancement maintains a clean separation of concerns between presentation (HTML/CSS), behavior (JavaScript), and data (Flask backend). The architecture follows a component-based approach where each UI element is self-contained with its own styles, behavior, and state management.

**Architectural Layers:**

1. **Presentation Layer** (Templates/CSS): Jinja2 templates render initial HTML structure; CSS provides all visual styling
2. **Behavior Layer** (JavaScript): Vanilla JS modules handle interactions, animations, and state management
3. **Data Layer** (Flask Backend): Python backend processes route requests and formats data (unchanged)

**Communication Flow:**
```
User Action → Form Controller → Flask POST /route → Backend Services → 
API Call → Response Processing → Template Render → Animation Controller → 
Results Display
```

### Component Hierarchy

```
Application Root
├── Layout Shell
│   ├── Form Sidebar Component
│   │   ├── Input Fields (origin, destination)
│   │   ├── Unit Controls (metric/imperial radio group)
│   │   ├── Travel Mode Controls (car/bike/walk radio group)
│   │   └── Submit Button with Loading State
│   ├── Map Component
│   │   ├── Leaflet Map Instance
│   │   ├── Custom Zoom Controls
│   │   ├── Route Polyline Layer
│   │   └── Custom Markers (origin/destination)
│   └── Results Panel Component
│       ├── Trip Summary Card
│       │   ├── Metrics Grid (distance, duration, fuel)
│       │   └── Route Information
│       └── Turn-by-Turn Directions List
│           └── Direction Step Cards
├── Toast Notification System
└── Loading Overlay System
```

### CSS Architecture

**File Structure:**
```
static/
├── style.css (main stylesheet, ~800-1000 lines)
│   ├── 1. CSS Custom Properties (design tokens)
│   ├── 2. Base Styles & Reset
│   ├── 3. Layout System (Grid & Flexbox)
│   ├── 4. Component Styles
│   ├── 5. Animation Keyframes
│   ├── 6. Responsive Breakpoints
│   ├── 7. Dark Mode Overrides
│   └── 8. Print Styles
```

**Methodology**: BEM (Block Element Modifier) with utility classes for common patterns

**Example BEM Structure:**
```css
.form-sidebar { }                    /* Block */
.form-sidebar__input { }             /* Element */
.form-sidebar__input--focused { }    /* Modifier */
```

### JavaScript Architecture

**Module Structure:**
```javascript
// app.js structure (~500-700 lines)
(function() {
  'use strict';
  
  // 1. Configuration & Constants
  const CONFIG = { ... };
  
  // 2. State Management
  const state = { ... };
  
  // 3. Utility Functions
  const utils = { ... };
  
  // 4. Animation Controller
  const animations = { ... };
  
  // 5. Component Controllers
  const formController = { ... };
  const mapController = { ... };
  const resultsController = { ... };
  
  // 6. Toast Notification System
  const toastManager = { ... };
  
  // 7. Theme Manager
  const themeManager = { ... };
  
  // 8. Initialization
  function init() { ... }
  
  // 9. Event Listeners
  document.addEventListener('DOMContentLoaded', init);
})();
```

## Components and Interfaces

### Component Overview

The web UI consists of five primary components, each responsible for a specific aspect of the user experience:

1. **Form Sidebar Component**: User input for route parameters
2. **Map Component**: Interactive Leaflet.js map display with route visualization
3. **Results Panel Component**: Trip summary and turn-by-turn directions
4. **Toast Notification Component**: Transient feedback messages
5. **Theme Manager Component**: Light/dark mode switching

### Component Interfaces

**Form Sidebar Component Interface:**
```javascript
interface FormSidebarController {
  init(): void;
  validateForm(): boolean;
  validateField(input: HTMLInputElement): boolean;
  showLoadingState(): void;
  updateSegmentedControl(control: HTMLElement): void;
}
```

**Map Component Interface:**
```javascript
interface MapController {
  init(): void;
  initializeMap(element: HTMLElement): void;
  displayRoute(points: Array<[number, number]>): void;
  addCustomMarkers(points: Array<[number, number]>): void;
  showLoadingState(text: string): void;
  hideLoadingState(): void;
}
```

**Results Panel Component Interface:**
```javascript
interface ResultsController {
  init(): void;
  showResults(): void;
  hideResults(): void;
  handleStepClick(stepIndex: number): void;
  animateResults(): void;
}
```

**Toast Manager Interface:**
```javascript
interface ToastManager {
  init(): void;
  show(options: ToastOptions): HTMLElement;
  dismiss(toast: HTMLElement): void;
}

interface ToastOptions {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number;
}
```

**Theme Manager Interface:**
```javascript
interface ThemeManager {
  init(): void;
  setTheme(theme: 'light' | 'dark'): void;
  toggleTheme(): void;
}
```

### Component Dependencies

**Dependency Graph:**
```
FormSidebarController
  ↓
  ├─→ ToastManager (for validation feedback)
  └─→ AnimationController (for button ripples)

MapController
  ↓
  ├─→ Leaflet.js (external dependency)
  ├─→ AnimationController (for polyline drawing)
  └─→ ThemeManager (for map tile styling)

ResultsController
  ↓
  ├─→ MapController (for step click interactions)
  ├─→ AnimationController (for panel transitions)
  └─→ ToastManager (for step notifications)

ToastManager
  └─→ AnimationController (for entry/exit animations)

ThemeManager
  ↓
  ├─→ MapController (for tile updates)
  └─→ localStorage (browser API)

AnimationController
  └─→ requestAnimationFrame (browser API)
```

### Inter-Component Communication

**Event-Based Communication:**
```javascript
// Custom events for component coordination
const events = {
  ROUTE_LOADED: 'route:loaded',
  ROUTE_ERROR: 'route:error',
  THEME_CHANGED: 'theme:changed',
  STEP_CLICKED: 'step:clicked'
};

// Example: Map controller listens for route loaded event
document.addEventListener(events.ROUTE_LOADED, (e) => {
  mapController.displayRoute(e.detail.points);
});
```

### External Integrations

**Backend Integration Points:**
- `GET /` - Initial page load
- `POST /route` - Route calculation request

**Backend Response Contract:**
```python
{
  "ok": boolean,
  "from_name": string,
  "to_name": string,
  "profile_label": string,
  "duration": string,  # Formatted as "HH:MM:SS"
  "distance": string,  # Formatted with unit
  "fuel": string,      # Formatted with unit or "N/A"
  "steps": [
    {
      "number": int,
      "text": string,
      "distance": string
    }
  ],
  "route_points": [[lat: float, lon: float]]
}
```

**Leaflet.js Integration:**
- Version: 1.9.4
- Tile Provider: OpenStreetMap
- Custom markers using L.divIcon
- Custom polyline styling
- Event handling for map interactions

**Browser APIs Used:**
- localStorage (theme persistence)
- matchMedia (responsive design, dark mode detection)
- requestAnimationFrame (smooth animations)
- IntersectionObserver (lazy loading, future enhancement)
- Fullscreen API (map fullscreen mode)

## Data Models

### Frontend State Model

**Application State:**
```javascript
const state = {
  theme: 'light' | 'dark',
  formData: {
    origin: string,
    destination: string,
    units: 'metric' | 'imperial',
    profile: 'car' | 'bike' | 'walk'
  },
  routeData: {
    fromName: string,
    toName: string,
    duration: string,
    distance: string,
    fuel: string,
    points: Array<[number, number]>,
    steps: Array<DirectionStep>
  },
  uiState: {
    isLoading: boolean,
    sidebarCollapsed: boolean,
    resultsVisible: boolean,
    activeToasts: Array<HTMLElement>
  }
};
```

**Direction Step Model:**
```javascript
interface DirectionStep {
  number: number;
  text: string;
  distance: string;
  icon: string; // Maneuver type
}
```

**Route Point Model:**
```javascript
interface RoutePoint {
  lat: number;  // Latitude (-90 to 90)
  lon: number;  // Longitude (-180 to 180)
}
```

**Toast Notification Model:**
```javascript
interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number;
  element: HTMLElement;
  timeoutId: number;
}
```

**Theme Configuration Model:**
```javascript
interface ThemeConfig {
  name: 'light' | 'dark';
  colors: {
    primary: string;
    background: string;
    text: string;
    border: string;
    // ... other color tokens
  };
  mapTileUrl: string;
  mapFilter: string;
}
```

### Backend Data Models (Unchanged)

**Route Request Model:**
```python
{
  "origin": str,        # Starting location
  "destination": str,   # Ending location
  "units": str,        # "metric" or "imperial"
  "profile": str       # "car", "bike", or "walk"
}
```

**GraphHopper API Response Model (Internal):**
```python
{
  "paths": [
    {
      "distance": float,  # meters
      "time": float,      # milliseconds
      "points": {
        "coordinates": [[lon: float, lat: float]]
      },
      "instructions": [
        {
          "text": str,
          "distance": float  # meters
        }
      ]
    }
  ]
}
```

### CSS Custom Properties Data Model

**Design Token Structure:**
```javascript
interface DesignTokens {
  colors: {
    primary: ColorSet,
    neutral: ColorSet,
    semantic: SemanticColors
  },
  typography: {
    fontSizes: FontSizeScale,
    fontWeights: FontWeightSet,
    lineHeights: LineHeightSet
  },
  spacing: SpacingScale,
  shadows: ShadowSet,
  radii: BorderRadiusSet,
  transitions: TransitionSet
}

interface ColorSet {
  main: string;
  dark: string;
  light: string;
  pale: string;
}

interface SemanticColors {
  success: string;
  error: string;
  warning: string;
  info: string;
}
```

### State Management Strategy

**State Persistence:**
- Theme preference → localStorage
- Form data → Session state (lost on page reload)
- Route data → Server-rendered in template
- UI state → Transient (component-local)

**State Updates:**
```javascript
// Centralized state update pattern
const stateManager = {
  updateTheme(newTheme) {
    state.theme = newTheme;
    localStorage.setItem('theme', newTheme);
    document.dispatchEvent(new CustomEvent(events.THEME_CHANGED, {
      detail: { theme: newTheme }
    }));
  },
  
  updateRouteData(data) {
    state.routeData = data;
    state.uiState.resultsVisible = true;
    document.dispatchEvent(new CustomEvent(events.ROUTE_LOADED, {
      detail: { data }
    }));
  }
};
```

## Design System

### Color Tokens

**CSS Custom Properties Definition:**
```css
:root {
  /* Primary Palette - Google Maps inspired */
  --color-primary: #1a73e8;           /* Primary blue */
  --color-primary-dark: #1557b0;      /* Hover/active states */
  --color-primary-light: #4285f4;     /* Accents */
  --color-primary-pale: #e8f0fe;      /* Backgrounds */
  
  /* Neutral Palette */
  --color-bg-page: #f8f9fa;           /* Page background */
  --color-bg-card: #ffffff;           /* Card backgrounds */
  --color-bg-elevated: #ffffff;       /* Elevated elements */
  --color-bg-hover: #f1f3f4;          /* Hover states */
  --color-bg-active: #e8eaed;         /* Active states */
  
  /* Text Colors */
  --color-text-primary: #202124;      /* Primary text */
  --color-text-secondary: #5f6368;    /* Secondary text */
  --color-text-tertiary: #70757a;     /* Muted text */
  --color-text-inverse: #ffffff;      /* Text on dark backgrounds */
  
  /* Border Colors */
  --color-border: #dadce0;            /* Default borders */
  --color-border-light: #e8eaed;      /* Subtle borders */
  --color-border-dark: #bdc1c6;       /* Emphasized borders */
  
  /* Semantic Colors */
  --color-success: #1e8e3e;           /* Success states */
  --color-success-bg: #e6f4ea;        /* Success backgrounds */
  --color-error: #d93025;             /* Error states */
  --color-error-bg: #fce8e6;          /* Error backgrounds */
  --color-warning: #f9ab00;           /* Warning states */
  --color-warning-bg: #fef7e0;        /* Warning backgrounds */
  --color-info: #1967d2;              /* Info states */
  --color-info-bg: #e8f0fe;           /* Info backgrounds */
  
  /* Map-specific Colors */
  --color-route: #1a73e8;             /* Route polyline */
  --color-route-gradient-end: #4285f4; /* Route gradient end */
  --color-marker-origin: #34a853;     /* Origin marker green */
  --color-marker-destination: #ea4335; /* Destination marker red */
}
```

**Dark Mode Overrides:**
```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-page: #202124;
    --color-bg-card: #292a2d;
    --color-bg-elevated: #35363a;
    --color-bg-hover: #3c4043;
    --color-bg-active: #5f6368;
    
    --color-text-primary: #e8eaed;
    --color-text-secondary: #9aa0a6;
    --color-text-tertiary: #80868b;
    
    --color-border: #3c4043;
    --color-border-light: #5f6368;
    --color-border-dark: #80868b;
    
    /* Adjust semantic colors for dark mode */
    --color-success-bg: #1e3a2a;
    --color-error-bg: #3a2020;
    --color-warning-bg: #3a3220;
    --color-info-bg: #1e2a3a;
  }
}

[data-theme="dark"] {
  /* Same overrides for manual dark mode toggle */
}
```

### Typography System

**Type Scale (Modular Scale 1.25):**
```css
:root {
  /* Base size */
  --font-size-base: 16px;
  --line-height-base: 1.6;
  
  /* Type scale */
  --font-size-xs: 0.75rem;      /* 12px */
  --font-size-sm: 0.875rem;     /* 14px */
  --font-size-base: 1rem;       /* 16px */
  --font-size-lg: 1.125rem;     /* 18px */
  --font-size-xl: 1.25rem;      /* 20px */
  --font-size-2xl: 1.563rem;    /* 25px */
  --font-size-3xl: 1.953rem;    /* 31px */
  --font-size-4xl: 2.441rem;    /* 39px */
  
  /* Line heights */
  --line-height-tight: 1.2;
  --line-height-snug: 1.4;
  --line-height-normal: 1.6;
  --line-height-relaxed: 1.8;
  
  /* Font weights */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* Letter spacing */
  --letter-spacing-tight: -0.02em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.01em;
  
  /* Font families */
  --font-family-base: system-ui, -apple-system, "Segoe UI", Roboto, 
                      "Helvetica Neue", Arial, sans-serif;
  --font-family-mono: "Consolas", "Monaco", "Courier New", monospace;
}
```

**Typography Classes:**
```css
/* Heading styles */
.heading-1 {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}

.heading-2 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-snug);
  letter-spacing: var(--letter-spacing-tight);
}

.heading-3 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-snug);
}

/* Body text */
.body-text {
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
}

.body-text-small {
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

/* Utility classes */
.text-muted { color: var(--color-text-secondary); }
.text-bold { font-weight: var(--font-weight-semibold); }
.text-tabular { font-variant-numeric: tabular-nums; }
```

### Spacing System

**8px Grid System:**
```css
:root {
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
}
```

### Shadow System

```css
:root {
  /* Elevation shadows - Google Material inspired */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.12), 
               0 1px 2px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 2px 6px rgba(0, 0, 0, 0.1), 
               0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-xl: 0 4px 12px rgba(0, 0, 0, 0.12), 
               0 2px 4px rgba(0, 0, 0, 0.08);
  --shadow-2xl: 0 8px 24px rgba(0, 0, 0, 0.15), 
                0 4px 8px rgba(0, 0, 0, 0.1);
  
  /* Focus shadow */
  --shadow-focus: 0 0 0 3px var(--color-primary-pale);
  
  /* Dark mode shadows (lighter, more subtle) */
}

@media (prefers-color-scheme: dark) {
  :root {
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.4), 
                 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 2px 6px rgba(0, 0, 0, 0.4), 
                 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-xl: 0 4px 12px rgba(0, 0, 0, 0.5), 
                 0 2px 4px rgba(0, 0, 0, 0.4);
    --shadow-2xl: 0 8px 24px rgba(0, 0, 0, 0.6), 
                  0 4px 8px rgba(0, 0, 0, 0.5);
  }
}
```

### Border Radius System

```css
:root {
  --radius-sm: 4px;     /* Input fields, small elements */
  --radius-md: 8px;     /* Cards, containers */
  --radius-lg: 12px;    /* Large cards, modals */
  --radius-xl: 16px;    /* Hero sections */
  --radius-full: 9999px; /* Pills, circular elements */
  --radius-button: 24px; /* Rounded buttons */
}
```

## Component Design

### Form Sidebar Component

**HTML Structure:**
```html
<aside class="form-sidebar" id="formSidebar" role="complementary">
  <div class="form-sidebar__header">
    <h1 class="form-sidebar__title">Directions Finder</h1>
    <button class="form-sidebar__collapse-btn" 
            aria-label="Collapse sidebar"
            id="collapseBtn">
      <svg class="icon icon--collapse" aria-hidden="true">...</svg>
    </button>
  </div>
  
  <form class="form-sidebar__form" id="routeForm" method="post" action="/route">
    <!-- Origin Input -->
    <div class="form-field" data-field="origin">
      <label class="form-field__label" for="origin">
        <svg class="form-field__icon icon icon--location" aria-hidden="true">...</svg>
        <span class="form-field__label-text">From</span>
      </label>
      <div class="form-field__input-wrapper">
        <input 
          class="form-field__input" 
          type="text" 
          id="origin" 
          name="origin"
          value="{{ origin }}"
          placeholder="Enter starting location"
          autocomplete="off"
          required
          aria-describedby="originHelp"
        >
        <button 
          class="form-field__clear" 
          type="button"
          aria-label="Clear origin"
          hidden
        >×</button>
      </div>
      <span class="form-field__error" id="originError" role="alert"></span>
      <span class="form-field__help" id="originHelp">e.g. Manila, PH</span>
    </div>
    
    <!-- Destination Input (same structure) -->
    <div class="form-field" data-field="destination">...</div>
    
    <!-- Unit Selection -->
    <fieldset class="form-group form-group--segmented">
      <legend class="form-group__legend">
        <svg class="form-group__icon icon icon--gauge" aria-hidden="true">...</svg>
        Units
      </legend>
      <div class="segmented-control" role="radiogroup">
        <label class="segmented-control__option">
          <input 
            type="radio" 
            name="units" 
            value="metric"
            {{ 'checked' if units == 'metric' }}
          >
          <span class="segmented-control__label">Metric</span>
        </label>
        <label class="segmented-control__option">
          <input 
            type="radio" 
            name="units" 
            value="imperial"
            {{ 'checked' if units == 'imperial' }}
          >
          <span class="segmented-control__label">Imperial</span>
        </label>
        <div class="segmented-control__slider" aria-hidden="true"></div>
      </div>
    </fieldset>
    
    <!-- Travel Mode Selection (same structure) -->
    <fieldset class="form-group form-group--segmented">...</fieldset>
    
    <!-- Submit Button -->
    <button class="btn btn--primary btn--large btn--full-width" 
            type="submit" 
            id="submitBtn">
      <span class="btn__content">
        <span class="btn__text">Find route</span>
        <span class="btn__spinner" hidden>
          <svg class="spinner" aria-hidden="true">...</svg>
        </span>
      </span>
      <span class="btn__ripple" aria-hidden="true"></span>
    </button>
  </form>
</aside>
```

**CSS Styles:**
```css
/* Form Sidebar Layout */
.form-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  max-width: 380px;
  height: 100vh;
  background: var(--color-bg-card);
  box-shadow: var(--shadow-xl);
  z-index: 100;
  overflow-y: auto;
  padding: var(--space-6);
  
  /* Smooth appearance animation */
  animation: slideInLeft 400ms cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Performance optimizations */
  contain: layout style paint;
  will-change: transform;
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Form Field Component */
.form-field {
  position: relative;
  margin-bottom: var(--space-5);
}

.form-field__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
  transition: color 200ms ease;
}

.form-field__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-field__input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  padding-right: var(--space-10);
  font-size: var(--font-size-base);
  font-family: var(--font-family-base);
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  transition: border-color 200ms ease, box-shadow 200ms ease;
}

.form-field__input:focus {
  outline: none;
  border-color: var(--color-primary);
  border-bottom-width: 2px;
  padding-bottom: calc(var(--space-3) - 1px);
  box-shadow: 0 2px 0 var(--color-primary);
}

.form-field__input:focus + .form-field__clear {
  opacity: 1;
  pointer-events: all;
}

.form-field__clear {
  position: absolute;
  right: var(--space-2);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  color: var(--color-text-tertiary);
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease, background-color 150ms ease;
}

.form-field__clear:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.form-field__error {
  display: none;
  margin-top: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-error);
  animation: shake 300ms ease;
}

.form-field--error .form-field__error {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.form-field--error .form-field__input {
  border-color: var(--color-error);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

/* Segmented Control Component */
.form-group--segmented {
  border: none;
  padding: 0;
  margin-bottom: var(--space-5);
}

.form-group__legend {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.segmented-control {
  position: relative;
  display: inline-flex;
  background: var(--color-bg-hover);
  border-radius: var(--radius-button);
  padding: var(--space-1);
}

.segmented-control__option {
  position: relative;
  z-index: 1;
  cursor: pointer;
}

.segmented-control__option input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.segmented-control__label {
  display: block;
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  transition: color 200ms ease;
  user-select: none;
}

.segmented-control__option input:checked ~ .segmented-control__label {
  color: var(--color-primary);
}

.segmented-control__slider {
  position: absolute;
  top: var(--space-1);
  left: var(--space-1);
  height: calc(100% - var(--space-2));
  background: var(--color-bg-card);
  border-radius: calc(var(--radius-button) - var(--space-1));
  box-shadow: var(--shadow-sm);
  transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1),
              width 250ms cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
}

/* Button Component */
.btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3) var(--space-6);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  text-align: center;
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: transform 200ms ease, box-shadow 200ms ease;
  overflow: hidden;
  user-select: none;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.btn:active {
  transform: translateY(0);
  box-shadow: var(--shadow-md);
}

.btn--primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn--primary:hover {
  background: var(--color-primary-dark);
}

.btn--large {
  padding: var(--space-4) var(--space-8);
  font-size: var(--font-size-lg);
}

.btn--full-width {
  width: 100%;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn__spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  margin-left: var(--space-2);
}

.btn__ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
  pointer-events: none;
}

.btn__ripple--active {
  animation: ripple 600ms ease-out;
}

@keyframes ripple {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
```

**JavaScript Controller:**
```javascript
const formController = {
  form: null,
  submitBtn: null,
  
  init() {
    this.form = document.getElementById('routeForm');
    this.submitBtn = document.getElementById('submitBtn');
    
    if (!this.form || !this.submitBtn) return;
    
    this.attachEventListeners();
    this.initializeSegmentedControls();
    this.initializeClearButtons();
  },
  
  attachEventListeners() {
    // Form submission
    this.form.addEventListener('submit', (e) => {
      const isValid = this.validateForm();
      if (!isValid) {
        e.preventDefault();
        return;
      }
      this.showLoadingState();
    });
    
    // Real-time validation
    const inputs = this.form.querySelectorAll('.form-field__input');
    inputs.forEach(input => {
      input.addEventListener('blur', () => this.validateField(input));
      input.addEventListener('input', () => this.clearFieldError(input));
    });
  },
  
  initializeSegmentedControls() {
    const controls = document.querySelectorAll('.segmented-control');
    controls.forEach(control => {
      const options = control.querySelectorAll('.segmented-control__option');
      const slider = control.querySelector('.segmented-control__slider');
      
      // Set initial slider position
      this.updateSliderPosition(control);
      
      // Handle option changes
      options.forEach(option => {
        const input = option.querySelector('input');
        input.addEventListener('change', () => {
          this.updateSliderPosition(control);
        });
      });
    });
  },
  
  updateSliderPosition(control) {
    const checkedOption = control.querySelector('input:checked').closest('.segmented-control__option');
    const slider = control.querySelector('.segmented-control__slider');
    const index = Array.from(control.querySelectorAll('.segmented-control__option')).indexOf(checkedOption);
    
    const optionWidth = checkedOption.offsetWidth;
    const translateX = index * optionWidth;
    
    slider.style.width = `${optionWidth}px`;
    slider.style.transform = `translateX(${translateX}px)`;
  },
  
  initializeClearButtons() {
    const clearButtons = document.querySelectorAll('.form-field__clear');
    clearButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const field = btn.closest('.form-field');
        const input = field.querySelector('.form-field__input');
        input.value = '';
        input.focus();
        btn.hidden = true;
      });
    });
    
    // Show/hide clear buttons based on input content
    const inputs = document.querySelectorAll('.form-field__input');
    inputs.forEach(input => {
      input.addEventListener('input', () => {
        const clearBtn = input.parentElement.querySelector('.form-field__clear');
        if (clearBtn) {
          clearBtn.hidden = input.value.length === 0;
        }
      });
    });
  },
  
  validateForm() {
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    
    let isValid = true;
    
    if (!this.validateField(originInput)) {
      isValid = false;
    }
    
    if (!this.validateField(destinationInput)) {
      isValid = false;
    }
    
    return isValid;
  },
  
  validateField(input) {
    const field = input.closest('.form-field');
    const errorElement = field.querySelector('.form-field__error');
    const value = input.value.trim();
    
    if (value === '') {
      this.showFieldError(field, errorElement, 'This field is required');
      return false;
    }
    
    this.clearFieldError(input);
    return true;
  },
  
  showFieldError(field, errorElement, message) {
    field.classList.add('form-field--error');
    errorElement.textContent = message;
  },
  
  clearFieldError(input) {
    const field = input.closest('.form-field');
    const errorElement = field.querySelector('.form-field__error');
    field.classList.remove('form-field--error');
    errorElement.textContent = '';
  },
  
  showLoadingState() {
    const btnText = this.submitBtn.querySelector('.btn__text');
    const btnSpinner = this.submitBtn.querySelector('.btn__spinner');
    
    this.submitBtn.disabled = true;
    btnText.textContent = 'Searching...';
    btnSpinner.hidden = false;
    
    // Disable form inputs
    const inputs = this.form.querySelectorAll('input, button[type="button"]');
    inputs.forEach(input => input.disabled = true);
  },
  
  addRippleEffect(event) {
    const button = event.currentTarget;
    const ripple = button.querySelector('.btn__ripple');
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.classList.add('btn__ripple--active');
    
    setTimeout(() => ripple.classList.remove('btn__ripple--active'), 600);
  }
};
```

### Map Component

**HTML Structure:**
```html
<div class="map-container" role="region" aria-label="Interactive route map">
  <div id="map" class="map-container__map"></div>
  
  <!-- Custom Zoom Controls -->
  <div class="map-controls map-controls--zoom">
    <button class="map-control-btn" 
            aria-label="Zoom in"
            id="zoomInBtn">
      <svg class="icon icon--plus" aria-hidden="true">...</svg>
    </button>
    <button class="map-control-btn" 
            aria-label="Zoom out"
            id="zoomOutBtn">
      <svg class="icon icon--minus" aria-hidden="true">...</svg>
    </button>
  </div>
  
  <!-- Map Action Controls -->
  <div class="map-controls map-controls--actions">
    <button class="map-control-btn" 
            aria-label="Recenter map"
            id="recenterBtn">
      <svg class="icon icon--target" aria-hidden="true">...</svg>
    </button>
    <button class="map-control-btn" 
            aria-label="Toggle fullscreen"
            id="fullscreenBtn">
      <svg class="icon icon--fullscreen" aria-hidden="true">...</svg>
    </button>
  </div>
  
  <!-- Loading Overlay -->
  <div class="map-loading" id="mapLoading" hidden>
    <div class="map-loading__content">
      <div class="spinner spinner--large"></div>
      <p class="map-loading__text" id="loadingText">Calculating route...</p>
    </div>
  </div>
</div>
```

**CSS Styles:**
```css
/* Map Container */
.map-container {
  position: fixed;
  top: 0;
  left: 380px;
  right: 0;
  height: 100vh;
  background: var(--color-bg-hover);
  overflow: hidden;
  
  /* Fade-in animation */
  animation: fadeIn 500ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.map-container__map {
  width: 100%;
  height: 100%;
  filter: grayscale(10%) brightness(95%);
  transition: filter 300ms ease;
}

@media (prefers-color-scheme: dark) {
  .map-container__map {
    filter: grayscale(20%) brightness(80%) contrast(110%);
  }
}

/* Custom Map Controls */
.map-controls {
  position: absolute;
  z-index: 400;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.map-controls--zoom {
  top: var(--space-4);
  right: var(--space-4);
}

.map-controls--actions {
  bottom: var(--space-4);
  right: var(--space-4);
}

.map-control-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease, 
              background-color 150ms ease;
}

.map-control-btn:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
  background: var(--color-bg-hover);
}

.map-control-btn:active {
  transform: scale(0.95);
}

.map-control-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Map Loading Overlay */
.map-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  animation: fadeIn 200ms ease;
}

@media (prefers-color-scheme: dark) {
  .map-loading {
    background: rgba(32, 33, 36, 0.9);
  }
}

.map-loading__content {
  text-align: center;
}

.map-loading__text {
  margin-top: var(--space-4);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  animation: loadingTextPulse 2s ease-in-out infinite;
}

@keyframes loadingTextPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Spinner Component */
.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 800ms linear infinite;
}

.spinner--large {
  width: 48px;
  height: 48px;
  border-width: 3px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Custom Route Polyline Styles (applied via Leaflet) */
.route-polyline {
  /* Applied programmatically */
}
```

**JavaScript Controller:**
```javascript
const mapController = {
  map: null,
  routeLayer: null,
  originMarker: null,
  destinationMarker: null,
  
  init() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    this.initializeMap(mapElement);
    this.attachControlListeners();
    
    // Load route if data is present
    if (window.routePoints && window.routePoints.length > 0) {
      this.displayRoute(window.routePoints);
    }
  },
  
  initializeMap(element) {
    // Initialize Leaflet map
    this.map = L.map(element, {
      zoomControl: false, // Use custom controls
      attributionControl: true
    });
    
    // Add tile layer
    const tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    const attribution = '&copy; OpenStreetMap contributors';
    
    L.tileLayer(tileUrl, {
      maxZoom: 19,
      attribution: attribution
    }).addTo(this.map);
    
    // Set default view
    this.map.setView([14.5995, 120.9842], 11); // Manila, PH
  },
  
  displayRoute(points) {
    if (!this.map || !points || points.length === 0) return;
    
    // Animate route appearance
    animations.orchestrateRouteDisplay(() => {
      // Draw polyline
      this.routeLayer = L.polyline(points, {
        color: getComputedStyle(document.documentElement)
          .getPropertyValue('--color-route').trim(),
        weight: 5,
        opacity: 0.85,
        className: 'route-polyline'
      }).addTo(this.map);
      
      // Add custom markers
      this.addCustomMarkers(points);
      
      // Fit bounds with animation
      this.map.fitBounds(this.routeLayer.getBounds(), {
        padding: [50, 50],
        animate: true,
        duration: 0.8
      });
      
      // Animate polyline drawing
      this.animatePolyline();
    });
  },
  
  addCustomMarkers(points) {
    const originIcon = this.createCustomIcon('origin');
    const destIcon = this.createCustomIcon('destination');
    
    // Origin marker
    this.originMarker = L.marker(points[0], { icon: originIcon })
      .addTo(this.map)
      .bindPopup('Starting point');
    
    // Destination marker
    this.destinationMarker = L.marker(points[points.length - 1], { icon: destIcon })
      .addTo(this.map)
      .bindPopup('Destination');
  },
  
  createCustomIcon(type) {
    const color = type === 'origin' 
      ? getComputedStyle(document.documentElement)
          .getPropertyValue('--color-marker-origin').trim()
      : getComputedStyle(document.documentElement)
          .getPropertyValue('--color-marker-destination').trim();
    
    return L.divIcon({
      className: `custom-marker custom-marker--${type}`,
      html: `<div class="marker-pin" style="background-color: ${color};">
               <svg class="marker-icon" viewBox="0 0 24 24">
                 <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
               </svg>
             </div>`,
      iconSize: [32, 40],
      iconAnchor: [16, 40],
      popupAnchor: [0, -40]
    });
  },
  
  animatePolyline() {
    if (!this.routeLayer) return;
    
    const path = this.routeLayer.getElement();
    if (!path) return;
    
    const length = path.getTotalLength();
    
    path.style.strokeDasharray = length;
    path.style.strokeDashoffset = length;
    path.style.animation = 'drawPolyline 800ms ease-out forwards';
  },
  
  attachControlListeners() {
    // Zoom controls
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    
    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', () => this.map.zoomIn());
    }
    
    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', () => this.map.zoomOut());
    }
    
    // Recenter button
    const recenterBtn = document.getElementById('recenterBtn');
    if (recenterBtn && this.routeLayer) {
      recenterBtn.addEventListener('click', () => {
        this.map.fitBounds(this.routeLayer.getBounds(), {
          padding: [50, 50],
          animate: true
        });
      });
    }
    
    // Fullscreen button
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }
  },
  
  toggleFullscreen() {
    const mapContainer = document.querySelector('.map-container');
    if (!document.fullscreenElement) {
      mapContainer.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  },
  
  showLoadingState(text = 'Calculating route...') {
    const loading = document.getElementById('mapLoading');
    const loadingText = document.getElementById('loadingText');
    
    if (loading) {
      loading.hidden = false;
      if (loadingText) {
        loadingText.textContent = text;
        this.cycleLoadingText(loadingText);
      }
    }
  },
  
  hideLoadingState() {
    const loading = document.getElementById('mapLoading');
    if (loading) {
      loading.hidden = true;
    }
  },
  
  cycleLoadingText(element) {
    const messages = [
      'Calculating route...',
      'Finding best path...',
      'Almost there...'
    ];
    let index = 0;
    
    const interval = setInterval(() => {
      index = (index + 1) % messages.length;
      element.textContent = messages[index];
    }, 2000);
    
    // Store interval ID to clear later
    element.dataset.intervalId = interval;
  }
};

/* Additional CSS for polyline animation */
```

I'll continue with the Results Panel, Animation System, and remaining components in the next section.

<function_calls>
<invoke name="report_progress">
<parameter name="message">Created first half of design document covering architecture, design system, and Form/Map components. Now continuing with Results Panel, animations, and responsive design.


### Results Panel Component

**HTML Structure:**
```html
<section class="results-panel" id="resultsPanel" hidden role="region" aria-labelledby="resultsTitle">
  <!-- Trip Summary Card -->
  <article class="trip-summary" aria-labelledby="summaryTitle">
    <header class="trip-summary__header">
      <h2 class="trip-summary__title" id="summaryTitle">Trip Summary</h2>
      <button class="icon-btn" aria-label="Close results" id="closeResultsBtn">
        <svg class="icon icon--close" aria-hidden="true">...</svg>
      </button>
    </header>
    
    <!-- Route Info -->
    <div class="trip-summary__route-info">
      <div class="route-endpoint">
        <svg class="icon icon--location-origin" aria-hidden="true">...</svg>
        <div class="route-endpoint__details">
          <span class="route-endpoint__label">From</span>
          <span class="route-endpoint__name">{{ result.from_name }}</span>
        </div>
      </div>
      <div class="route-endpoint">
        <svg class="icon icon--location-destination" aria-hidden="true">...</svg>
        <div class="route-endpoint__details">
          <span class="route-endpoint__label">To</span>
          <span class="route-endpoint__name">{{ result.to_name }}</span>
        </div>
      </div>
    </div>
    
    <!-- Metrics Grid -->
    <dl class="metrics-grid">
      <div class="metric-card" data-metric="distance">
        <dt class="metric-card__label">
          <svg class="icon icon--distance" aria-hidden="true">...</svg>
          Distance
        </dt>
        <dd class="metric-card__value">{{ result.distance }}</dd>
      </div>
      
      <div class="metric-card" data-metric="duration">
        <dt class="metric-card__label">
          <svg class="icon icon--clock" aria-hidden="true">...</svg>
          Duration
        </dt>
        <dd class="metric-card__value">{{ result.duration }}</dd>
      </div>
      
      <div class="metric-card" data-metric="fuel">
        <dt class="metric-card__label">
          <svg class="icon icon--fuel" aria-hidden="true">...</svg>
          Fuel
        </dt>
        <dd class="metric-card__value">{{ result.fuel }}</dd>
      </div>
    </dl>
  </article>
  
  <!-- Turn-by-Turn Directions -->
  <article class="directions" aria-labelledby="directionsTitle">
    <header class="directions__header">
      <h3 class="directions__title" id="directionsTitle">Turn-by-Turn Directions</h3>
      <button class="btn btn--secondary btn--small" id="printDirectionsBtn">
        <svg class="icon icon--print" aria-hidden="true">...</svg>
        Print
      </button>
    </header>
    
    {% if result.steps %}
    <ol class="directions-list">
      {% for step in result.steps %}
      <li class="direction-step" data-step="{{ step.number }}">
        <div class="direction-step__number" aria-hidden="true">{{ step.number }}</div>
        <div class="direction-step__content">
          <svg class="direction-step__icon icon icon--maneuver" aria-hidden="true">...</svg>
          <div class="direction-step__details">
            <p class="direction-step__instruction">{{ step.text }}</p>
            <span class="direction-step__distance">{{ step.distance }}</span>
          </div>
        </div>
      </li>
      {% endfor %}
    </ol>
    {% else %}
    <div class="empty-state">
      <svg class="empty-state__icon icon icon--directions" aria-hidden="true">...</svg>
      <p class="empty-state__text">No turn-by-turn instructions available for this route.</p>
    </div>
    {% endif %}
  </article>
</section>
```

**CSS Styles:**
```css
/* Results Panel Layout */
.results-panel {
  position: fixed;
  bottom: 0;
  left: 380px;
  right: 0;
  max-height: 50vh;
  background: var(--color-bg-card);
  border-top-left-radius: var(--radius-lg);
  border-top-right-radius: var(--radius-lg);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  z-index: 200;
  
  /* Slide-in animation */
  animation: slideInUp 300ms cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Performance */
  contain: layout style paint;
  will-change: transform;
}

@keyframes slideInUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Trip Summary Card */
.trip-summary {
  padding: var(--space-6);
  background: linear-gradient(135deg, var(--color-bg-card) 0%, var(--color-bg-hover) 100%);
  border-bottom: 1px solid var(--color-border);
}

.trip-summary__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.trip-summary__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

/* Route Endpoints */
.trip-summary__route-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.route-endpoint {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.route-endpoint__details {
  display: flex;
  flex-direction: column;
}

.route-endpoint__label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
}

.route-endpoint__name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-4);
  margin: 0;
}

.metric-card {
  padding: var(--space-4);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.metric-card__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.metric-card__value {
  display: block;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  font-variant-numeric: tabular-nums;
}

.metric-card[data-metric="distance"] .metric-card__label {
  color: var(--color-primary);
}

.metric-card[data-metric="duration"] .metric-card__label {
  color: var(--color-success);
}

.metric-card[data-metric="fuel"] .metric-card__label {
  color: var(--color-warning);
}

/* Directions Section */
.directions {
  padding: var(--space-6);
}

.directions__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.directions__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

/* Directions List */
.directions-list {
  list-style: none;
  padding: 0;
  margin: 0;
  position: relative;
}

/* Timeline connector */
.directions-list::before {
  content: '';
  position: absolute;
  left: 18px;
  top: 40px;
  bottom: 40px;
  width: 2px;
  background: linear-gradient(180deg, 
    var(--color-primary) 0%, 
    var(--color-border) 100%);
}

/* Direction Step */
.direction-step {
  position: relative;
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  margin-bottom: var(--space-2);
  border-radius: var(--radius-md);
  transition: background-color 200ms ease, transform 150ms ease;
  cursor: pointer;
  
  /* Stagger animation */
  opacity: 0;
  animation: fadeInStagger 300ms ease forwards;
}

.direction-step:nth-child(1) { animation-delay: 0ms; }
.direction-step:nth-child(2) { animation-delay: 50ms; }
.direction-step:nth-child(3) { animation-delay: 100ms; }
.direction-step:nth-child(4) { animation-delay: 150ms; }
.direction-step:nth-child(5) { animation-delay: 200ms; }
.direction-step:nth-child(n+6) { animation-delay: 250ms; }

@keyframes fadeInStagger {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.direction-step:hover {
  background: var(--color-bg-hover);
  transform: translateX(4px);
}

.direction-step:focus-within {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.direction-step__number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  z-index: 1;
}

.direction-step__content {
  flex: 1;
  display: flex;
  gap: var(--space-3);
}

.direction-step__icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  color: var(--color-text-secondary);
}

.direction-step__details {
  flex: 1;
}

.direction-step__instruction {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  line-height: var(--line-height-snug);
}

.direction-step__distance {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

/* Empty State */
.empty-state {
  padding: var(--space-10) var(--space-6);
  text-align: center;
}

.empty-state__icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-4);
  color: var(--color-text-tertiary);
  opacity: 0.5;
}

.empty-state__text {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}
```

**JavaScript Controller:**
```javascript
const resultsController = {
  panel: null,
  
  init() {
    this.panel = document.getElementById('resultsPanel');
    if (!this.panel || this.panel.hidden) return;
    
    this.attachEventListeners();
    this.animateResults();
  },
  
  attachEventListeners() {
    // Direction step interactions
    const steps = document.querySelectorAll('.direction-step');
    steps.forEach((step, index) => {
      step.addEventListener('click', () => {
        this.handleStepClick(index);
      });
      
      // Make keyboard accessible
      step.setAttribute('tabindex', '0');
      step.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.handleStepClick(index);
        }
      });
    });
    
    // Close button
    const closeBtn = document.getElementById('closeResultsBtn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideResults());
    }
    
    // Print button
    const printBtn = document.getElementById('printDirectionsBtn');
    if (printBtn) {
      printBtn.addEventListener('click', () => window.print());
    }
  },
  
  handleStepClick(stepIndex) {
    // Center map on this step's location
    if (window.routePoints && window.routePoints[stepIndex]) {
      mapController.map.setView(
        window.routePoints[stepIndex], 
        16, 
        { animate: true, duration: 0.5 }
      );
      
      // Show toast notification
      toastManager.show({
        type: 'info',
        message: `Viewing step ${stepIndex + 1}`,
        duration: 2000
      });
    }
  },
  
  animateResults() {
    // Coordinate animation sequence
    animations.orchestrateResultsDisplay(() => {
      // Scroll to top of results
      this.panel.scrollTop = 0;
    });
  },
  
  hideResults() {
    if (!this.panel) return;
    
    this.panel.style.animation = 'slideOutDown 250ms ease-out forwards';
    setTimeout(() => {
      this.panel.hidden = true;
      this.panel.style.animation = '';
    }, 250);
  },
  
  showResults() {
    if (!this.panel) return;
    
    this.panel.hidden = false;
    this.animateResults();
  }
};

// Additional animation for slide out
```

## Animation System

### Animation Controller

**JavaScript Module:**
```javascript
const animations = {
  // Configuration
  config: {
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    defaultDuration: 300,
    defaultEasing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },
  
  // Check if animations should run
  shouldAnimate() {
    return !this.config.reducedMotion;
  },
  
  // Orchestrate route display sequence
  orchestrateRouteDisplay(callback) {
    if (!this.shouldAnimate()) {
      callback();
      return;
    }
    
    // Sequence:
    // 1. Map fade-in (already handled by CSS)
    // 2. Polyline drawing (800ms)
    // 3. Results panel slide-in (300ms) - starts at 500ms
    // 4. Direction steps stagger (starts at 800ms)
    
    // Execute callback immediately (polyline animation handled in mapController)
    callback();
    
    // Show results panel after map animation starts
    setTimeout(() => {
      resultsController.showResults();
    }, 500);
  },
  
  // Orchestrate results display
  orchestrateResultsDisplay(callback) {
    if (!this.shouldAnimate()) {
      callback();
      return;
    }
    
    // Results panel slides in (CSS animation)
    // Direction steps stagger in (CSS animation with delays)
    callback();
  },
  
  // Ripple effect for buttons
  createRipple(element, event) {
    if (!this.shouldAnimate()) return;
    
    const ripple = element.querySelector('.btn__ripple');
    if (!ripple) return;
    
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.classList.add('btn__ripple--active');
    
    setTimeout(() => ripple.classList.remove('btn__ripple--active'), 600);
  },
  
  // Smooth scroll utility
  smoothScroll(element, target, duration = 400) {
    if (!this.shouldAnimate()) {
      element.scrollTop = target;
      return;
    }
    
    const start = element.scrollTop;
    const distance = target - start;
    const startTime = performance.now();
    
    const easeInOutCubic = (t) => {
      return t < 0.5 
        ? 4 * t * t * t 
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };
    
    const scroll = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeInOutCubic(progress);
      
      element.scrollTop = start + distance * eased;
      
      if (progress < 1) {
        requestAnimationFrame(scroll);
      }
    };
    
    requestAnimationFrame(scroll);
  },
  
  // Page load sequence
  orchestratePageLoad() {
    if (!this.shouldAnimate()) return;
    
    // Form sidebar already has CSS animation
    // Initialize controllers after brief delay
    setTimeout(() => {
      formController.init();
      mapController.init();
      resultsController.init();
    }, 100);
  }
};
```

### CSS Keyframes Library

```css
/* ===== Animation Keyframes ===== */

/* Slide Animations */
@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideInDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideOutDown {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(100%);
    opacity: 0;
  }
}

/* Fade Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes fadeInStagger {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scale Animations */
@keyframes scaleIn {
  from {
    transform: scale(0.8);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* Shake Animation */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

/* Spin Animation */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Ripple Animation */
@keyframes ripple {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* Pulse Animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(0.95);
  }
}

/* Polyline Draw Animation */
@keyframes drawPolyline {
  to {
    stroke-dashoffset: 0;
  }
}

/* Shimmer Loading Animation */
@keyframes shimmer {
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
}

/* Loading Text Pulse */
@keyframes loadingTextPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Reduced Motion Overrides */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Transition Timing Functions

```css
:root {
  /* Easing functions */
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
  --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
  --ease-sharp: cubic-bezier(0.4, 0, 0.6, 1);
  
  /* Duration scales */
  --duration-instant: 50ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;
}
```

## Responsive Design Strategy

### Breakpoint System

```css
:root {
  --breakpoint-mobile: 768px;
  --breakpoint-tablet: 1024px;
  --breakpoint-desktop: 1280px;
}

/* Mobile-first approach: base styles are for mobile */

/* Tablet (768px - 1024px) */
@media (min-width: 768px) {
  /* Tablet-specific styles */
}

/* Desktop (> 1024px) */
@media (min-width: 1024px) {
  /* Desktop-specific styles */
}

/* Large Desktop (> 1280px) */
@media (min-width: 1280px) {
  /* Large desktop optimizations */
}
```

### Layout Adaptations

**Mobile Layout (≤ 768px):**
```css
@media (max-width: 767px) {
  /* Stack layout vertically */
  .form-sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    top: auto;
    width: 100%;
    max-width: 100%;
    height: auto;
    max-height: 70vh;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    animation: slideInUp 300ms cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 300;
  }
  
  /* Collapsed state */
  .form-sidebar--collapsed {
    max-height: 60px;
  }
  
  /* Expand handle */
  .form-sidebar__handle {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2);
    cursor: pointer;
  }
  
  .form-sidebar__handle::before {
    content: '';
    width: 40px;
    height: 4px;
    background: var(--color-border-dark);
    border-radius: var(--radius-full);
  }
  
  /* Map takes full viewport */
  .map-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    height: 100vh;
  }
  
  /* Results as full-screen overlay */
  .results-panel {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    max-height: 100vh;
    border-radius: 0;
  }
  
  /* Touch-friendly targets */
  .btn,
  .form-field__input,
  .segmented-control__label,
  .direction-step {
    min-height: 44px;
  }
  
  /* Larger text for readability */
  .form-field__input {
    font-size: 16px; /* Prevents zoom on iOS */
  }
  
  /* Adjust spacing */
  .form-sidebar {
    padding: var(--space-4);
  }
  
  .directions-list {
    padding: var(--space-2);
  }
  
  .direction-step {
    padding: var(--space-5) var(--space-3);
  }
}
```

**Tablet Layout (768px - 1024px):**
```css
@media (min-width: 768px) and (max-width: 1023px) {
  /* Sidebar at 40% width */
  .form-sidebar {
    max-width: 40%;
    min-width: 320px;
  }
  
  /* Map fills remaining space */
  .map-container {
    left: 40%;
  }
  
  /* Results panel adjusted */
  .results-panel {
    left: 40%;
  }
  
  /* Smaller font sizes for compact view */
  .form-sidebar__title {
    font-size: var(--font-size-xl);
  }
  
  .metric-card__value {
    font-size: var(--font-size-xl);
  }
}
```

**Desktop Layout (> 1024px):**
```css
@media (min-width: 1024px) {
  /* Fixed 380px sidebar */
  .form-sidebar {
    width: 380px;
    max-width: 380px;
  }
  
  /* Map positioning */
  .map-container {
    left: 380px;
  }
  
  /* Results panel */
  .results-panel {
    left: 380px;
    max-height: 60vh;
  }
  
  /* Resizable sidebar (optional enhancement) */
  .form-sidebar--resizable {
    resize: horizontal;
    min-width: 320px;
    max-width: 600px;
  }
  
  /* Hover effects more prominent */
  .direction-step:hover {
    transform: translateX(8px);
    box-shadow: var(--shadow-sm);
  }
  
  /* Show tooltips on hover */
  .metric-card:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    padding: var(--space-2) var(--space-3);
    background: var(--color-text-primary);
    color: var(--color-text-inverse);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-sm);
    white-space: nowrap;
    opacity: 0;
    animation: fadeIn 200ms ease forwards;
  }
}
```

### Mobile-First Utilities

```css
/* Container Queries (where supported) */
@container (min-width: 400px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@container (min-width: 600px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Orientation handling */
@media (orientation: landscape) and (max-height: 600px) {
  .form-sidebar {
    max-height: 80vh;
    overflow-y: auto;
  }
}

/* High DPI displays */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  /* Sharper borders */
  .form-field__input,
  .btn,
  .card {
    border-width: 0.5px;
  }
}
```

## Toast Notification System

**HTML Structure:**
```html
<div class="toast-container" id="toastContainer" aria-live="polite" aria-atomic="true">
  <!-- Toasts inserted dynamically -->
</div>
```

**CSS Styles:**
```css
/* Toast Container */
.toast-container {
  position: fixed;
  top: var(--space-4);
  right: var(--space-4);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  pointer-events: none;
}

/* Toast Component */
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 300px;
  max-width: 500px;
  padding: var(--space-4);
  background: var(--color-bg-card);
  border-left: 4px solid var(--color-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  pointer-events: all;
  
  /* Entry animation */
  animation: toastSlideIn 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes toastSlideIn {
  from {
    transform: translateX(calc(100% + var(--space-4)));
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast--success {
  border-left-color: var(--color-success);
}

.toast--error {
  border-left-color: var(--color-error);
}

.toast--warning {
  border-left-color: var(--color-warning);
}

.toast--info {
  border-left-color: var(--color-info);
}

.toast__icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
}

.toast--success .toast__icon { color: var(--color-success); }
.toast--error .toast__icon { color: var(--color-error); }
.toast--warning .toast__icon { color: var(--color-warning); }
.toast--info .toast__icon { color: var(--color-info); }

.toast__content {
  flex: 1;
}

.toast__message {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.toast__close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: background-color 150ms ease;
}

.toast__close:hover {
  background: var(--color-bg-hover);
}

/* Exit animation */
.toast--exiting {
  animation: toastSlideOut 200ms cubic-bezier(0.4, 0, 1, 1) forwards;
}

@keyframes toastSlideOut {
  to {
    transform: translateX(calc(100% + var(--space-4)));
    opacity: 0;
  }
}
```

**JavaScript Module:**
```javascript
const toastManager = {
  container: null,
  toasts: [],
  
  init() {
    this.container = document.getElementById('toastContainer');
    if (!this.container) {
      this.createContainer();
    }
  },
  
  createContainer() {
    this.container = document.createElement('div');
    this.container.id = 'toastContainer';
    this.container.className = 'toast-container';
    this.container.setAttribute('aria-live', 'polite');
    this.container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(this.container);
  },
  
  show({ type = 'info', message, duration = 4000 }) {
    const toast = this.createToast(type, message);
    this.container.appendChild(toast);
    this.toasts.push(toast);
    
    // Auto-dismiss
    if (duration > 0) {
      setTimeout(() => this.dismiss(toast), duration);
    }
    
    return toast;
  },
  
  createToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'status');
    
    const iconSVG = this.getIconForType(type);
    
    toast.innerHTML = `
      <svg class="toast__icon" aria-hidden="true">${iconSVG}</svg>
      <div class="toast__content">
        <p class="toast__message">${this.escapeHTML(message)}</p>
      </div>
      <button class="toast__close" aria-label="Close notification">
        <svg class="icon" viewBox="0 0 24 24">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
    `;
    
    // Close button handler
    const closeBtn = toast.querySelector('.toast__close');
    closeBtn.addEventListener('click', () => this.dismiss(toast));
    
    return toast;
  },
  
  dismiss(toast) {
    toast.classList.add('toast--exiting');
    
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
      this.toasts = this.toasts.filter(t => t !== toast);
    }, 200);
  },
  
  getIconForType(type) {
    const icons = {
      success: '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>',
      error: '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>',
      warning: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
      info: '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>'
    };
    return icons[type] || icons.info;
  },
  
  escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
```

## Theme Management System

**JavaScript Module:**
```javascript
const themeManager = {
  currentTheme: null,
  
  init() {
    // Check for saved preference
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      // Use system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
    
    // Create theme toggle button
    this.createToggleButton();
  },
  
  setTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update map tiles for dark mode
    if (mapController.map) {
      this.updateMapTiles(theme);
    }
    
    // Announce to screen readers
    this.announceThemeChange(theme);
  },
  
  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  },
  
  createToggleButton() {
    const button = document.createElement('button');
    button.id = 'themeToggle';
    button.className = 'theme-toggle';
    button.setAttribute('aria-label', 'Toggle theme');
    button.innerHTML = `
      <svg class="theme-toggle__icon theme-toggle__icon--light" viewBox="0 0 24 24">
        <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.39.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"/>
      </svg>
      <svg class="theme-toggle__icon theme-toggle__icon--dark" viewBox="0 0 24 24">
        <path d="M9 2c-1.05 0-2.05.16-3 .46 4.06 1.27 7 5.06 7 9.54 0 4.48-2.94 8.27-7 9.54.95.3 1.95.46 3 .46 5.52 0 10-4.48 10-10S14.52 2 9 2z"/>
      </svg>
    `;
    
    button.addEventListener('click', () => this.toggleTheme());
    
    // Add to form sidebar header
    const formHeader = document.querySelector('.form-sidebar__header');
    if (formHeader) {
      formHeader.appendChild(button);
    }
  },
  
  updateMapTiles(theme) {
    // Switch to dark map tiles if available
    // This would require a dark tile provider
    const filter = theme === 'dark' 
      ? 'grayscale(20%) brightness(80%) contrast(110%)'
      : 'grayscale(10%) brightness(95%)';
    
    const mapElement = document.querySelector('.map-container__map');
    if (mapElement) {
      mapElement.style.filter = filter;
    }
  },
  
  announceThemeChange(theme) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = `Theme changed to ${theme} mode`;
    document.body.appendChild(announcement);
    
    setTimeout(() => document.body.removeChild(announcement), 1000);
  }
};
```

**CSS Styles for Theme Toggle:**
```css
.theme-toggle {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 150ms ease, transform 150ms ease;
}

.theme-toggle:hover {
  background: var(--color-bg-hover);
  transform: rotate(15deg);
}

.theme-toggle__icon {
  width: 20px;
  height: 20px;
  color: var(--color-text-primary);
  transition: opacity 200ms ease;
}

.theme-toggle__icon--light {
  display: block;
}

.theme-toggle__icon--dark {
  display: none;
}

[data-theme="dark"] .theme-toggle__icon--light {
  display: none;
}

[data-theme="dark"] .theme-toggle__icon--dark {
  display: block;
}
```

## Accessibility Implementation

### ARIA Patterns

**Live Regions:**
```html
<!-- For dynamic content updates -->
<div role="status" aria-live="polite" aria-atomic="true" class="sr-only">
  <!-- Announcements for screen readers -->
</div>

<!-- For error messages -->
<div role="alert" aria-live="assertive">
  <!-- Critical error messages -->
</div>
```

**Keyboard Navigation:**
```javascript
const accessibilityController = {
  init() {
    this.setupKeyboardShortcuts();
    this.setupFocusManagement();
    this.setupSkipLinks();
  },
  
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Alt+O: Focus origin input
      if (e.altKey && e.key === 'o') {
        e.preventDefault();
        document.getElementById('origin')?.focus();
      }
      
      // Alt+D: Focus destination input
      if (e.altKey && e.key === 'd') {
        e.preventDefault();
        document.getElementById('destination')?.focus();
      }
      
      // Enter: Submit form (if in form)
      if (e.key === 'Enter' && e.target.closest('form')) {
        // Handled by form submit
      }
      
      // Escape: Close modals/overlays
      if (e.key === 'Escape') {
        this.handleEscape();
      }
    });
  },
  
  setupFocusManagement() {
    // Focus trap for modals
    document.addEventListener('focus', (e) => {
      const activeModal = document.querySelector('[role="dialog"]:not([hidden])');
      if (activeModal && !activeModal.contains(e.target)) {
        e.preventDefault();
        const firstFocusable = activeModal.querySelector('button, input, textarea, select, a[href]');
        firstFocusable?.focus();
      }
    }, true);
    
    // Visible focus indicators
    document.addEventListener('mousedown', () => {
      document.body.classList.add('using-mouse');
    });
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.remove('using-mouse');
      }
    });
  },
  
  setupSkipLinks() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);
  },
  
  handleEscape() {
    // Close results panel
    if (!document.getElementById('resultsPanel')?.hidden) {
      resultsController.hideResults();
    }
    
    // Close toasts
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => toastManager.dismiss(toast));
  }
};
```

**CSS for Accessibility:**
```css
/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  padding: var(--space-2) var(--space-4);
  text-decoration: none;
  z-index: 10000;
}

.skip-link:focus {
  top: 0;
}

/* Focus indicators - only show for keyboard navigation */
body:not(.using-mouse) *:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}

body.using-mouse *:focus {
  outline: none;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --color-border: #000000;
    --shadow-md: none;
    --shadow-lg: none;
  }
  
  .btn {
    border: 2px solid currentColor;
  }
}
```

## Performance Optimization

### CSS Containment

```css
/* Apply containment to isolated components */
.form-sidebar {
  contain: layout style paint;
}

.map-container {
  contain: layout style paint;
}

.results-panel {
  contain: layout style paint;
}

.toast {
  contain: layout style paint;
}

/* Individual cards */
.metric-card,
.direction-step {
  contain: layout paint;
}
```

### Will-Change Optimization

```css
/* Only apply to elements that will definitely animate */
.form-sidebar {
  will-change: transform;
}

.btn:hover {
  will-change: transform, box-shadow;
}

.direction-step {
  will-change: transform, background-color;
}

/* Remove will-change after animation */
@keyframes removeWillChange {
  to {
    will-change: auto;
  }
}

.animated-element {
  animation: slideIn 300ms, removeWillChange 1ms 300ms;
}
```

### Lazy Loading Strategy

```javascript
const performanceOptimizer = {
  init() {
    this.lazyLoadMap();
    this.deferNonCriticalCSS();
    this.preloadCriticalAssets();
  },
  
  lazyLoadMap() {
    // Only load Leaflet when map is needed
    if (window.routePoints && window.routePoints.length > 0) {
      this.loadLeaflet().then(() => {
        mapController.init();
      });
    }
  },
  
  loadLeaflet() {
    return new Promise((resolve, reject) => {
      if (window.L) {
        resolve();
        return;
      }
      
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
      link.crossOrigin = '';
      
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = resolve;
      script.onerror = reject;
      
      document.head.appendChild(link);
      document.head.appendChild(script);
    });
  },
  
  deferNonCriticalCSS() {
    // Load icon fonts after page load
    window.addEventListener('load', () => {
      const iconFont = document.createElement('link');
      iconFont.rel = 'stylesheet';
      iconFont.href = 'https://fonts.googleapis.com/icon?family=Material+Icons';
      document.head.appendChild(iconFont);
    });
  },
  
  preloadCriticalAssets() {
    // Preload main font
    const fontPreload = document.createElement('link');
    fontPreload.rel = 'preload';
    fontPreload.as = 'font';
    fontPreload.type = 'font/woff2';
    fontPreload.href = '/path/to/font.woff2';
    fontPreload.crossOrigin = 'anonymous';
    document.head.appendChild(fontPreload);
  }
};
```

### Debouncing and Throttling

```javascript
const utils = {
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
};

// Usage examples
const debouncedValidation = utils.debounce((input) => {
  formController.validateField(input);
}, 300);

const throttledScroll = utils.throttle((e) => {
  // Handle scroll events
}, 100);
```

## Error Handling

### Error States Design

```html
<!-- Form Error -->
<div class="form-field form-field--error">
  <label class="form-field__label" for="origin">From</label>
  <input class="form-field__input" type="text" id="origin" aria-invalid="true" aria-describedby="originError">
  <span class="form-field__error" id="originError" role="alert">
    <svg class="icon icon--error" aria-hidden="true">...</svg>
    This field is required
  </span>
</div>

<!-- API Error Modal -->
<div class="modal" role="dialog" aria-labelledby="errorTitle" aria-describedby="errorDesc">
  <div class="modal__overlay"></div>
  <div class="modal__content">
    <header class="modal__header">
      <h2 class="modal__title" id="errorTitle">Route Error</h2>
      <button class="modal__close" aria-label="Close">×</button>
    </header>
    <div class="modal__body">
      <svg class="error-icon" aria-hidden="true">...</svg>
      <p id="errorDesc">{{ error_detail }}</p>
    </div>
    <footer class="modal__footer">
      <button class="btn btn--primary">Try Again</button>
      <button class="btn btn--secondary">Cancel</button>
    </footer>
  </div>
</div>
```

## Testing Strategy

### Manual Testing Checklist

**Visual Testing:**
- [ ] Design system colors applied correctly
- [ ] Typography hierarchy clear
- [ ] Spacing consistent across components
- [ ] Shadows and elevation appropriate
- [ ] Dark mode matches design
- [ ] All animations smooth (60fps)

**Responsive Testing:**
- [ ] Mobile layout (375px, 414px)
- [ ] Tablet layout (768px, 1024px)
- [ ] Desktop layout (1280px, 1920px)
- [ ] Touch targets adequate (44x44px minimum)
- [ ] Text readable at all sizes

**Accessibility Testing:**
- [ ] Keyboard navigation works
- [ ] Screen reader announcements correct
- [ ] Focus indicators visible
- [ ] Color contrast ratios meet WCAG AA
- [ ] ARIA attributes correct
- [ ] Skip links functional

**Performance Testing:**
- [ ] Initial load under 3 seconds
- [ ] Time to Interactive under 5 seconds
- [ ] Animations run at 60fps
- [ ] No layout shifts
- [ ] Memory usage reasonable

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Form Validation Completeness

*For any* form submission attempt, the system SHALL validate all required fields and prevent submission if any field is invalid

**Validates: Requirements 4.5, 4.7**

### Property 2: Animation Performance Guarantee

*For any* animation or transition, when hardware acceleration is available, the system SHALL use CSS transforms (translate, scale, rotate) and opacity properties exclusively to maintain 60fps performance

**Validates: Requirements 2.7**

### Property 3: Responsive Layout Consistency

*For any* viewport width change, the layout SHALL transition smoothly within 300ms and all interactive elements SHALL remain accessible without horizontal scrolling

**Validates: Requirements 3.5, 3.10**

### Property 4: Accessibility Focus Order

*For any* keyboard navigation sequence, the focus order SHALL follow the visual layout order and skip-to-content links SHALL allow bypassing navigation

**Validates: Requirements 9.4, 9.6, 9.8**

### Property 5: Color Contrast Compliance

*For any* text element against its background, the color contrast ratio SHALL be at least 4.5:1 in both light and dark modes

**Validates: Requirements 9.1**

### Property 6: Loading State Feedback

*For any* asynchronous operation (route fetch, map load), the system SHALL display visual feedback within 100ms and update loading text every 2 seconds

**Validates: Requirements 6.1, 6.5**

### Property 7: Touch Target Adequacy

*For any* interactive element on mobile viewports (≤768px), the minimum touch target size SHALL be 44x44px

**Validates: Requirements 3.6**

### Property 8: Toast Notification Lifecycle

*For any* toast notification, it SHALL auto-dismiss after its specified duration (default 4 seconds) OR when manually dismissed, with smooth exit animation

**Validates: Requirements 16.3, 16.4**

### Property 9: Theme Persistence

*For any* theme change (light/dark), the preference SHALL be saved to localStorage and applied on subsequent page loads

**Validates: Requirements 12.7**

### Property 10: Reduced Motion Respect

*For any* user with prefers-reduced-motion enabled, all animations SHALL be disabled or reduced to minimal duration (≤0.01ms)

**Validates: Requirements 9.5**

## Error Handling

### Client-Side Error Handling

**Validation Errors:**
- Display inline error messages with shake animation
- Show error icon and descriptive text
- Apply error styling to form field
- Prevent form submission
- Announce errors to screen readers

**API Errors:**
- Display user-friendly error messages
- Avoid exposing technical details
- Provide actionable suggestions
- Show retry option
- Log errors for debugging

**Network Errors:**
- Display persistent banner
- Show offline indicator
- Provide retry button
- Cache form data to prevent loss

### Error Recovery

```javascript
const errorHandler = {
  handleFormError(field, message) {
    const errorElement = field.querySelector('.form-field__error');
    errorElement.textContent = message;
    field.classList.add('form-field--error');
    errorElement.setAttribute('role', 'alert');
  },
  
  handleAPIError(error) {
    let message = 'Unable to calculate route. Please try again.';
    let detail = '';
    
    if (error.status === 429) {
      message = 'Too many requests';
      detail = 'Please wait a moment before trying again.';
    } else if (error.status >= 500) {
      message = 'Server error';
      detail = 'The routing service is temporarily unavailable.';
    }
    
    toastManager.show({
      type: 'error',
      message: `${message} ${detail}`,
      duration: 6000
    });
  },
  
  handleNetworkError() {
    const banner = document.createElement('div');
    banner.className = 'network-error-banner';
    banner.innerHTML = `
      <svg class="icon icon--offline">...</svg>
      <span>No internet connection</span>
      <button class="btn btn--small" onclick="location.reload()">Retry</button>
    `;
    document.body.prepend(banner);
  }
};
```

## Testing Strategy

### Unit Testing

**Test Coverage Areas:**
- Form validation logic
- Utility functions (debounce, throttle, formatters)
- Theme management
- Toast notification system

**Example Test Structure:**
```javascript
// test-form-validation.js
describe('Form Validation', () => {
  test('validates required fields', () => {
    const result = formController.validateField(emptyInput);
    expect(result).toBe(false);
  });
  
  test('accepts valid input', () => {
    const result = formController.validateField(validInput);
    expect(result).toBe(true);
  });
});
```

### Integration Testing

**Test Scenarios:**
- Complete form submission flow
- Route display with map interaction
- Theme switching across components
- Responsive layout transitions

### Property-Based Testing

**Note:** While property-based testing is valuable for algorithmic logic, this UI enhancement project focuses on visual presentation and user interaction. The correctness properties defined above serve as design requirements rather than PBT test cases. Testing will rely on:
- Manual visual inspection
- Accessibility audits
- Performance profiling
- Cross-browser testing
- User acceptance testing

## Implementation Plan

### Phase 1: Foundation (Design System)
1. Implement CSS custom properties
2. Create base styles and reset
3. Build typography system
4. Establish spacing and layout grid

### Phase 2: Component Development
1. Form sidebar component
2. Map component integration
3. Results panel component
4. Toast notification system

### Phase 3: Animations and Interactions
1. Implement animation system
2. Add micro-interactions
3. Create loading states
4. Build transition orchestration

### Phase 4: Responsive Design
1. Mobile layout implementation
2. Tablet layout adjustments
3. Desktop enhancements
4. Touch interaction support

### Phase 5: Accessibility and Polish
1. ARIA implementation
2. Keyboard navigation
3. Screen reader testing
4. Focus management

### Phase 6: Performance Optimization
1. CSS containment
2. Lazy loading
3. Animation optimization
4. Bundle size reduction

### Phase 7: Testing and Refinement
1. Cross-browser testing
2. Accessibility audit
3. Performance profiling
4. User feedback integration

## Maintenance Guidelines

### Code Organization
- Keep CSS organized by section
- Use consistent naming conventions
- Comment complex calculations
- Document animation choreography

### Performance Monitoring
- Track animation frame rates
- Monitor bundle size
- Measure interaction latency
- Profile memory usage

### Accessibility Audits
- Regular WCAG compliance checks
- Screen reader testing
- Keyboard navigation verification
- Color contrast validation

### Browser Compatibility
- Test on Chrome, Firefox, Safari, Edge
- Verify mobile browser behavior
- Check progressive enhancement
- Document known issues

## Conclusion

This design document provides a comprehensive technical specification for transforming the MapQuest web frontend into a modern, Google Maps-inspired interface. The design maintains the existing Flask/Jinja2/vanilla JavaScript stack while introducing professional design patterns, smooth animations, and comprehensive responsive support.

Key achievements of this design:
- Modern design system with consistent tokens
- Smooth 60fps animations using CSS transforms
- Full responsive support across all screen sizes
- WCAG 2.1 AA accessibility compliance
- Dark mode with theme persistence
- Performance-optimized implementation
- Maintainable code architecture

The design is ready for implementation following the phased approach outlined above.
