# Deploying Helios on Google Cloud for an election

This is the procedure used to run the ECS 2026 election (August–September 2026).
Follow it top to bottom and you will end up with the same setup: one small
Google Compute Engine VM running the whole app with Docker Compose. When the
election is over, take a backup and tear it down (sections 9 and 10).

Plan on about an hour for a first install. Most of it is waiting for the VM to
build the Docker image.

## What you end up with

```
                 Internet  ──  http://<VM external IP>/   (port 80)
                                   │
 GCE VM "helios-server"  (e2-micro, Ubuntu 24.04, 30 GB disk, 2 GB swap)
 └── /opt/app  (git checkout of this repo + .env)
     └── docker compose
         ├── web     gunicorn, Django app          → host port 80
         ├── worker  celery (emails, voter CSVs, tallies)
         ├── db      postgres:16, data in volume app_pgdata
         └── broker  redis:7 (in-memory only)
```

The services come from `docker-compose.yml` and `Dockerfile` at the repo root.
Nothing else is used: no Cloud SQL, no load balancer, no bucket.

**Cost:** one `e2-micro` with a 30 GB standard disk in `us-central1`,
`us-west1` or `us-east1` falls within GCP's Always Free tier. The external IPv4
address is billed at a few dollars a month. Delete everything when you're done
(section 10) and the bill stops.

## 0. Before you start

You need:

- A Google account with billing enabled on Google Cloud.
- The [`gcloud` CLI](https://cloud.google.com/sdk/docs/install), logged in:
  `gcloud auth login`.
- A **Gmail account to send election mail from**, with 2-Step Verification
  turned on and an **App Password** created for it
  (Google Account → Security → App passwords). Voters see this address, so use
  the organization's account, not a personal one. Gmail allows roughly 500
  messages a day, which covers a roll of a few hundred voters.
- Your election's voter list as a CSV (you upload it later, in the web UI).

## 1. Create the project

```bash
PROJECT=helios-server-deploy        # any globally unique id
gcloud projects create $PROJECT --name="Helios Server"
gcloud config set project $PROJECT
# link billing: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT
gcloud services enable compute.googleapis.com
```

If the project already exists from a previous election, just
`gcloud config set project <id>` and carry on.

## 2. Create the VM and open the firewall

```bash
gcloud compute instances create helios-server \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB --boot-disk-type=pd-standard \
  --tags=http-server,https-server

gcloud compute firewall-rules create allow-web \
  --network=default --direction=INGRESS \
  --allow=tcp:80,tcp:443,tcp:22 --source-ranges=0.0.0.0/0

gcloud compute instances list      # note the EXTERNAL_IP
```

The external IP is **ephemeral**: it survives reboots but can change if the VM
is stopped and started again. Every link in voter emails is built from it, so
don't stop the VM during an election. If you think you might need to, reserve a
static address first (`gcloud compute addresses create ...`) and attach it.

## 3. Prepare the server

```bash
gcloud compute ssh helios-server --zone=us-central1-a
```

Everything below runs **on the VM**.

**Swap.** An e2-micro has 1 GB of RAM, which isn't enough to build the image and
run Postgres at the same time. Without swap, the build or the tally gets killed.

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Docker** (official Docker apt repository, as in
https://docs.docker.com/engine/install/ubuntu/):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**The code:**

```bash
sudo git clone https://github.com/gjimenexv/helios-server.git /opt/app
```

`/opt/app` is owned by root, so every `git` and `docker` command below runs
with `sudo`.

## 4. Configure: `/opt/app/.env`

Generate the secrets first. Use hex: the database password goes inside a URL,
and symbols would break it.

```bash
openssl rand -hex 32   # SECRET_KEY
openssl rand -hex 32   # EMAIL_OPTOUT_SECRET
openssl rand -hex 24   # POSTGRES_PASSWORD (use the same value in DATABASE_URL)
```

Create the file with `sudo nano /opt/app/.env`, replacing `<IP>` and every
`<...>`:

```ini
DEBUG=0
SECRET_KEY=<hex>
EMAIL_OPTOUT_SECRET=<hex>
ALLOWED_HOSTS=<IP>

POSTGRES_DB=helios
POSTGRES_USER=helios
POSTGRES_PASSWORD=<hex>
DATABASE_URL=postgres://helios:<same hex>@db:5432/helios
DATABASE_SSL_REQUIRE=0

CELERY_BROKER_URL=redis://broker:6379/0

URL_HOST=http://<IP>:80
SECURE_URL_HOST=http://<IP>:80
SSL=0

EMAIL_USE_CONSOLE=0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=<sender>@gmail.com
EMAIL_HOST_PASSWORD=<16-character app password, no spaces>
DEFAULT_FROM_EMAIL=<sender>@gmail.com
DEFAULT_FROM_NAME=<Name voters see, e.g. Espacio Seguro ECS 2026>

# Recommended (the 2026 install left these at their defaults):
AUTH_ENABLED_SYSTEMS=password
ELECTION_TIME_ZONE=America/Costa_Rica
```

```bash
sudo chmod 600 /opt/app/.env
```

Notes:

- `DEBUG=0` is mandatory. With `DEBUG=1`, anyone can log in as anyone via the
  development login.
- `EMAIL_HOST_USER` and `DEFAULT_FROM_EMAIL` **must be the same Gmail
  account**. Otherwise Gmail rewrites the sender.
- `AUTH_ENABLED_SYSTEMS=password` hides the Google, Facebook and LDAP buttons,
  which aren't configured anyway. Voters don't use these: they sign in with
  their per-election voter credentials (see `docs/credenciales-de-votante.md`).
- Other optional settings (`SITE_TITLE`, `WELCOME_MESSAGE`, `HELP_EMAIL_ADDRESS`,
  `HELIOS_VOTER_TOKEN_EXPIRY_HOURS`, ...) are listed in `settings.py`; look for
  `get_from_env`.

## 5. Start it

```bash
cd /opt/app
sudo docker compose up -d --build          # first build is slow on an e2-micro; let it finish
sudo docker compose exec web python manage.py migrate
sudo docker compose ps                      # all four services "Up"; db and broker "healthy"
```

Create the administrator account, which is the one that creates elections:

```bash
sudo docker compose exec web python manage.py shell -c \
  "from helios_auth.auth_systems.password import create_user; create_user('admin', '<long password>', '<Admin name>')"
```

Log in at `http://<IP>/auth/password/login`.

> The admin password is stored **in plain text** in the `helios_auth_user` table
> (upstream Helios behavior). Use a password that isn't used anywhere else, and
> treat database backups as secret.

## 6. Smoke test before the real election

Do all of this with a **test election** and two or three voters whose inboxes
you can read:

1. `http://<IP>/` loads and `http://<IP>/static/helios/css/civic.css` returns 200.
2. Create an election, add a question, and generate the trustee key
   (keep the trustee's secret key file safe; you need it to decrypt).
3. Upload a small voter CSV and confirm the worker processes it:
   `sudo docker compose logs --tail=50 worker`.
4. Freeze the election and email the voters. Check that the mail arrives and
   that the link in it works.
5. Cast a vote, end voting, compute the tally, decrypt as trustee, release results.

Then delete the test election (or leave it; it's harmless) and set up the real one.

## 7. During the election

- **Logs:** `cd /opt/app && sudo docker compose logs -f --tail=100 web worker`
- **Restart a stuck service:** `sudo docker compose restart worker`
- **Take a backup before sending the voter emails and right after voting
  closes** (section 9). It takes seconds.
- Don't stop the VM (the IP could change, see section 2).

## 8. Deploying a code change

From your own machine, with the change merged to `master` on GitHub:

```bash
gcloud compute ssh helios-server --zone=us-central1-a --command \
  "sudo git -C /opt/app pull --ff-only origin master && cd /opt/app && sudo docker compose up -d --build web worker"
```

Or use `deploy-production.sh` at the repo root, which does the same with a dry
run first and checks the site afterwards (it logs in with the SSH key that
`gcloud compute ssh` created):

```bash
HOST=<IP> bash deploy-production.sh          # dry run
HOST=<IP> bash deploy-production.sh --go     # deploy
```

If the change includes a migration, also run
`sudo docker compose exec web python manage.py migrate`. Expect about 30 seconds
of downtime. Tell voters to hard-reload (Cmd/Ctrl-Shift-R) if the booth looks
wrong.

## 9. Backup and restore

**Backup:** run from your machine. It writes a compressed custom-format dump
and a plain SQL copy, then downloads them:

```bash
DEST=~/helios-backups/$(date +%F); mkdir -p $DEST
gcloud compute ssh helios-server --zone=us-central1-a --command '
  cd /opt/app
  sudo docker compose exec -T db sh -c "pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB -Fc" > /tmp/helios.dump
  sudo docker compose exec -T db sh -c "pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB --no-owner" | gzip > /tmp/helios.sql.gz'
gcloud compute scp --zone=us-central1-a \
  helios-server:/tmp/helios.dump helios-server:/tmp/helios.sql.gz $DEST/
chmod 600 $DEST/*; (cd $DEST && shasum -a 256 * > SHA256SUMS)
```

The backup contains every election, the voter roll (names and emails), the
encrypted ballots, the tallies, and the admin password (plain text). Keep it
somewhere private and keep a second copy. **Never commit it to git.**

**Check that a backup restores** before you rely on it. Load it into a
throwaway database and compare counts with the live site:

```bash
cd /opt/app; C=$(sudo docker compose ps -q db)
sudo docker cp /tmp/helios.dump $C:/tmp/helios.dump
sudo docker compose exec -T db sh -c '
  createdb -U $POSTGRES_USER restore_test
  pg_restore -U $POSTGRES_USER -d restore_test --no-owner /tmp/helios.dump
  psql -U $POSTGRES_USER -d restore_test -c "select short_name, (select count(*) from helios_voter v where v.election_id=e.id) voters from helios_election e;"
  dropdb -U $POSTGRES_USER restore_test'
```

**Restore onto a new install:** do sections 1–4, then instead of section 5:

```bash
cd /opt/app
sudo docker compose up -d db                  # database only, empty
C=$(sudo docker compose ps -q db)
sudo docker cp helios.dump $C:/tmp/helios.dump   # after gcloud compute scp-ing it to the VM
sudo docker compose exec -T db sh -c 'pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --no-owner /tmp/helios.dump'
sudo docker compose up -d --build
sudo docker compose exec web python manage.py migrate   # applies only migrations newer than the backup
```

The restore doesn't need the old `.env`. Voter passwords are stored as
salted hashes and don't depend on `SECRET_KEY`, so a fresh `.env` works. If the
IP changed, the links in voter emails already sent will point to the old
address.

## 10. Teardown after the election

1. Make sure results are **released** in the UI (or at least tallied and
   decrypted) and that everyone who needs the result page has seen it.
2. Take a final backup (section 9) and verify it restores.
3. Delete the resources:

```bash
gcloud compute instances delete helios-server --zone=us-central1-a --delete-disks=all
gcloud compute firewall-rules delete allow-web
gcloud compute instances list; gcloud compute disks list; gcloud compute addresses list   # all empty
```

This destroys the database and the `.env`. It can't be undone; the backup is
all that remains. You can keep the (now empty) project for the next election, or
delete it: `gcloud projects delete <id>`.

If you later SSH to a new VM that got the same IP, remove the stale host key:
`ssh-keygen -R <IP>`.

## Known limitations of this setup

- **HTTP only, no TLS.** Ballots are encrypted in the browser before they're
  sent, so vote secrecy doesn't depend on TLS. But voter passwords, the admin
  password and session cookies cross the network in clear, and nothing proves
  to voters that the booth code they received is genuine. For the next election,
  consider pointing a domain at the VM and putting a TLS reverse proxy (such as
  Caddy) in front of `web`. Then set `SSL=1` and change `URL_HOST`,
  `SECURE_URL_HOST` and `ALLOWED_HOSTS` to the `https://` domain.
- **One small VM, no redundancy.** Fine for a roll of a few hundred voters. For
  thousands, use a bigger machine type.
- The Gmail sending limit (about 500/day) caps how many voters you can email per day.

## History

| Election | Installed | Torn down | Backup |
|---|---|---|---|
| ECS 2026 (`Elecciones2026`, 104 voters, 70 ballots) | 2026-08-14 | 2026-09-16 | Held privately by the repo owner (`pg_dump` custom + SQL, verified by test restore) |
