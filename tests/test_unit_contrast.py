"""Colour-contrast regression tests for the palette in css/style.css.

The light palette shipped below WCAG AA at one point: the teal accent measured
3.15:1 and the muted grey 3.51:1 against the page background, so every body
link and every mono micro-label failed the 4.5:1 floor for normal-size text.
Both were corrected by pulling lightness down while holding hue and saturation.

These colours are easy to nudge by eye later and hard to eyeball for contrast,
so the ratios are asserted rather than left to review. If a change here fails,
darken the token rather than lowering the threshold.
"""
import re

import pytest

# Normal-size text under WCAG 2.1 AA. The site sets its micro-labels between
# 9.5px and 12px, well under the large-text exemption, so this is the bar that
# applies to nearly all of them.
AA_NORMAL = 4.5


def _parse_tokens(css, selector):
    """Pull the custom properties out of one rule block."""
    match = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S)
    assert match, f"no {selector} block in style.css"
    return dict(re.findall(r"--([\w-]+):\s*([^;]+?)\s*(?:;|/\*)", match.group(1)))


def _rgb(value):
    value = value.strip()
    if value.startswith("rgba") or value.startswith("rgb"):
        parts = re.findall(r"[\d.]+", value)
        return tuple(float(p) for p in parts[:3])
    value = value.lstrip("#")
    return tuple(float(int(value[i:i + 2], 16)) for i in (0, 2, 4))


def _alpha(value):
    parts = re.findall(r"[\d.]+", value)
    return float(parts[3]) if len(parts) > 3 else 1.0


def _luminance(rgb):
    channels = []
    for c in rgb:
        c /= 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg, bg):
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def _composite(fg, alpha, bg):
    """Flatten a translucent layer onto an opaque one."""
    return tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg, bg))


@pytest.fixture(scope="module")
def palettes(site_root):
    css = (site_root / "css" / "style.css").read_text(encoding="utf-8")
    light = _parse_tokens(css, ":root")
    dark = _parse_tokens(css, '[data-theme="dark"]')
    # Dark mode overrides only some tokens; the rest fall through to :root.
    return {"light": light, "dark": {**light, **dark}}


def _pairings(tokens):
    """Every foreground/background combination the stylesheet actually renders."""
    bg = _rgb(tokens["bg"])
    surface = _rgb(tokens["surface"])
    code_bg = _rgb(tokens["code-bg"])
    text = _rgb(tokens["text"])
    text_lt = _rgb(tokens["text-lt"])
    accent = _rgb(tokens["accent"])
    accent_dk = _rgb(tokens["accent-dk"])

    # The current-week row and every card hover tint their background, which is
    # the worst case for anything sitting on top of them.
    wash = _composite(_rgb(tokens["accent-wash"]), _alpha(tokens["accent-wash"]), bg)

    return [
        ("body text on page", text, bg),
        ("muted labels on page", text_lt, bg),
        ("links on page", accent, bg),
        ("link hover on page", accent_dk, bg),
        ("body text in card", text, surface),
        ("muted labels in card", text_lt, surface),
        ("links in card", accent, surface),
        ("accent on hover wash", accent, wash),
        ("muted labels on hover wash", text_lt, wash),
        ("link hover on wash", accent_dk, wash),
        ("body text on code background", text, code_bg),
    ]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_text_colours_meet_wcag_aa(palettes, theme):
    failures = []
    for label, fg, bg in _pairings(palettes[theme]):
        ratio = _contrast(fg, bg)
        if ratio < AA_NORMAL:
            failures.append(f"{label}: {ratio:.2f}:1 (needs {AA_NORMAL}:1)")
    assert not failures, f"{theme} mode below WCAG AA: {failures}"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_link_hover_is_distinguishable_from_link(palettes, theme):
    """Hover must actually shift, and shift far enough to notice."""
    tokens = palettes[theme]
    bg = _rgb(tokens["bg"])
    accent = _contrast(_rgb(tokens["accent"]), bg)
    hover = _contrast(_rgb(tokens["accent-dk"]), bg)
    assert abs(hover - accent) >= 0.5, (
        f"{theme}: --accent ({accent:.2f}:1) and --accent-dk ({hover:.2f}:1) "
        "are too close to read as a state change"
    )
