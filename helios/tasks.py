"""
Celery queued tasks for Helios

2010-08-01
ben@adida.net
"""
import copy
from celery import shared_task
from celery.utils.log import get_logger
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
from urllib.parse import urlparse

from . import election_url_names
from . import signals
from . import utils
from .models import CastVote, Election, Voter, VoterFile, EmailOptOut
from .view_utils import render_template_raw


@shared_task
def cast_vote_verify_and_store(cast_vote_id, status_update_message=None, **kwargs):
    cast_vote = CastVote.objects.get(id=cast_vote_id)
    result = cast_vote.verify_and_store()

    voter = cast_vote.voter
    election = voter.election
    user = voter.get_user()

    if result:
        # send the signal
        signals.vote_cast.send(sender=election, election=election, user=user, voter=voter, cast_vote=cast_vote)

        if status_update_message and user.can_update_status():
            user.update_status(status_update_message)
    else:
        logger = get_logger(cast_vote_verify_and_store.__name__)
        logger.error("Failed to verify and store %d" % cast_vote_id)


@shared_task
def voters_email(election_id, subject_template, body_template, extra_vars={},
                 voter_constraints_include=None, voter_constraints_exclude=None):
    """
    voter_constraints_include are conditions on including voters
    voter_constraints_exclude are conditions on excluding voters
    """
    election = Election.objects.get(id=election_id)

    # select the right list of voters
    voters = election.voter_set.all()
    if voter_constraints_include:
        voters = voters.filter(**voter_constraints_include)
    if voter_constraints_exclude:
        voters = voters.exclude(**voter_constraints_exclude)

    for voter in voters:
        single_voter_email.delay(voter.uuid, subject_template, body_template, extra_vars)


@shared_task
def voters_notify(election_id, notification_template, extra_vars={}):
    election = Election.objects.get(id=election_id)
    for voter in election.voter_set.all():
        single_voter_notify.delay(voter.uuid, notification_template, extra_vars)


@shared_task
def single_voter_email(voter_uuid, subject_template, body_template, extra_vars={}):
    voter = Voter.objects.get(uuid=voter_uuid)
    
    # Check if voter email is opted out
    voter_email = voter.voter_email or (voter.user and voter.user.user_id)
    if voter_email and EmailOptOut.is_opted_out(voter_email):
        logger = get_logger(single_voter_email.__name__)
        logger.info(f"Skipping email to opted-out voter {voter.uuid}")
        return

    the_vars = copy.copy(extra_vars)
    the_vars.update({'election': voter.election})
    the_vars.update({'voter': voter})

    # A password voter is never sent a password. They are sent a single-use
    # link on which they choose their own, so that no copy of the credential
    # survives in anyone's sent folder or in the database.
    if voter.voter_type == 'password' and voter.voter_login_id and voter.election.uuid:
        issue_login_token = the_vars.pop('issue_login_token', False)

        if issue_login_token or not voter.has_password:
            token = voter.generate_login_token()
            voter.save()
            setup_path = reverse(election_url_names.ELECTION_VOTER_SETUP_CREDENTIALS,
                                 args=[voter.election.uuid, token])
            the_vars['voter_setup_url'] = f"{settings.SECURE_URL_HOST}{setup_path}"

        resend_path = reverse(election_url_names.ELECTION_PASSWORD_VOTER_RESEND,
                              args=[voter.election.uuid])
        the_vars['password_resend_url'] = f"{settings.SECURE_URL_HOST}{resend_path}"

    # Add unsubscribe link to email context
    if voter_email:
        unsubscribe_code = utils.generate_email_confirmation_code(voter_email, 'optout')
        unsubscribe_path = reverse('optout_confirm', kwargs={'email': voter_email, 'code': unsubscribe_code})
        unsubscribe_url = f"{settings.URL_HOST}{unsubscribe_path}"
        
        the_vars.update({
            'unsubscribe_url': unsubscribe_url,
            'unsubscribe_code': unsubscribe_code
        })

    subject = render_template_raw(None, subject_template, the_vars)
    body = render_template_raw(None, body_template, the_vars)

    voter.send_message(subject, body)


@shared_task
def single_voter_notify(voter_uuid, notification_template, extra_vars={}):
    voter = Voter.objects.get(uuid=voter_uuid)

    the_vars = copy.copy(extra_vars)
    the_vars.update({'voter': voter})

    notification = render_template_raw(None, notification_template, the_vars)

    voter.send_notification(notification)


@shared_task
def election_compute_tally(election_id):
    election = Election.objects.get(id=election_id)
    election.compute_tally()

    election_notify_admin.delay(election_id=election_id,
                                subject=_("encrypted tally computed"),
                                body=_("""
The encrypted tally for election %(election_name)s has been computed.

--
Helios
""") % {'election_name': election.name})

    if election.has_helios_trustee():
        tally_helios_decrypt.delay(election_id=election.id)


@shared_task
def tally_helios_decrypt(election_id):
    election = Election.objects.get(id=election_id)
    election.helios_trustee_decrypt()
    election_notify_admin.delay(election_id=election_id,
                                subject=_('Helios Decrypt'),
                                body=_("""
Helios has decrypted its portion of the tally
for election %(election_name)s.

--
Helios
""") % {'election_name': election.name})


@shared_task
def voter_file_process(voter_file_id):
    voter_file = VoterFile.objects.get(id=voter_file_id)
    voter_file.process()
    election_notify_admin.delay(election_id=voter_file.election.id,
                                subject=_('voter file processed'),
                                body=_("""
Your voter file upload for election %(election_name)s
has been processed.

%(num_voters)s voters have been created.

--
Helios
""") % {'election_name': voter_file.election.name, 'num_voters': voter_file.num_voters})


@shared_task
def notify_admin_opted_out_voters(election_id, opted_out_voters):
    election = Election.objects.get(id=election_id)
    
    if not opted_out_voters:
        return
    
    subject = _("Opted-out voters not added to election %(election_name)s") % {'election_name': election.name}

    body = _("""
The following %(num_voters)s voters could not be added to election "%(election_name)s" 
because they have opted out of receiving Helios emails:

""") % {'num_voters': len(opted_out_voters), 'election_name': election.name}

    for voter in opted_out_voters:
        body += _("- %(name)s (%(email)s) [ID: %(voter_id)s, Type: %(voter_type)s]\n") % {
            'name': voter['name'], 'email': voter['email'],
            'voter_id': voter['voter_id'], 'voter_type': voter['voter_type']}

    optin_path = reverse('optin_form')
    optin_url = f"{settings.URL_HOST}{optin_path}"

    body += _("""

These voters will need to opt back in before they can be added to elections.
They can opt back in at: %(optin_url)s

--
Helios
""") % {'optin_url': optin_url}
    
    election.admin.send_message(subject, body)


@shared_task
def election_notify_admin(election_id, subject, body):
    election = Election.objects.get(id=election_id)
    election.admin.send_message(subject, body)
