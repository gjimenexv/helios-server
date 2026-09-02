"""
Template tags for rendering election results.
"""

from django import template

register = template.Library()


@register.filter(name='share_of')
def share_of(count, answers):
  """
  Width, as a percentage, of one answer's bar in a result readout, scaled so
  the leading answer fills the row.

  Scaling against the maximum rather than the total keeps the comparison
  legible for approval-style questions, where the counts can add up to well
  over the number of voters and a share-of-total bar would be uniformly tiny.

  Usage:
    {{ answer.count|share_of:question.answers }}

  `answers` is the list of {'answer', 'count', 'winner'} dicts that
  Election.pretty_result builds for the question.
  """
  try:
    counts = [int(a['count']) for a in answers]
    value = int(count)
  except (TypeError, ValueError, KeyError):
    return 0

  top = max(counts) if counts else 0
  if top <= 0:
    return 0

  return round(value * 100.0 / top, 2)
