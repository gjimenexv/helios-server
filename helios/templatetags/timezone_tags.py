"""
Template tags for timezone display in Helios
"""

import datetime

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from helios.timezone_utils import format_election_time

register = template.Library()


@register.filter(name='election_time')
def election_time(value):
  """
  Render a stored (naive UTC) datetime on the election's own clock.

  Every viewer sees the same wall-clock time -- the one the administrator
  scheduled -- rather than a per-browser conversion, so what an email, an
  admin screen and a voter's screen say about the closing time always agree.

  Usage in templates:
    {{ election.voting_starts_at|election_time }}
  """
  if value is None:
    return ''

  # Only accept date/datetime values; anything else is escaped rather than
  # trusted, since these render into mark_safe output below.
  # (datetime.datetime is a subclass of datetime.date, so datetime first.)
  if not isinstance(value, (datetime.datetime, datetime.date)):
    return escape(str(value))

  formatted = escape(format_election_time(value))

  return mark_safe(f'<span class="tz-timestamp">{formatted}</span>')
