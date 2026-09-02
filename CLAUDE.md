# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Helios is an end-to-end verifiable voting system that provides secure, transparent online elections with cryptographic verification. It supports multiple authentication systems (Google, Facebook, GitHub, LDAP, CAS, password, etc.) and uses homomorphic (ElGamal) encryption for privacy-preserving vote tallying.

## Critical Instructions for Claude when preparing a PR

- always run the tests. Install everything and run the tests. Every time.

## Technology Stack

- **Python**: 3.13
- **Framework**: Django 5.2
- **Database**: PostgreSQL 9.5+ (12+ recommended; tests/CI use 16)
- **Task Queue**: Celery with RabbitMQ
- **Crypto**: pycryptodome, custom ElGamal implementation
- **Package Manager**: uv

## Common Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run python manage.py runserver

# Run all tests
uv run python manage.py test -v 2

# Run tests for a specific app
uv run python manage.py test helios -v 2
uv run python manage.py test helios_auth -v 2

# Run a specific test class
uv run python manage.py test helios.tests.ElectionModelTests -v 2

# Database migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Reset database (drops and recreates)
./reset.sh

# Start Celery worker (for background tasks)
uv run celery --app helios worker --events --beat --concurrency 1
```

## Project Structure

- `helios/` - Core election system (models, views, crypto, forms)
- `helios_auth/` - Authentication system with multiple backends
- `server_ui/` - Site shell / admin web interface (home, about, footer/branding, glue between `helios_auth` and `helios`)
- `heliosbooth/` - JavaScript voting booth interface (client-side ballot encryption)
- `heliosverifier/` - JavaScript ballot verification interface (standalone auditing tool)

## Architecture

### Domain model

`Election` (`helios/models.py`) is the aggregate root. It has no status enum — lifecycle is tracked via nullable timestamp fields (`frozen_at`, `voting_starts_at`, `voting_ends_at`, `tallying_started_at`, `deleted_at`, etc.), checked by helper functions in `helios/security.py` (e.g. `do_election_checks`). Related models, all FK'd to `Election`:

- `Voter` - FK to `Election` and to `helios_auth.User` (nullable, for password-only voters); holds the voter's current `CastVote`.
- `CastVote` - the encrypted ballot (`EncryptedVote` LD object), verification hash, cast timestamp.
- `Trustee` - holds a keyshare of the election public key; later publishes a decryption factor + proof.
- `AuditedBallot` - "spoiled" ballots kept for Benaloh-challenge auditing.
- `ElectionLog`, `VoterFile`, `EmailOptOut` - audit trail / voter CSV upload bookkeeping / opt-outs.

All domain models inherit `HeliosModel(models.Model, datatypes.LDObjectContainer)`.

### Crypto/tallying pipeline

1. Client-side JS (`heliosbooth/`, vendored `jscrypto` libs) encrypts each answer as ElGamal ciphertext(s) against the election's public key, with disjunctive zero-knowledge proofs that each ciphertext encodes a valid choice.
2. The server verifies ballot proofs on submission (`helios/crypto/algs.py`, `EncryptedAnswer.verify()` in `helios/workflows/homomorphic.py`) and stores the result as a `CastVote`.
3. Tallying is homomorphic: encrypted choices for a question are multiplied together across all cast ballots without decrypting individual votes.
4. Each `Trustee` independently decrypts their share of the homomorphic sum and publishes a decryption factor + proof of correct decryption; combining all trustees' factors yields the final tally without any single party learning individual votes.
5. `helios/datatypes/` (`LDObject`/`LDObjectField` in `core.py`/`djangofield.py`) is the "Linked Data" serialization layer that lets crypto objects (keys, ciphertexts, proofs) be stored as versioned JSON on Django models and interchanged with the JS clients. `legacy.py` and `2011/01.py` support older election data formats for backward compatibility.

Core crypto lives in `helios/crypto/`: `numtheory.py` (big-integer primitives), `elgamal.py` (`Cryptosystem`, key pairs, encryption/decryption/proofs), `algs.py` (Helios-specific ZK proofs and plaintext handling), `electionalgs.py` (election-level crypto orchestration).

### Async processing

Celery tasks (`helios/tasks.py`, autodiscovered via `helios/celery_app.py`, broker set by `CELERY_BROKER_URL`) handle anything that shouldn't block a request: `cast_vote_verify_and_store`, `voters_email`/`single_voter_email`, `voters_notify`/`single_voter_notify`, `election_compute_tally`, `tally_helios_decrypt`, `voter_file_process` (parses uploaded voter CSVs), and admin notification tasks. In tests, `CELERY_TASK_ALWAYS_EAGER` is forced `True` so tasks run synchronously.

### Authentication

`helios_auth/` is a pluggable auth system independent of core election logic. Each backend lives in `helios_auth/auth_systems/` (`password.py`, `devlogin.py`, `google.py`, `facebook.py`, `github.py`, `gitlab.py`, `linkedin.py`, `live.py`, `yahoo.py`, `cas.py`, `ldapauth.py` + `ldapbackend/`, `openid/`). Enabled backends are controlled by the `AUTH_ENABLED_SYSTEMS` env var (defaults to `ldap,password,google,facebook`); `devlogin` is auto-enabled when `DEBUG` is on. `helios_auth/views.py` dispatches login/callback flows to the selected backend.

### Frontend JS apps

`heliosbooth/` and `heliosverifier/` are vendored, unbuilt legacy JS (no npm/webpack) — jQuery, underscore, and a `jscrypto` library (client-side ElGamal) are checked in directly. Compressed bundles are produced manually via `uglifyjs` (see `heliosbooth/build-helios-booth-compressed.txt` and root `build-helios-main-site-js.txt` for the exact commands); there is no automated JS build step in CI.

## Settings (`settings.py`)

- `get_from_env(var, default)` is the central config helper. It returns the **default** whenever Django's test runner is detected (`TESTING`, via `sys.argv` inspection) regardless of actual env vars, so tests stay hermetic.
- `DATABASES` defaults to a local Postgres `helios` DB, overridden by `DATABASE_URL` (Heroku-style) via `dj_database_url` when present.
- Email backend selection: console (if `DEBUG` + `EMAIL_USE_CONSOLE=1`) → Mailgun via `django-anymail` (if `MAILGUN_API_KEY` set) → AWS SES via `django_ses` (if `EMAIL_USE_AWS=1`).
- LDAP settings (`AUTH_LDAP_*`) are hardcoded to a public test server (`ldap.forumsys.com`) as an example — replace for real LDAP deployments.
- `settings_ci.py` is a separate settings module used by CI (`--settings=settings_ci`).

## Code Style Conventions

### Naming

- **Boolean fields**: Use `_p` suffix (e.g., `private_p`, `frozen_p`, `admin_p`, `featured_p`)
- **Datetime fields**: Use `_at` suffix (e.g., `created_at`, `frozen_at`, `voting_ends_at`)
- **Functions/methods**: snake_case
- **Classes**: PascalCase

### Indentation

- Use 2-space indentation throughout Python files

### Imports

```python
# Standard library
import copy, csv, datetime, uuid

# Third-party
from django.db import models, transaction
import bleach

# Local
from helios import datatypes, utils
from helios_auth.jsonfield import JSONField
```

## Key Patterns

### View Decorators

Use existing security decorators for views:

```python
from helios.security import election_view, election_admin, trustee_check

@election_view(frozen=True)
def my_view(request, election):
    pass

@election_admin()
def admin_view(request, election):
    pass
```

### Model Base Class

All domain models inherit from `HeliosModel`:

```python
class MyModel(HeliosModel):
    class Meta:
        app_label = 'helios'
```

### JSON Responses

```python
from helios.views import render_json
return render_json({'key': 'value'})
```

### Template Rendering

```python
from helios.views import render_template
return render_template(request, 'template_name', {'context': 'vars'})
```

### Database Queries

- Use `@transaction.atomic` for operations that need atomicity
- Prefer `select_related()` for foreign key joins
- Use `get_or_create()` pattern for safe creation

## Security Considerations

- Always use `check_csrf(request)` for POST handlers
- Use `bleach.clean()` for user-provided HTML (see `description_bleached` pattern)
- Never store plaintext passwords; use the auth system's hashing
- Check permissions with `user_can_admin_election()` and similar helpers

## Configuration

Settings use environment variables with defaults:

```python
from settings import get_from_env
MY_SETTING = get_from_env('MY_SETTING', 'default_value')
```

Key environment variables: `DEBUG`, `SECRET_KEY`, `DATABASE_URL`, `CELERY_BROKER_URL`, `AUTH_ENABLED_SYSTEMS` (legacy name `AUTH_ENABLED_AUTH_SYSTEMS` also read)

To enable Google Auth locally: create OAuth2 credentials at https://console.developers.google.com as a web application (origin + `/auth/after/` callback), enable the Google People API, and set `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`.

## Testing

- Tests use Django's TestCase with django-webtest
- Fixtures are in `helios/fixtures/` (includes legacy-format election JSON for backward-compatibility regression tests)
- Test classes: `ElectionModelTests`, `VoterModelTests`, `ElectionBlackboxTests`, etc.
- CI (`.github/workflows/ci.yml`) runs against Python 3.13 / PostgreSQL 16 with `uv run python -Wall manage.py test -v 2 --settings=settings_ci`; there is no separate lint/format CI step.

## Agent skills

### Issue tracker

GitHub Issues on the `origin` fork, `gjimenexv/helios-server`, via the `gh` CLI; `upstream` (`benadida/helios-server`) is read-only context. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles, using their default label strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
