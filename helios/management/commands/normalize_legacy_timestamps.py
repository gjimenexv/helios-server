"""
One-off repair for timestamps written before TIME_ZONE became UTC.

Helios stores naive datetimes. Until this release settings.TIME_ZONE was
'America/Los_Angeles', so the fields Django fills in itself (auto_now_add)
were written on the Los Angeles clock, while every field the application sets
explicitly used datetime.utcnow(). The two therefore disagreed by 7 or 8
hours: a ballot cast one minute before an election closed could look like it
arrived hours early, and the ballot tracking centre disagreed with the
election's own schedule.

New rows are consistent. This command shifts the OLD ones -- the rows written
while the setting was wrong -- forward onto UTC.

It refuses to guess which rows those are: pass --before with the moment you
deployed the fix, and only rows stamped before that are touched. Nothing is
written without --apply.

    uv run python manage.py normalize_legacy_timestamps --before 2026-09-04T12:00
    uv run python manage.py normalize_legacy_timestamps --before 2026-09-04T12:00 --apply

Run it once. Running it twice over the same rows would shift them twice.
"""

import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from helios.models import (AuditedBallot, CastVote, Election, ElectionLog,
                           EmailOptOut, Voter, VoterFile)

# The zone the affected rows were written on.
LEGACY_ZONE = ZoneInfo('America/Los_Angeles')

# (model, field) pairs that Django stamped itself, plus Voter.cast_at, which
# is copied verbatim from CastVote.cast_at and so inherited the same skew.
AFFECTED_FIELDS = [
  (Election, 'created_at'),
  (Election, 'modified_at'),
  (ElectionLog, 'at'),
  (VoterFile, 'uploaded_at'),
  (CastVote, 'cast_at'),
  (Voter, 'cast_at'),
  (AuditedBallot, 'added_at'),
  (EmailOptOut, 'opted_out_at'),
]


def to_utc(value):
  """
  A naive datetime that was meant as Los Angeles local time -> naive UTC.
  """
  return (value.replace(tzinfo=LEGACY_ZONE)
               .astimezone(datetime.timezone.utc)
               .replace(tzinfo=None))


class Command(BaseCommand):
  help = "Shift pre-UTC timestamps from the old America/Los_Angeles clock onto UTC."

  def add_arguments(self, parser):
    parser.add_argument(
      '--before', required=True,
      help="Only rows stamped before this naive UTC moment are shifted, in "
           "YYYY-MM-DDTHH:MM form. Use the time you deployed the UTC fix.")
    parser.add_argument(
      '--apply', action='store_true',
      help="Actually write the shifted values. Without it, only report.")

  def handle(self, *args, **options):
    try:
      cutoff = datetime.datetime.strptime(options['before'][:16], '%Y-%m-%dT%H:%M')
    except ValueError:
      raise CommandError("--before must look like 2026-09-04T12:00")

    apply_changes = options['apply']
    total = 0

    with transaction.atomic():
      for model, field in AFFECTED_FIELDS:
        label = '%s.%s' % (model.__name__, field)
        rows = list(model.objects.filter(**{
          '%s__lt' % field: cutoff,
          '%s__isnull' % field: False,
        }).only('id', field))

        if not rows:
          self.stdout.write('%-26s no rows before cutoff' % label)
          continue

        total += len(rows)
        sample = rows[0]
        old = getattr(sample, field)
        self.stdout.write('%-26s %6d rows  (e.g. %s -> %s)'
                          % (label, len(rows), old, to_utc(old)))

        if apply_changes:
          for row in rows:
            setattr(row, field, to_utc(getattr(row, field)))
          # bulk_update, so auto_now_add fields are written as given rather
          # than being re-stamped by save().
          model.objects.bulk_update(rows, [field], batch_size=500)

      if not apply_changes:
        transaction.set_rollback(True)

    if apply_changes:
      self.stdout.write(self.style.SUCCESS('Shifted %d timestamps onto UTC.' % total))
    else:
      self.stdout.write(self.style.WARNING(
        'Dry run: %d timestamps would be shifted. Re-run with --apply.' % total))
