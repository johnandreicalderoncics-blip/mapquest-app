// Directions Finder - progressive enhancement only.
// The form works without JavaScript; this just shows feedback while
// the server round-trip is in flight.
//
// Server-rendered app: every page load re-renders index.html with the
// route result inlined as window.routePoints. All controllers below
// initialize post-render against the server-provided DOM; there is no
// fetch anywhere.
//
(function () {
  "use strict";
  // CONFIG
  var CONFIG = {
    rippleDuration: 600,          // matches .btn__ripple--active CSS (600ms)
    orchestrationDelay: 500,      // ms before results panel becomes visible
    polylineColorFallback: "#1a73e8",
    tileUrl: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    tileAttribution: "&copy; OpenStreetMap contributors",
    tileMaxZoom: 19,
    defaultView: { center: [14.5995, 120.9842], zoom: 12 }, // Manila
    routeBoundsPadding: [40, 40]
  };

  function getMediaQuery(query) {
    if (typeof window.matchMedia !== "function") {
      return null;
    }
    try {
      return window.matchMedia(query);
    } catch (error) {
      return null;
    }
  }

  function onMediaQueryChange(mediaQuery, handler) {
    if (!mediaQuery) {
      return;
    }
    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", handler);
    } else if (typeof mediaQuery.addListener === "function") {
      mediaQuery.addListener(handler);
    }
  }

  function requestFrame(callback) {
    if (typeof window.requestAnimationFrame === "function") {
      return window.requestAnimationFrame(callback);
    }
    return window.setTimeout(function () {
      callback(Date.now());
    }, 16);
  }
  // state
  var state = {
    map: null,
    route: null,
    mapInitialized: false
  };
  // utils
  var utils = {
    /** Return a function that runs fn after `wait` ms of quiet. */
    debounce: function (fn, wait) {
      var timer = null;
      return function () {
        var args = arguments;
        var self = this;
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(function () {
          timer = null;
          fn.apply(self, args);
        }, wait);
      };
    },

    /** Return a function that runs fn at most once per `interval` ms. */
    throttle: function (fn, interval) {
      var last = 0;
      var timer = null;
      return function () {
        var args = arguments;
        var self = this;
        var now = Date.now();
        var remaining = interval - (now - last);
        if (remaining <= 0) {
          if (timer) {
            clearTimeout(timer);
            timer = null;
          }
          last = now;
          fn.apply(self, args);
        } else if (!timer) {
          timer = setTimeout(function () {
            last = Date.now();
            timer = null;
            fn.apply(self, args);
          }, remaining);
        }
      };
    },

    /** Escape a string for safe insertion into HTML. */
    escapeHTML: function (text) {
      var div = document.createElement("div");
      div.textContent = String(text == null ? "" : text);
      return div.innerHTML;
    }
  };
  var animations = {
    /** Cached reduced-motion media query; null where matchMedia is absent. */
    _reducedMotionQuery: getMediaQuery("(prefers-reduced-motion: reduce)"),

    /** True when UI animation is allowed (i.e. user has not requested
     *  reduced motion). Re-evaluated on each call so OS toggles are
     *  picked up even without the change listener. */
    shouldAnimate: function () {
      var query = animations._reducedMotionQuery;
      return !(query && query.matches);
    },

    /** Element-level guard: gate a one-off element animation. */
    animateElement: function (element, className) {
      if (!element || !animations.shouldAnimate()) {
        return;
      }
      element.classList.add(className);
    },

    /** Create a material-style ripple inside a .btn. The CSS keyframe
     *  scales a positioned .btn__ripple from 0 to 4 while fading out;
     *  we size and place it inline, then trigger the --active class. */
    createRipple: function (event) {
      var button = event.currentTarget;
      if (!button || !animations.shouldAnimate()) {
        return;
      }
      var ripple = button.querySelector(".btn__ripple");
      if (!ripple) {
        return;
      }

      var rect = button.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var x = event.clientX - rect.left - size / 2;
      var y = event.clientY - rect.top - size / 2;

      // Restart cleanly if a previous ripple is still animating.
      ripple.classList.remove("btn__ripple--active");
      // Force a reflow so removing/re-adding the class restarts the
      // CSS animation instead of letting it continue.
      void ripple.offsetWidth;

      ripple.style.width = size + "px";
      ripple.style.height = size + "px";
      ripple.style.left = x + "px";
      ripple.style.top = y + "px";
      ripple.classList.add("btn__ripple--active");

      setTimeout(function () {
        ripple.classList.remove("btn__ripple--active");
      }, CONFIG.rippleDuration);
    },

    /** Ease-in-out cubic easing for smoothScroll. */
    easeInOutCubic: function (t) {
      return t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    },

    /** rAF-based smooth scroll to an absolute Y position. Used instead
     *  of scrollIntoView({behavior:"smooth"}) so duration is controlled
     *  and reduced motion is honored. */
    smoothScroll: function (targetY, duration) {
      if (!animations.shouldAnimate()) {
        window.scrollTo(0, targetY);
        return;
      }
      var start = window.pageYOffset;
      var change = targetY - start;
      var startTime = null;
      var dur = duration || 500;

      function step(timestamp) {
        if (startTime === null) {
          startTime = timestamp;
        }
        var elapsed = timestamp - startTime;
        var progress = Math.min(elapsed / dur, 1);
        window.scrollTo(0, start + change * animations.easeInOutCubic(progress));
        if (progress < 1) {
          requestFrame(step);
        }
      }
      requestFrame(step);
    },

    /** Post-render route display orchestration: the map and polyline are
     *  already in place (mapController), so after a short delay reveal
     *  the results panel and bring it into view. Runs once per load. */
    orchestrateRouteDisplay: function () {
      var resultsPanel = document.getElementById("resultsPanel");
      if (!resultsPanel) {
        return;
      }

      setTimeout(function () {
        if (resultsController) {
          resultsController.show();
        } else {
          resultsPanel.classList.add("results-panel--visible");
        }
        if (animations.shouldAnimate() && resultsPanel.scrollIntoView) {
          // Panel sits at the bottom on mobile / right on desktop;
          // scroll it into view on small screens only.
          var mobileQuery = getMediaQuery("(max-width: 767px)");
          if (mobileQuery && mobileQuery.matches) {
            resultsPanel.scrollIntoView({ behavior: "smooth", block: "end" });
          }
        }
      }, CONFIG.orchestrationDelay);
    }
  };

  // Listen for OS-level reduced-motion toggles (keeps shouldAnimate and
  // any animation-gated state current without a reload).
  onMediaQueryChange(animations._reducedMotionQuery, function () {
    // shouldAnimate() re-reads matches on every call.
  });
  // toastManager (Tasks 9.1-9.2)
  var toastManager = {
    CONTAINER_ID: "toast-container",
    AUTO_DISMISS_MS: 5000,
    EXIT_MS: 200,          // matches .toast--dismissing (slideOutUp 200ms)
    MAX_TOASTS: 4,
    active: [],

    ICONS: {
      success: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/></svg>',
      error: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="currentColor"/></svg>',
      warning: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" fill="currentColor"/></svg>',
      info: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="currentColor"/></svg>'
    },

    /** Create and display a toast. Returns the element or null when the
     *  container is absent. Content is escaped before insertion. */
    show: function (message, type, options) {
      var container = document.getElementById(toastManager.CONTAINER_ID);
      if (!container) {
        return null;
      }
      type = toastManager.ICONS[type] ? type : "info";
      options = options || {};

      var toast = document.createElement("div");
      toast.className = "toast toast--" + type;
      toast.setAttribute("role", "status");
      toast.innerHTML =
        '<div class="toast__icon">' + toastManager.ICONS[type] + "</div>" +
        '<div class="toast__message">' + utils.escapeHTML(message) + "</div>" +
        '<button class="toast__close" type="button" aria-label="Dismiss notification">' +
        '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">' +
        '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>' +
        "</svg></button>";

      container.appendChild(toast);
      toastManager.active.push(toast);

      // Cap at MAX_TOASTS: drop the oldest when over.
      while (toastManager.active.length > toastManager.MAX_TOASTS) {
        var oldest = toastManager.active.shift();
        if (oldest && oldest.parentNode) {
          toastManager.dismiss(oldest);
        }
      }

      // Auto-dismiss unless the caller pinned the toast.
      if (!options.sticky) {
        toast._autoTimer = setTimeout(function () {
          toastManager.dismiss(toast);
        }, toastManager.AUTO_DISMISS_MS);
      }

      toast.querySelector(".toast__close").addEventListener("click", function () {
        toastManager.dismiss(toast);
      });

      return toast;
    },

    /** Exit-animate and remove every active toast. */
    dismissAll: function () {
      Array.prototype.slice.call(toastManager.active)
        .forEach(function (toast) {
          toastManager.dismiss(toast);
        });
    },

    /** Exit-animate a toast, then remove it from the DOM. */
    dismiss: function (toast) {
      if (!toast || toast._dismissing) {
        return;
      }
      toast._dismissing = true;
      if (toast._autoTimer) {
        clearTimeout(toast._autoTimer);
        toast._autoTimer = null;
      }
      var index = toastManager.active.indexOf(toast);
      if (index !== -1) {
        toastManager.active.splice(index, 1);
      }
      toast.classList.add("toast--dismissing");
      setTimeout(function () {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, toastManager.EXIT_MS);
    }
  };
  var themeManager = {
    STORAGE_KEY: "theme",

    _systemQuery: getMediaQuery("(prefers-color-scheme: dark)"),

    /** Saved preference, or null when none was stored. */
    getSavedTheme: function () {
      try {
        return localStorage.getItem(themeManager.STORAGE_KEY);
      } catch (e) {
        return null; // storage unavailable (private mode, blocked, etc.)
      }
    },

    /** Saved pref wins; otherwise follow the OS color scheme. */
    getPreferredTheme: function () {
      var saved = themeManager.getSavedTheme();
      if (saved === "dark" || saved === "light") {
        return saved;
      }
      return (themeManager._systemQuery && themeManager._systemQuery.matches)
        ? "dark"
        : "light";
    },

    /** Apply a theme and persist it. */
    setTheme: function (theme) {
      if (theme !== "dark" && theme !== "light") {
        return;
      }
      document.documentElement.setAttribute("data-theme", theme);
      try {
        localStorage.setItem(themeManager.STORAGE_KEY, theme);
      } catch (e) { /* persistence is best-effort */ }
    },

    /** Sync the attribute at load (the anti-FOUC head script already
     *  set it; this reconciles and starts the OS-change listener). */
    initialize: function () {
      document.documentElement.setAttribute(
        "data-theme", themeManager.getPreferredTheme());

      // Follow OS changes only while the user has no saved preference.
      onMediaQueryChange(themeManager._systemQuery, function (event) {
        if (!themeManager.getSavedTheme()) {
          document.documentElement.setAttribute(
            "data-theme", event.matches ? "dark" : "light");
        }
      });
    },

    /** Switch light/dark behind a 300ms cross-fade and
     *  announce the change to screen readers. */
    toggleTheme: function () {
      var root = document.documentElement;
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";

      root.classList.add("theme-transitioning");
      themeManager.setTheme(next);
      setTimeout(function () {
        root.classList.remove("theme-transitioning");
      }, 300);

      accessibilityController.announce(
        next === "dark" ? "Dark theme enabled" : "Light theme enabled");
    },

    /** Wire the sidebar header toggle: click switches the theme and
     *  keeps aria-pressed in sync with the applied theme. */
    attachThemeToggle: function () {
      var toggle = document.getElementById("themeToggle");
      if (!toggle) {
        return;
      }

      var syncPressed = function () {
        var dark =
          document.documentElement.getAttribute("data-theme") === "dark";
        toggle.setAttribute("aria-pressed", dark ? "true" : "false");
      };

      syncPressed();
      toggle.addEventListener("click", function () {
        toggle.classList.remove("theme-toggle--changing");
        void toggle.offsetWidth;
        toggle.classList.add("theme-toggle--changing");
        themeManager.toggleTheme();
        syncPressed();
        setTimeout(function () {
          toggle.classList.remove("theme-toggle--changing");
        }, 300);
      });
    }
  };

  // Forward declarations: controllers defined in later tasks/sections.
  var resultsController = {
    /** Reveal the results panel after paint and reset its scroll
     *  position. Idempotent per page load. */
    show: function () {
      var panel = document.getElementById("resultsPanel");
      if (!panel || panel.classList.contains("results-panel--visible")) {
        return;
      }
      // Reveal on the next frame so the CSS transition always runs.
      requestFrame(function () {
        panel.classList.add("results-panel--visible");
        panel.scrollTop = 0;
      });
    },

    /** Make direction steps keyboard-activatable. The click
     *  handler centers the map on an interpolated point along the route;
     *  Enter/Space activate via the same path. */
    attachStepInteractions: function () {
      var steps = document.querySelectorAll(".direction-step");
      Array.prototype.forEach.call(steps, function (step) {
        if (step.getAttribute("tabindex") === null) {
          step.setAttribute("tabindex", "0");
        }
        step.setAttribute("role", "button");

        step.addEventListener("click", function () {
          resultsController.activateStep(step);
        });

        step.addEventListener("keydown", function (event) {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            resultsController.activateStep(step);
          }
        });
      });
    },

    /** Fire the "Route found" success toast using the rendered endpoint
     *  names. */
    showSuccessToast: function () {
      var names = document.querySelectorAll(".endpoint__name");
      if (names.length < 2) {
        return;
      }
      var origin = names[0].textContent.trim();
      var destination = names[names.length - 1].textContent.trim();
      toastManager.show("Route found: " + origin + " to " + destination, "success");
    },

    /** Center the map near the step's position along the polyline
     *  (window.routePoints holds vertices, not per-step points, so the
     *  position is interpolated by step fraction over cumulative
     *  segment length). */
    activateStep: function (step) {
      if (!state.map || !window.routePoints || window.routePoints.length < 2) {
        return;
      }

      var points = window.routePoints;
      var totalSteps = document.querySelectorAll(".direction-step").length;
      var number = parseInt(step.getAttribute("data-step"), 10);
      if (!number || number < 1) {
        number = 1;
      }
      var fraction = (number - 0.5) / Math.max(totalSteps, 1);

      // Cumulative planar segment lengths (lat/lng degrees).
      var cumulative = [0];
      var i;
      for (i = 1; i < points.length; i++) {
        var dLat = points[i][0] - points[i - 1][0];
        var dLng = points[i][1] - points[i - 1][1];
        cumulative.push(cumulative[i - 1] + Math.sqrt(dLat * dLat + dLng * dLng));
      }
      var target = cumulative[cumulative.length - 1] * fraction;
      var position = points[points.length - 1];
      for (i = 1; i < cumulative.length; i++) {
        if (cumulative[i] >= target) {
          var segLen = cumulative[i] - cumulative[i - 1];
          var t = segLen > 0 ? (target - cumulative[i - 1]) / segLen : 0;
          position = [
            points[i - 1][0] + t * (points[i][0] - points[i - 1][0]),
            points[i - 1][1] + t * (points[i][1] - points[i - 1][1])
          ];
          break;
        }
      }

      state.map.setView(position, Math.max(state.map.getZoom(), 14), {
        animate: animations.shouldAnimate()
      });
      toastManager.show("Showing step " + number + " on the map", "info");
    }
  };
  // mapController (Tasks 7.1 - 7.3; route display animation arrives in 7.2)
  var mapController = {
    /** Initialize the Leaflet map. Behavior-preserving move of the
     *  original inline code. */
    initializeMap: function () {
      var mapElement = document.getElementById("route-map");
      var mapContainer = document.getElementById("mapContainer");

      if (!mapElement || !window.L) {
        return;
      }

      var hasRoute = window.routePoints && window.routePoints.length > 0;
      var loadingOverlay = document.getElementById("mapLoadingOverlay");
      if (loadingOverlay && hasRoute) {
        loadingOverlay.removeAttribute("hidden");
      }

      // Cycle loading messages every 2s while the map loads
      var loadingMessages = [
        "Finding route...",
        "Plotting path...",
        "Almost there..."
      ];
      var messageIndex = 0;
      var messageTimer = null;
      var loadingText = document.getElementById("mapLoadingText");
      if (loadingText) {
        messageTimer = setInterval(function () {
          messageIndex = (messageIndex + 1) % loadingMessages.length;
          loadingText.textContent = loadingMessages[messageIndex];
        }, 2000);
      }

      state.map = L.map(mapElement, {
        zoomControl: false, // Disable default zoom control
        attributionControl: true
      });

      L.tileLayer(CONFIG.tileUrl, {
        maxZoom: CONFIG.tileMaxZoom,
        attribution: CONFIG.tileAttribution
      }).addTo(state.map);

      if (hasRoute) {
        mapController.displayRoute();
        state.map.fitBounds(state.route.getBounds(), {
          padding: CONFIG.routeBoundsPadding
        });
      } else {
        state.map.setView(
          CONFIG.defaultView.center,
          CONFIG.defaultView.zoom
        );
      }

      mapController.attachControlListeners(mapContainer);

      // Hide loading overlay after map loads (min 300ms display);
      // stop the message cycle
      state.map.whenReady(function () {
        if (messageTimer) {
          clearInterval(messageTimer);
          messageTimer = null;
        }
        setTimeout(function () {
          if (loadingOverlay && hasRoute) {
            loadingOverlay.setAttribute("hidden", "");
          }
        }, 300);
      });

      // Throttled resize keeps Leaflet's canvas in sync
      window.addEventListener("resize", utils.throttle(function () {
        if (state.map) {
          state.map.invalidateSize();
        }
      }, 200));

      state.mapInitialized = true;
    },

    /** Draw the route polyline and endpoint markers. */
    displayRoute: function () {
      // Route styling pulled from the CSS primary token, with a safe
      // fallback for when getComputedStyle is unavailable.
      var color = CONFIG.polylineColorFallback;
      try {
        var token = getComputedStyle(document.documentElement)
          .getPropertyValue("--color-primary");
        if (token && token.trim()) {
          color = token.trim();
        }
      } catch (e) { /* keep fallback */ }

      state.route = L.polyline(window.routePoints, {
        color: color,
        weight: 5,
        opacity: 0.85,
        smoothFactor: 1.0
      }).addTo(state.map);

      // Custom markers for origin (green) and destination (red)
      var originIcon = L.divIcon({
        className: "custom-marker custom-marker--origin",
        html: '<div class="marker-pin marker-pin--origin"></div>',
        iconSize: [30, 40],
        iconAnchor: [15, 40]
      });

      var destIcon = L.divIcon({
        className: "custom-marker custom-marker--destination",
        html: '<div class="marker-pin marker-pin--destination"></div>',
        iconSize: [30, 40],
        iconAnchor: [15, 40]
      });

      L.marker(window.routePoints[0], { icon: originIcon })
        .addTo(state.map)
        .bindPopup("Starting point");
      L.marker(window.routePoints[window.routePoints.length - 1], { icon: destIcon })
        .addTo(state.map)
        .bindPopup("Destination");

      mapController.animatePolyline();
    },

    /** Draw the polyline in with a stroke-dasharray animation
     *. Skipped under prefers-reduced-motion or when the
     *  path API is unavailable. */
    animatePolyline: function () {
      if (!state.route || !animations.shouldAnimate()) {
        return;
      }
      var path = state.route.getElement && state.route.getElement();
      if (!path || typeof path.getTotalLength !== "function") {
        return;
      }
      try {
        var length = path.getTotalLength();
        if (!length || !isFinite(length)) {
          return;
        }
        path.style.strokeDasharray = String(length);
        path.style.strokeDashoffset = String(length);
        path.classList.add("polyline-animating");
        setTimeout(function () {
          path.classList.remove("polyline-animating");
          path.style.strokeDasharray = "";
          path.style.strokeDashoffset = "";
        }, 800);
      } catch (e) {
        // Leave the polyline static rather than break the map.
      }
    },

    /** Custom zoom / recenter / fullscreen controls. */
    attachControlListeners: function (mapContainer) {
      var zoomInBtn = document.getElementById("zoomInBtn");
      var zoomOutBtn = document.getElementById("zoomOutBtn");

      if (zoomInBtn) {
        zoomInBtn.addEventListener("click", function () {
          state.map.zoomIn();
        });
      }

      if (zoomOutBtn) {
        zoomOutBtn.addEventListener("click", function () {
          state.map.zoomOut();
        });
      }

      var recenterBtn = document.getElementById("recenterBtn");
      if (recenterBtn && state.route) {
        recenterBtn.addEventListener("click", function () {
          state.map.fitBounds(state.route.getBounds(), {
            padding: CONFIG.routeBoundsPadding,
            animate: true,
            duration: 0.5
          });
        });
      }

      var fullscreenBtn = document.getElementById("fullscreenBtn");
      if (fullscreenBtn && mapContainer) {
        var syncFullscreenPressed = function () {
          fullscreenBtn.setAttribute(
            "aria-pressed",
            document.fullscreenElement ? "true" : "false");
        };

        fullscreenBtn.addEventListener("click", function () {
          if (!document.fullscreenElement) {
            // Enter fullscreen
            if (mapContainer.requestFullscreen) {
              mapContainer.requestFullscreen();
            } else if (mapContainer.webkitRequestFullscreen) {
              mapContainer.webkitRequestFullscreen();
            } else if (mapContainer.msRequestFullscreen) {
              mapContainer.msRequestFullscreen();
            }
            mapContainer.classList.add("map-container--fullscreen");
          } else {
            // Exit fullscreen
            if (document.exitFullscreen) {
              document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
              document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
              document.msExitFullscreen();
            }
            mapContainer.classList.remove("map-container--fullscreen");
          }
          syncFullscreenPressed();

          // Invalidate map size after fullscreen change
          setTimeout(function () {
            state.map.invalidateSize();
          }, 100);
        });

        // Listen for fullscreen changes
        document.addEventListener("fullscreenchange", function () {
          syncFullscreenPressed();
          if (!document.fullscreenElement) {
            mapContainer.classList.remove("map-container--fullscreen");
            setTimeout(function () {
              state.map.invalidateSize();
            }, 100);
          }
        });
      }
    }
  };
  // formController (Tasks 6.1-6.4; loading states arrive in 6.4)
  var formController = {
    FIELDS: ["origin", "destination"],

    /** Show in-flight feedback on submit: validate first;
     *  block invalid submissions; on a valid submit disable the controls,
     *  show the spinner + "Searching..." label. Progressive enhancement
     *  only: without JS the form still submits normally. */
    attachSubmitFeedback: function () {
      var form = document.getElementById("routeForm");
      var button = document.getElementById("submitBtn");
      if (!form || !button) {
        return;
      }

      form.addEventListener("submit", function (event) {
        if (!formController.validateForm()) {
          event.preventDefault();
          return;
        }
        formController.setLoading(true);
      });

      // Ripple feedback on every button.
      button.addEventListener("pointerdown", animations.createRipple);
    },

    /** Toggle the loading state: disable the submit button, lock the
     *  location fields without excluding them from native form submission,
     *  and drive the spinner via .btn--loading. */
    setLoading: function (loading) {
      var button = document.getElementById("submitBtn");
      if (!button) {
        return;
      }

      button.disabled = loading;
      button.classList.toggle("btn--loading", loading);

      var text = button.querySelector(".btn__text");
      if (text) {
        text.textContent = loading ? "Searching..." : "Find Route";
      } else {
        button.textContent = loading ? "Searching..." : "Find Route";
      }

      formController.FIELDS.forEach(function (name) {
        var input = document.getElementById(name);
        if (input) {
          // Disabled controls are omitted from a native POST. Readonly
          // fields remain successful controls, so Flask receives both
          // locations when the browser submits the form.
          input.readOnly = loading;
        }
      });
    },

    /** Validate one field: required, whitespace-trimmed. Returns true
     *  when the field has content. */
    validateField: function (name) {
      var input = document.getElementById(name);
      if (!input) {
        return true;
      }
      var value = input.value.trim();
      if (!value) {
        formController.showFieldError(name, "This field is required");
        return false;
      }
      formController.clearFieldError(name);
      var field = input.closest(".form-field");
      if (field) {
        field.classList.add("form-field--valid");
      }
      return true;
    },

    /** Validate every field; returns true when the whole form is valid. */
    validateForm: function () {
      var valid = true;
      formController.FIELDS.forEach(function (name) {
        if (!formController.validateField(name)) {
          valid = false;
        }
      });
      return valid;
    },

    /** Surface a validation error: error text, aria-invalid, the
     *  .form-field--error class (which drives the CSS shake/border). */
    showFieldError: function (name, message) {
      var input = document.getElementById(name);
      var field = input ? input.closest(".form-field") : null;
      var errorEl = document.getElementById(name + "Error");
      if (!input || !field) {
        return;
      }
      input.setAttribute("aria-invalid", "true");
      field.classList.add("form-field--error");
      field.classList.remove("form-field--valid");
      if (errorEl) {
        errorEl.textContent = message;
      }
    },

    /** Clear the validation error state for one field. */
    clearFieldError: function (name) {
      var input = document.getElementById(name);
      var field = input ? input.closest(".form-field") : null;
      var errorEl = document.getElementById(name + "Error");
      if (!input) {
        return;
      }
      input.setAttribute("aria-invalid", "false");
      if (field) {
        field.classList.remove("form-field--error");
        // Keep the valid checkmark while the field still has content;
        // drop it once emptied so it cannot go stale.
        if (!input.value.trim()) {
          field.classList.remove("form-field--valid");
        }
      }
      if (errorEl) {
        errorEl.textContent = "";
      }
    },

    /** Debounced real-time validation on input (300ms quiet period). */
    attachValidation: function () {
      var debouncedValidate = utils.debounce(function (event) {
        formController.validateField(event.target.id);
      }, 300);

      formController.FIELDS.forEach(function (name) {
        var input = document.getElementById(name);
        if (!input) {
          return;
        }
        input.addEventListener("input", function (event) {
          // Clear immediately so stale errors do not linger while typing.
          formController.clearFieldError(name);
          formController.syncClearButton(name);
          debouncedValidate(event);
        });
        // Only validate on blur after user has started typing
        input.addEventListener("blur", function () {
          // Skip validation if field is empty and hasn't been touched
          if (input.value.length === 0 && !input.getAttribute("data-touched")) {
            return;
          }
          formController.validateField(name);
        });
        
        // Mark field as touched when user types
        input.addEventListener("input", function() {
          input.setAttribute("data-touched", "true");
        }, { once: true });
      });
    },

    /** Show/hide the field clear button based on the input's current
     *  value. Runs on input events and once at load (server pre-fills
     *  values but the buttons start hidden). */
    syncClearButton: function (name) {
      var input = document.getElementById(name);
      var clear = input
        ? input.closest(".form-field__input-wrapper").querySelector(".form-field__clear")
        : null;
      if (!input || !clear) {
        return;
      }
      if (input.value.length > 0) {
        clear.removeAttribute("hidden");
      } else {
        clear.setAttribute("hidden", "");
      }
    },

    /** Wire clear-button clicks: empty the field, resync, refocus. */
    attachClearButtons: function () {
      var clearButtons = document.querySelectorAll(".form-field__clear");
      Array.prototype.forEach.call(clearButtons, function (clear) {
        clear.addEventListener("click", function () {
          var wrapper = clear.closest(".form-field__input-wrapper");
          var input = wrapper ? wrapper.querySelector(".form-field__input") : null;
          if (!input) {
            return;
          }
          input.value = "";
          formController.syncClearButton(input.id);
          formController.clearFieldError(input.id);
          input.focus();
        });
      });
    },

    /** Sync segmented-control radios: aria-checked mirrors the checked
     *  state on change and exposes the selected option to CSS so the
     *  slider remains aligned with the labels at every width. */
    attachSegmentedSync: function () {
      var radios = document.querySelectorAll(".segmented-control__input");
      Array.prototype.forEach.call(radios, function (radio) {
        var syncGroup = function () {
          var group = radio.closest(".segmented-control");
          if (!group) {
            return;
          }
          var siblings = group.querySelectorAll(".segmented-control__input");
          var selectedIndex = 0;
          Array.prototype.forEach.call(siblings, function (r) {
            r.setAttribute("aria-checked", r.checked ? "true" : "false");
            if (r.checked) {
              selectedIndex = Array.prototype.indexOf.call(siblings, r);
            }
          });
          group.setAttribute("data-selected-index", String(selectedIndex));
        };

        radio.addEventListener("change", syncGroup);
        syncGroup();
      });
    }
  };

  var sidebarController = {
    initialize: function () {
      var sidebar = document.getElementById("formSidebar");
      var button = document.getElementById("collapseBtn");
      if (!sidebar || !button) {
        return;
      }

      var idleTimer = null;
      var show = function () {
        sidebar.classList.remove("form-sidebar--idle");
        if (idleTimer) {
          clearTimeout(idleTimer);
        }
        idleTimer = setTimeout(function () {
          var mobileQuery = getMediaQuery("(max-width: 767px)");
          if (mobileQuery && mobileQuery.matches &&
              document.activeElement &&
              !sidebar.contains(document.activeElement)) {
            sidebar.classList.add("form-sidebar--idle");
          }
        }, 1800);
      };

      button.addEventListener("click", function () {
        show();
        var collapsed = sidebar.classList.toggle("form-sidebar--collapsed");
        button.setAttribute("aria-expanded", collapsed ? "false" : "true");
        button.setAttribute(
          "aria-label",
          collapsed ? "Expand sidebar" : "Collapse sidebar");
      });

      ["scroll", "wheel", "touchstart", "pointerdown"].forEach(function (eventName) {
        window.addEventListener(eventName, show, { passive: true });
      });
      sidebar.addEventListener("focusin", show);
      show();
    }
  };

  var tripSummaryController = {
    initialize: function () {
      var card = document.querySelector(".trip-summary-card");
      var button = document.getElementById("tripSummaryToggle");
      if (!card || !button) {
        return;
      }
      var panel = document.getElementById("resultsPanel");

      button.addEventListener("click", function () {
        var collapsed = card.classList.toggle("trip-summary-card--collapsed");
        if (panel) {
          panel.classList.toggle("results-panel--summary-collapsed", collapsed);
        }
        button.setAttribute("aria-expanded", collapsed ? "false" : "true");
        button.setAttribute("aria-controls", panel ? "resultsPanel" : "tripSummaryContent");
        button.setAttribute(
          "aria-label",
          collapsed ? "Expand trip summary" : "Collapse trip summary");
      });
    }
  };

  var mapLayoutController = {
    initialize: function () {
      var mapContainer = document.getElementById("mapContainer");
      var resultsPanel = document.getElementById("resultsPanel");
      if (!mapContainer || !resultsPanel) {
        return;
      }

      var updateControls = function () {
        var panelRect = resultsPanel.getBoundingClientRect();
        var visible = panelRect.width > 0 && panelRect.height > 0 &&
          getComputedStyle(resultsPanel).opacity !== "0";
        var rightInset = 16;

        if (visible && panelRect.left < window.innerWidth) {
          rightInset = Math.max(16, window.innerWidth - panelRect.left + 16);
        }

        mapContainer.style.setProperty(
          "--map-controls-right",
          rightInset + "px"
        );
      };

      updateControls();
      window.addEventListener("resize", updateControls, { passive: true });
      resultsPanel.addEventListener("transitionend", updateControls);
      // The panel fades in with a CSS animation (not a transition), so the
      // first check can run while it is still at opacity 0. Re-check when
      // the animation ends, whenever the panel resizes, and once as a
      // backstop; otherwise the map buttons can stay hidden behind it.
      resultsPanel.addEventListener("animationend", updateControls);
      if (typeof ResizeObserver === "function") {
        new ResizeObserver(updateControls).observe(resultsPanel);
      }
      window.setTimeout(updateControls, 800);

      if (typeof MutationObserver === "function") {
        var observer = new MutationObserver(updateControls);
        observer.observe(resultsPanel, {
          attributes: true,
          attributeFilter: ["class", "style"]
        });
      }
    }
  };
  // accessibilityController (Tasks 11.1-11.3)
  var accessibilityController = {
    /** Announce a message via the polite live region. */
    announce: function (message) {
      var region = document.getElementById("sr-announcements");
      if (!region || !message) {
        return;
      }
      // Clear first so identical consecutive messages re-announce.
      region.textContent = "";
      setTimeout(function () {
        region.textContent = message;
      }, 50);
    },

    /** Global keyboard shortcuts:
     *  Alt+O / Alt+D focus the origin/destination inputs; Escape hides
     *  the results panel and dismisses all toasts. */
    attachKeyboardShortcuts: function () {
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          var panel = document.getElementById("resultsPanel");
          if (panel) {
            panel.classList.remove("results-panel--visible");
          }
          toastManager.dismissAll();
          return;
        }

        if (event.altKey && !event.ctrlKey && !event.metaKey) {
          var key = String(event.key).toLowerCase();
          if (key === "o" || key === "d") {
            event.preventDefault();
            var input = document.getElementById(key === "o" ? "origin" : "destination");
            if (input) {
              input.focus();
            }
          }
        }
      });
    },

    /** Keep Tab focus inside a container (mobile full-screen results
     *  overlay). Minimal trap: wraps at both ends. */
    trapFocus: function (container) {
      if (!container) {
        return;
      }
      container.addEventListener("keydown", function (event) {
        if (event.key !== "Tab") {
          return;
        }
        var focusable = container.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (!focusable.length) {
          return;
        }
        var first = focusable[0];
        var last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      });
    },

    /** Track input modality: pointer use adds body.using-mouse
     *  (suppressing focus outlines); Tab removes it so keyboard users
     *  always see :focus-visible outlines. */
    attachModalityTracking: function () {
      document.addEventListener("mousedown", function () {
        document.body.classList.add("using-mouse");
      });
      document.addEventListener("touchstart", function () {
        document.body.classList.add("using-mouse");
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Tab") {
          document.body.classList.remove("using-mouse");
        }
      });
    },

    /** Wire everything at load. */
    initialize: function () {
      accessibilityController.attachKeyboardShortcuts();
      accessibilityController.attachModalityTracking();

      var resultsPanel = document.getElementById("resultsPanel");
      if (resultsPanel) {
        accessibilityController.trapFocus(resultsPanel);
      }
    }
  };
  var errorHandler = {
    BANNER_ID: "networkBanner",

    /** Contextual help copy for known server error titles. */
    KNOWN_ERRORS: {
      "No GraphHopper API key found":
        "Add your GraphHopper API key and resubmit - no restart needed.",
      "Origin and destination are required":
        "Fill in both fields before searching."
    },

    /** On load, mirror server-rendered .alert text into an error toast
     *  (the inline alert remains the no-JS fallback). */
    mirrorServerAlerts: function () {
      var alerts = document.querySelectorAll(".alert");
      Array.prototype.forEach.call(alerts, function (alert) {
        var title = alert.querySelector("h2");
        var detail = alert.querySelector("p");
        var message = title ? title.textContent.trim() : alert.textContent.trim();
        errorHandler.log(message, detail ? detail.textContent.trim() : "");
        errorHandler.showContextualToast(message);
      });
    },

    /** Map known error titles to friendlier help copy. */
    showContextualToast: function (message) {
      var help = errorHandler.KNOWN_ERRORS[message];
      toastManager.show(help ? help : message, "error");
    },

    /** Offline/online listeners drive a network banner with a Retry
     *  action. */
    attachNetworkBanner: function () {
      window.addEventListener("offline", function () {
        errorHandler.showNetworkBanner();
      });
      window.addEventListener("online", function () {
        errorHandler.removeNetworkBanner();
      });
      if (window.navigator && navigator.onLine === false) {
        errorHandler.showNetworkBanner();
      }
    },

    showNetworkBanner: function () {
      if (document.getElementById(errorHandler.BANNER_ID)) {
        return;
      }
      var banner = document.createElement("div");
      banner.id = errorHandler.BANNER_ID;
      banner.className = "network-banner";
      banner.setAttribute("role", "alert");
      banner.innerHTML =
        '<span class="network-banner__text">You are offline. Check your connection.</span>' +
        '<button class="network-banner__retry btn btn--secondary" type="button">Retry</button>';
      banner.querySelector(".network-banner__retry")
        .addEventListener("click", function () {
          window.location.reload();
        });
      document.body.appendChild(banner);
    },

    removeNetworkBanner: function () {
      var banner = document.getElementById(errorHandler.BANNER_ID);
      if (banner && banner.parentNode) {
        banner.parentNode.removeChild(banner);
      }
    },

    /** Central console logging for JS-side errors. */
    log: function (message, detail) {
      console.error("[app]", message, detail || "");
    }
  };
  // directionsController: the turn-by-turn list lives in a panel over
  // the map, opened and closed by the list button in the map controls.
  var directionsController = {
    initialize: function () {
      var button = document.getElementById("directionsToggleBtn");
      var panel = document.getElementById("directionsPanel");
      var closeBtn = document.getElementById("directionsCloseBtn");
      if (!button || !panel) {
        return;
      }
      function setOpen(open, returnFocus) {
        panel.hidden = !open;
        button.setAttribute("aria-expanded", open ? "true" : "false");
        button.setAttribute("aria-label",
          open ? "Hide turn-by-turn directions" : "Show turn-by-turn directions");
        button.classList.toggle("map-control-btn--active", open);
        if (open && closeBtn) {
          closeBtn.focus();
        } else if (!open && returnFocus) {
          button.focus();
        }
      }
      button.addEventListener("click", function () {
        setOpen(panel.hidden, false);
      });
      if (closeBtn) {
        closeBtn.addEventListener("click", function () {
          setOpen(false, true);
        });
      }
      panel.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          event.stopPropagation();
          setOpen(false, true);
        }
      });
    }
  };

  // init + DOMContentLoaded
  function init() {
    themeManager.initialize();
    themeManager.attachThemeToggle();
    accessibilityController.initialize();
    errorHandler.mirrorServerAlerts();
    errorHandler.attachNetworkBanner();
    formController.attachSubmitFeedback();
    formController.attachValidation();
    formController.attachClearButtons();
    formController.attachSegmentedSync();
    sidebarController.initialize();
    tripSummaryController.initialize();
    mapLayoutController.initialize();
    directionsController.initialize();

    // Server pre-fills values; sync clear buttons on load.
    formController.FIELDS.forEach(function (name) {
      formController.syncClearButton(name);
    });

    mapController.initializeMap();

    // Orchestrate the post-render reveal only when a route exists.
    if (window.routePoints && window.routePoints.length > 0) {
      resultsController.attachStepInteractions();
      resultsController.showSuccessToast();
      animations.orchestrateRouteDisplay();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();


// Show the gas price field for car trips and the weight field for walk/bike.
(function profileFieldsController() {
  function sync() {
    const checked = document.querySelector('input[name="profile"]:checked');
    if (!checked) return;
    document.querySelectorAll("[data-profiles]").forEach((field) => {
      field.hidden = !field.dataset.profiles.split(" ").includes(checked.value);
    });
  }
  document.querySelectorAll('input[name="profile"]').forEach((radio) => {
    radio.addEventListener("change", sync);
  });
  sync();
})();
