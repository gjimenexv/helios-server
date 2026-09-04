"""
Timezone helpers for Helios.

Helios stores every datetime in the database as a *naive UTC* value
(``USE_TZ = False`` and ``TIME_ZONE = 'UTC'``, so both ``datetime.utcnow()``
and Django's ``auto_now_add`` produce the same clock). Nothing in the
database is ever in a local zone.

Elections, however, are run in one place, on one wall clock. An administrator
who types "18:00" as the closing time means 18:00 where the election happens,
and every voter must be shown that same 18:00 -- not a per-browser
translation of it. ``settings.ELECTION_TIME_ZONE`` is that wall clock, and
this module is the single place where UTC storage is converted to and from it.

The two directions:

  election_to_utc(naive_local)  -- what the admin typed  -> what we store
  utc_to_election(naive_utc)    -- what we stored        -> what we display
"""

import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings

UTC = datetime.timezone.utc


def election_tz():
  """
  The zone elections are scheduled and displayed in.

  Falls back to UTC rather than raising if the configured name is not a
  known zone: a typo in a deployment's environment should degrade the
  display, not take the site down.
  """
  name = getattr(settings, 'ELECTION_TIME_ZONE', 'UTC')
  try:
    return ZoneInfo(name)
  except (ZoneInfoNotFoundError, ValueError):
    return UTC


def election_tz_label(at=None):
  """
  Short name of the election zone at a given moment, e.g. "CST".

  Takes the moment because zones with daylight saving change label through
  the year; defaults to now.
  """
  moment = at or datetime.datetime.now(UTC)
  if moment.tzinfo is None:
    moment = moment.replace(tzinfo=UTC)
  return moment.astimezone(election_tz()).tzname() or 'UTC'


def utc_to_election(value):
  """
  Naive-UTC (or aware) datetime -> naive datetime on the election clock.

  Returns None unchanged so callers can pass optional fields straight in.
  """
  if value is None:
    return None
  if not isinstance(value, datetime.datetime):
    return value
  aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
  return aware.astimezone(election_tz()).replace(tzinfo=None)


def election_to_utc(value):
  """
  Naive datetime on the election clock -> naive UTC, for storage.

  Ambiguous and non-existent local times (the hour that repeats or is
  skipped at a daylight-saving boundary) are resolved by zoneinfo's default
  fold handling rather than rejected, so a form submission never fails on
  them.
  """
  if value is None:
    return None
  if not isinstance(value, datetime.datetime):
    return value
  if value.tzinfo is not None:
    return value.astimezone(UTC).replace(tzinfo=None)
  return value.replace(tzinfo=election_tz()).astimezone(UTC).replace(tzinfo=None)


def format_election_time(value, fmt='%Y-%m-%d %H:%M'):
  """
  Naive-UTC datetime -> "2026-09-15 18:00 CST" on the election clock.

  A plain date is treated as midnight, matching how the old UTC filter
  rendered dates.
  """
  if value is None:
    return ''
  if not isinstance(value, datetime.datetime):
    if isinstance(value, datetime.date):
      value = datetime.datetime.combine(value, datetime.time())
    else:
      return None
  local = utc_to_election(value)
  return '%s %s' % (local.strftime(fmt), election_tz_label(value))
