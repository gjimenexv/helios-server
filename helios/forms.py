"""
Forms for Helios
"""

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .branding import validate_color_contrast
from .fields import DateTimeLocalField
from .models import Election

HEX_COLOR_WIDGET = forms.TextInput(attrs={'type': 'color'})


class ElectionForm(forms.Form):
  short_name = forms.SlugField(max_length=40, help_text=_('no spaces, will be part of the URL for your election, e.g. my-club-2010'))
  name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':60}), help_text=_('the pretty name for your election, e.g. My Club 2010 Election'))
  description = forms.CharField(max_length=4000, widget=forms.Textarea(attrs={'cols': 70, 'wrap': 'soft'}), required=False)
  election_type = forms.ChoiceField(label=_("type"), choices = Election.ELECTION_TYPES)
  use_voter_aliases = forms.BooleanField(required=False, initial=False, help_text=_('If selected, voter identities will be replaced with aliases, e.g. "V12", in the ballot tracking center'))
  #use_advanced_audit_features = forms.BooleanField(required=False, initial=True, help_text='disable this only if you want a simple election with reduced security but a simpler user interface')
  randomize_answer_order = forms.BooleanField(required=False, initial=False, help_text=_('enable this if you want the answers to questions to appear in random order for each voter'))
  private_p = forms.BooleanField(required=False, initial=False, label=_("Private?"), help_text=_('A private election is only visible to registered voters.'))
  help_email = forms.CharField(required=False, initial="", label=_("Help Email Address"), help_text=_('An email address voters should contact if they need help.'))

  if settings.ALLOW_ELECTION_INFO_URL:
    election_info_url = forms.CharField(required=False, initial="", label=_("Election Info Download URL"), help_text=_("the URL of a PDF document that contains extra election information, e.g. candidate bios and statements"))

  # times
  voting_starts_at = DateTimeLocalField(help_text = _('UTC date and time when voting begins'),
                                   required=False)
  voting_ends_at = DateTimeLocalField(help_text = _('UTC date and time when voting ends'),
                                   required=False)

class ElectionTimeExtensionForm(forms.Form):
  voting_extended_until = DateTimeLocalField(help_text = _('UTC date and time voting extended to'),
                                   required=False)

class ElectionBrandingForm(forms.Form):
  logo = forms.ImageField(required=False, label=_("Logo"),
                           help_text=_("PNG, JPEG, or GIF, shown at the top of your election's pages. Leave blank to keep the current logo, or use \"clear\" to remove it and fall back to the site default."))
  logo_clear = forms.BooleanField(required=False, label=_("Remove current logo"))
  primary_color = forms.CharField(required=False, label=_("Primary color"), widget=HEX_COLOR_WIDGET,
                                   help_text=_("Used for buttons, links, and highlights. Leave blank to use the site default."))
  accent_color = forms.CharField(required=False, label=_("Accent color"), widget=HEX_COLOR_WIDGET,
                                  help_text=_("Used for secondary highlights. Leave blank to use the site default."))

  def _clean_color(self, field_name):
    value = self.cleaned_data.get(field_name)
    if not value:
      return value
    value = value.strip()
    if not value.startswith('#') or len(value) not in (4, 7):
      raise ValidationError(_("Enter a valid hex color, e.g. #1a73e8."))
    validate_color_contrast(value, label=self.fields[field_name].label)
    return value

  def clean_primary_color(self):
    return self._clean_color('primary_color')

  def clean_accent_color(self):
    return self._clean_color('accent_color')

class EmailVotersForm(forms.Form):
  subject = forms.CharField(max_length=80)
  body = forms.CharField(max_length=4000, widget=forms.Textarea)
  send_to = forms.ChoiceField(label=_("Send To"), initial="all", choices= [('all', _('all voters')), ('voted', _('voters who have cast a ballot')), ('not-voted', _('voters who have not yet cast a ballot'))])

class TallyNotificationEmailForm(forms.Form):
  subject = forms.CharField(max_length=80)
  body = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
  send_to = forms.ChoiceField(label=_("Send To"), choices= [('all', _('all voters')), ('voted', _('only voters who cast a ballot')), ('none', _('no one -- are you sure about this?'))])

class VoterPasswordForm(forms.Form):
  voter_id = forms.CharField(max_length=50, label=_("Voter ID"))
  password = forms.CharField(widget=forms.PasswordInput(), max_length=100)

class VoterPasswordResendForm(forms.Form):
  voter_id = forms.CharField(max_length=50, label=_("Voter ID"), help_text=_("Enter the voter ID you were assigned for this election"))

class VoterCredentialsSetupForm(forms.Form):
  """
  Where a voter chooses their own password, from the single-use link they were
  emailed. The password is hashed immediately and never stored in the clear.
  """
  password = forms.CharField(widget=forms.PasswordInput(), max_length=100, label=_("Choose a password"))
  password_confirm = forms.CharField(widget=forms.PasswordInput(), max_length=100, label=_("Confirm your password"))

  def clean_password(self):
    password = self.cleaned_data['password'].strip()
    min_length = settings.HELIOS_VOTER_PASSWORD_MIN_LENGTH
    if len(password) < min_length:
      raise ValidationError(_("Your password must be at least %(min_length)s characters long.") % {'min_length': min_length})
    return password

  def clean(self):
    cleaned_data = super().clean()
    password = cleaned_data.get('password')
    password_confirm = cleaned_data.get('password_confirm')

    if password and password_confirm and password != password_confirm.strip():
      self.add_error('password_confirm', _("The two passwords do not match."))

    return cleaned_data

