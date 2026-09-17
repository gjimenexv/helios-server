#!/usr/bin/env bash
#
# Deploy the current origin/master to the Helios production host.
#
# Written to be run by a human from their own machine:
#
#     HOST=<VM external IP> bash deploy-production.sh          # show what it would do, change nothing
#     HOST=<VM external IP> bash deploy-production.sh --go     # actually deploy
#
# The full install / backup / teardown procedure is in docs/deploy-gcp.md.
#
# It is deliberately chatty: every step prints what it is about to do, so you
# can stop and read if something looks wrong.
#
# What it does, in order:
#   1. works out the SSH username from your GCE key
#   2. connects and finds the Helios checkout on the server (read-only)
#   3. shows you the current commit there vs. what you are deploying
#   4. git pull, then rebuild and restart the web + worker containers
#   5. checks the site answers afterwards
#
# There is no database migration in this release, so there is nothing to undo
# on the data side. To roll the code back, re-run the git checkout shown at
# the end against the previous commit.

set -euo pipefail

HOST="${HOST:?set HOST to the VM external IP, e.g. HOST=1.2.3.4 bash deploy-production.sh}"
KEY="$HOME/.ssh/google_compute_engine"
BRANCH="master"
GO="${1:-}"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[31mFAILED: %s\033[0m\n' "$*" >&2; exit 1; }

# --- 1. who do we log in as? -------------------------------------------------

[ -f "$KEY" ] || die "no SSH key at $KEY"

# GCE writes the key comment as user@host; that user is the login name.
SSH_USER="$(awk '{print $NF}' "$KEY.pub" 2>/dev/null | cut -d@ -f1)"
[ -n "${SSH_USER:-}" ] || SSH_USER="$USER"

say "Logging in as: $SSH_USER@$HOST"

SSH="ssh -i $KEY -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $SSH_USER@$HOST"

$SSH 'echo connected' >/dev/null 2>&1 \
  || die "cannot SSH in as $SSH_USER. Try another username: SSH_USER=<name> is set from your key comment ($(awk '{print $NF}' "$KEY.pub" 2>/dev/null))"

# --- 2. find the checkout on the server --------------------------------------

# --- 1b. --find: read-only probe, for when the search below comes up empty ---

if [ "$GO" = "--find" ]; then
  say "Home directory"
  $SSH 'ls -la ~ 2>/dev/null | head -40'

  say "Running containers"
  $SSH 'docker ps --format "{{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || echo "(docker not reachable as this user)"'

  say "Directory each running container was started from"
  $SSH 'for c in $(docker ps -q 2>/dev/null); do
          docker inspect "$c" --format "{{.Name}}  {{index .Config.Labels \"com.docker.compose.project.working_dir\"}}" 2>/dev/null
        done'

  say "Any docker-compose.yml under the usual roots"
  $SSH 'find ~ /opt /srv /home /var/www -maxdepth 4 -name docker-compose.yml 2>/dev/null | head -20'

  say "Any Helios checkout (looking for manage.py next to helios/)"
  $SSH 'find ~ /opt /srv /home /var/www -maxdepth 4 -name manage.py 2>/dev/null | head -20'

  cat <<EOF

------------------------------------------------------------------
Read-only probe. Nothing was changed.

Take the directory that holds docker-compose.yml and re-run:

    REPO=/that/path bash deploy-production.sh          # dry run
    REPO=/that/path bash deploy-production.sh --go     # deploy

------------------------------------------------------------------
EOF
  exit 0
fi

say "Looking for the Helios checkout on the server"

# Skip the search entirely if the caller already knows the path:
#     REPO=/path/to/checkout bash deploy-production.sh --go
REPO="${REPO:-}"
if [ -n "$REPO" ]; then
  say "Using the path you gave: $REPO"
  $SSH "[ -f '$REPO/docker-compose.yml' ]" \
    || die "no docker-compose.yml at $REPO on the server"
else
REPO="$($SSH 'for d in /opt/app ~/helios-server ~/helios /opt/helios-server /srv/helios-server /opt/helios /srv/helios; do
            if [ -f "$d/docker-compose.yml" ]; then echo "$d"; exit 0; fi
          done
          # fall back to asking docker where the running stack was started from
          docker inspect helios-web-1 helios_web_1 helios-local-web-1 2>/dev/null \
            | grep -m1 -o "\"com.docker.compose.project.working_dir\": \"[^\"]*\"" \
            | cut -d\" -f4')"

[ -n "$REPO" ] || die "could not find the Helios checkout. Re-run with the path:
    REPO=/path/to/checkout bash deploy-production.sh"
fi

say "Using checkout: $REPO"

# --- 3. show the change --------------------------------------------------------

# /opt/app is root-owned and docker is not reachable as the login user, so
# every git and docker call below goes through sudo. Without it git refuses
# the repo outright ("dubious ownership") and the rebuild never starts.
say "Current state on the server"
$SSH "sudo git -C '$REPO' log --oneline -1 && sudo git -C '$REPO' status --short | head"

say "You are deploying"
git log --oneline -1 "origin/$BRANCH" | cat

if [ "$GO" != "--go" ]; then
  cat <<EOF

------------------------------------------------------------------
This was a dry run. Nothing on the server has been changed.

To actually deploy, run:

    bash deploy-production.sh --go

------------------------------------------------------------------
EOF
  exit 0
fi

# --- 4. deploy ------------------------------------------------------------------

say "Pulling $BRANCH"
$SSH "sudo git -C '$REPO' fetch origin && sudo git -C '$REPO' checkout $BRANCH && sudo git -C '$REPO' pull --ff-only origin $BRANCH"

say "Rebuilding and restarting web + worker (about 30 seconds of downtime)"
# No schema migration and no collectstatic step: the Dockerfile copies the
# source in, and Django serves /static/helios/* off disk.
#
# There IS a one-off data step in the timezone release, to run once after
# this deploy. It only reports until you add --apply:
#   sudo docker compose exec -T web python manage.py \
#     normalize_legacy_timestamps --before <UTC time of this deploy>
$SSH "cd '$REPO' && (sudo docker compose up -d --build web worker || sudo docker-compose up -d --build web worker)"

# --- 5. verify --------------------------------------------------------------------

say "Waiting for the site to come back"
for i in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://$HOST/" || true)"
  [ "$code" = "200" ] && break
  sleep 2
done

say "Site returned HTTP $code"
[ "$code" = "200" ] || die "site is not answering with 200. Check logs:
    $SSH \"cd '$REPO' && sudo docker compose logs --tail=50 web\""

say "Confirming the new stylesheet is being served"
css="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://$HOST/static/helios/css/civic.css" || true)"
say "civic.css returned HTTP $css"

$SSH "sudo git -C '$REPO' log --oneline -1"

cat <<EOF

------------------------------------------------------------------
Deployed. Open http://$HOST/ and hard-reload (Cmd-Shift-R) once:
the booth's templates refresh on their own but vote.html and the
stylesheet are cached normally, so an already-open tab can mix new
templates with old CSS.

To roll back, log in and check out the previous commit:

    $SSH
    sudo git -C '$REPO' checkout <previous-sha> && cd '$REPO' && sudo docker compose up -d --build web worker

------------------------------------------------------------------
EOF
