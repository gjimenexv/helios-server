# -*- coding: utf-8 -*-
"""
Branding/theming helpers: resolving effective per-election vs. site-wide
colors and logo, and validating that a chosen color is legible (WCAG
contrast) before it's saved.
"""

from django.conf import settings
from django.core.exceptions import ValidationError

# WCAG 2.1 AA minimum contrast ratio for normal-sized text/UI elements.
WCAG_AA_MIN_CONTRAST = 4.5


def _hex_to_rgb(hex_color):
  hex_color = hex_color.lstrip('#')
  if len(hex_color) == 3:
    hex_color = ''.join(c * 2 for c in hex_color)
  return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb):
  # https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
  def channel(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

  r, g, b = (channel(c) for c in rgb)
  return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_color_a, hex_color_b):
  """
  WCAG contrast ratio between two hex colors, from 1 (no contrast) to 21
  (black on white).
  """
  lum_a = _relative_luminance(_hex_to_rgb(hex_color_a))
  lum_b = _relative_luminance(_hex_to_rgb(hex_color_b))
  lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
  return (lighter + 0.05) / (darker + 0.05)


def validate_color_contrast(hex_color, against='#ffffff', label='color'):
  """
  Raises ValidationError if hex_color would be illegible (below WCAG AA)
  against the given background (white by default, since these colors are
  primarily used for text/buttons on a white page background).
  """
  try:
    ratio = contrast_ratio(hex_color, against)
  except (ValueError, IndexError):
    raise ValidationError(f"'{hex_color}' is not a valid hex color (e.g. #1a73e8).")

  if ratio < WCAG_AA_MIN_CONTRAST:
    raise ValidationError(
      f"This {label} doesn't have enough contrast against a white background "
      f"to be legible (contrast ratio {ratio:.1f}:1, WCAG AA requires at least "
      f"{WCAG_AA_MIN_CONTRAST}:1). Please choose a darker shade."
    )


def _rgb_string(hex_color):
  try:
    return ', '.join(str(c) for c in _hex_to_rgb(hex_color))
  except (ValueError, IndexError):
    return '26, 115, 232'  # falls back to the default primary color's RGB


def get_election_branding(election):
  """
  Resolves the effective branding for an election: its own logo/colors if
  set, falling back to the site-wide defaults from settings.py.
  """
  primary_color = election.primary_color or settings.DEFAULT_PRIMARY_COLOR
  accent_color = election.accent_color or settings.DEFAULT_ACCENT_COLOR
  return {
    'logo_url': election.logo.url if election.logo else settings.MAIN_LOGO_URL,
    'primary_color': primary_color,
    'accent_color': accent_color,
    'primary_color_rgb': _rgb_string(primary_color),
    'accent_color_rgb': _rgb_string(accent_color),
  }


def get_site_branding():
  """
  Site-wide default branding, used on pages with no specific election in
  context (home page, login, etc.).
  """
  return {
    'logo_url': settings.MAIN_LOGO_URL,
    'primary_color': settings.DEFAULT_PRIMARY_COLOR,
    'accent_color': settings.DEFAULT_ACCENT_COLOR,
    'primary_color_rgb': _rgb_string(settings.DEFAULT_PRIMARY_COLOR),
    'accent_color_rgb': _rgb_string(settings.DEFAULT_ACCENT_COLOR),
  }
