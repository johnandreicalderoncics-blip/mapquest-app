"""Tests for Task 11.4: WCAG contrast verification of design tokens.

Parses the token values straight out of style.css (:root for light,
[data-theme="dark"] for dark) and computes WCAG 2.x contrast ratios.
Thresholds follow usage: 4.5 for body/error text, 3.0 for icons,
borders and large graphical elements.
"""

import os
import re

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _block_tokens(css: str, header: str) -> dict:
    idx = css.find(header)
    assert idx != -1, f"{header} not found"
    start = css.find("{", idx)
    depth = 1
    pos = start + 1
    while pos < len(css) and depth > 0:
        if css[pos] == "{":
            depth += 1
        elif css[pos] == "}":
            depth -= 1
        pos += 1
    body = css[start + 1:pos - 1]
    tokens = {}
    for match in re.finditer(r"--color[\w-]*:\s*(#[0-9a-fA-F]{6})", body):
        name = match.group(0).split(":")[0].strip()
        tokens[name] = match.group(1)
    return tokens


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    adjusted = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        for c in channels
    ]
    return (0.2126 * adjusted[0] + 0.7152 * adjusted[1] + 0.0722 * adjusted[2])


def _ratio(fore: str, back: str) -> float:
    lf, lb = _relative_luminance(fore), _relative_luminance(back)
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_light_theme_contrast():
    tokens = _block_tokens(_css(), ":root {")
    checks = [
        ("--color-text-primary", "--color-bg-card", 4.5, "body text"),
        ("--color-text-secondary", "--color-bg-card", 4.5, "secondary text"),
        ("--color-text-tertiary", "--color-bg-card", 4.5, "help text"),
        ("--color-error", "--color-bg-card", 4.5, "error text"),
        ("--color-success", "--color-success-bg", 3.0, "success icons"),
        ("--color-warning", "--color-warning-bg", 3.0, "warning icons"),
        ("--color-warning", "--color-bg-card", 3.0, "warning borders"),
        ("--color-text-inverse", "--color-primary", 4.5, "button text"),
    ]
    failures = []
    for fore, back, threshold, usage in checks:
        ratio = _ratio(tokens[fore], tokens[back])
        if ratio < threshold:
            failures.append(f"{fore} on {back} ({usage}): {ratio:.2f} < {threshold}")
    assert not failures, "Light-theme contrast failures:\n" + "\n".join(failures)


def test_dark_theme_contrast():
    css = _css()
    # Dark overrides cascade over :root defaults.
    tokens = {**_block_tokens(css, ":root {"),
              **_block_tokens(css, '[data-theme="dark"] {')}
    checks = [
        ("--color-text-primary", "--color-bg-card", 4.5, "body text"),
        ("--color-text-secondary", "--color-bg-card", 4.5, "secondary text"),
        ("--color-text-tertiary", "--color-bg-card", 4.5, "help text"),
        ("--color-error", "--color-bg-card", 4.5, "error text"),
        ("--color-success", "--color-bg-card", 3.0, "success icons"),
        ("--color-warning", "--color-warning-bg", 3.0, "warning icons"),
    ]
    failures = []
    for fore, back, threshold, usage in checks:
        ratio = _ratio(tokens[fore], tokens[back])
        if ratio < threshold:
            failures.append(f"{fore} on {back} ({usage}): {ratio:.2f} < {threshold}")
    assert not failures, "Dark-theme contrast failures:\n" + "\n".join(failures)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
