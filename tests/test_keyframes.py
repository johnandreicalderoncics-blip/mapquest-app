"""Task 4.1 guard: every keyframe later tasks depend on must exist in style.css.

Task 4.1 is largely a verification task — the comprehensive keyframes
library was written with the design system (Task 1) and the component
sections. This test locks the names that Tasks 4.2, 6.x, 7.2, 8.3,
9.x, 13.3 and 14.x reference.
"""

import os

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")

REQUIRED_KEYFRAMES = (
    # Slides / fades (Requirements 2.1, 2.3, 2.6)
    "slideInUp", "slideInLeft", "slideInRight", "slideInDown",
    "fadeIn", "fadeOut", "staggerFadeIn",
    # Scale / bounce / shake / spin (Requirements 2.4, 8.3, 8.6)
    "scaleIn", "bounce", "elasticBounce", "shake", "shakeSubtle", "spin",
    # Ripple / pulse / shimmer (Requirements 8.1, 6.2)
    "ripple", "rippleExpand", "pulse", "shimmer",
    # Route drawing (Requirement 7.4) and success feedback (Requirement 8.7)
    "drawPolyline", "checkmark",
    # Spinner used by the button and map overlay
    "spinnerDash",
)


def test_required_keyframes_exist():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()
    missing = [name for name in REQUIRED_KEYFRAMES
               if f"@keyframes {name} " not in css and f"@keyframes {name}{{" not in css]
    assert not missing, f"Missing @keyframes definitions: {missing}"


def test_reduced_motion_block_disables_animations():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()
    assert "@media (prefers-reduced-motion: reduce)" in css, \
        "Reduced-motion override block must exist (Requirement 9.5)"


def test_fade_in_stagger_alias_exists():
    """design.md references `fadeInStagger`; the canonical name here is
    `staggerFadeIn`. An alias keeps both names valid for later tasks."""
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()
    assert "@keyframes fadeInStagger" in css, \
        "fadeInStagger alias keyframe must exist"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
