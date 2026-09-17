# Instalar Helios en Google Cloud para una elección

Este es el procedimiento que se usó en la elección ECS 2026 (agosto–septiembre
de 2026). Si lo sigue de principio a fin, obtendrá la misma instalación: una
máquina virtual pequeña de Google Compute Engine que ejecuta toda la aplicación
con Docker Compose. Cuando termine la elección, haga una copia de seguridad y
elimine la instalación (secciones 9 y 10).

Cuente con una hora para la primera instalación. La mayor parte es esperar a
que la máquina construya la imagen de Docker.

## Qué se obtiene

```
                 Internet  ──  http://<IP externa de la VM>/   (puerto 80)
                                   │
 VM de GCE "helios-server"  (e2-micro, Ubuntu 24.04, disco de 30 GB, 2 GB de swap)
 └── /opt/app  (copia de este repositorio + .env)
     └── docker compose
         ├── web     gunicorn, aplicación Django     → puerto 80 del host
         ├── worker  celery (correos, padrones CSV, escrutinios)
         ├── db      postgres:16, datos en el volumen app_pgdata
         └── broker  redis:7 (solo en memoria)
```

Los servicios salen de `docker-compose.yml` y `Dockerfile`, en la raíz del
repositorio. No se usa nada más: ni Cloud SQL, ni balanceador de carga, ni
buckets.

**Costo:** una `e2-micro` con disco estándar de 30 GB en `us-central1`,
`us-west1` o `us-east1` entra en el nivel Always Free de GCP. La dirección IPv4
externa se cobra aparte, unos pocos dólares al mes. Si elimina todo al terminar
(sección 10), el cobro se detiene.

## 0. Antes de empezar

Necesita:

- Una cuenta de Google con facturación habilitada en Google Cloud.
- La [CLI `gcloud`](https://cloud.google.com/sdk/docs/install) con sesión
  iniciada: `gcloud auth login`.
- Una **cuenta de Gmail desde la que se enviarán los correos de la elección**,
  con la verificación en dos pasos activada y una **contraseña de aplicación**
  creada (Cuenta de Google → Seguridad → Contraseñas de aplicaciones). Los
  votantes verán esta dirección, así que use la cuenta de la organización, no
  una personal. Gmail permite unos 500 mensajes al día, suficiente para un
  padrón de unos cientos de votantes.
- El padrón de votantes de la elección en CSV (se sube después, desde la
  interfaz web).

## 1. Crear el proyecto

```bash
PROJECT=helios-server-deploy        # cualquier id único a nivel global
gcloud projects create $PROJECT --name="Helios Server"
gcloud config set project $PROJECT
# vincular la facturación: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT
gcloud services enable compute.googleapis.com
```

Si el proyecto ya existe de una elección anterior, basta con
`gcloud config set project <id>` y continuar.

## 2. Crear la VM y abrir el firewall

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

gcloud compute instances list      # anote la EXTERNAL_IP
```

La IP externa es **efímera**: se mantiene al reiniciar, pero puede cambiar si la
VM se detiene y se vuelve a encender. Todos los enlaces de los correos a los
votantes se construyen con ella, así que no detenga la VM durante una elección.
Si cree que podría necesitar hacerlo, reserve antes una dirección estática
(`gcloud compute addresses create ...`) y asígnela a la VM.

## 3. Preparar el servidor

```bash
gcloud compute ssh helios-server --zone=us-central1-a
```

Todo lo que sigue se ejecuta **en la VM**.

**Swap.** Una e2-micro tiene 1 GB de RAM, que no alcanza para construir la
imagen y ejecutar Postgres a la vez. Sin swap, el sistema mata la construcción
o el escrutinio.

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Docker** (repositorio apt oficial de Docker, según
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

**El código:**

```bash
sudo git clone https://github.com/gjimenexv/helios-server.git /opt/app
```

`/opt/app` pertenece a root, por eso todos los comandos `git` y `docker` que
siguen llevan `sudo`.

## 4. Configurar: `/opt/app/.env`

Primero genere los secretos. Use hexadecimal: la contraseña de la base de datos
va dentro de una URL y los símbolos la romperían.

```bash
openssl rand -hex 32   # SECRET_KEY
openssl rand -hex 32   # EMAIL_OPTOUT_SECRET
openssl rand -hex 24   # POSTGRES_PASSWORD (el mismo valor va en DATABASE_URL)
```

Cree el archivo con `sudo nano /opt/app/.env` y reemplace `<IP>` y cada `<...>`:

```ini
DEBUG=0
SECRET_KEY=<hex>
EMAIL_OPTOUT_SECRET=<hex>
ALLOWED_HOSTS=<IP>

POSTGRES_DB=helios
POSTGRES_USER=helios
POSTGRES_PASSWORD=<hex>
DATABASE_URL=postgres://helios:<el mismo hex>@db:5432/helios
DATABASE_SSL_REQUIRE=0

CELERY_BROKER_URL=redis://broker:6379/0

URL_HOST=http://<IP>:80
SECURE_URL_HOST=http://<IP>:80
SSL=0

EMAIL_USE_CONSOLE=0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=<remitente>@gmail.com
EMAIL_HOST_PASSWORD=<contraseña de aplicación de 16 caracteres, sin espacios>
DEFAULT_FROM_EMAIL=<remitente>@gmail.com
DEFAULT_FROM_NAME=<Nombre que ven los votantes, p. ej. Espacio Seguro ECS 2026>

# Recomendado (la instalación de 2026 los dejó con su valor por defecto):
AUTH_ENABLED_SYSTEMS=password
ELECTION_TIME_ZONE=America/Costa_Rica
```

```bash
sudo chmod 600 /opt/app/.env
```

Notas:

- `DEBUG=0` es obligatorio. Con `DEBUG=1`, cualquiera puede entrar como
  cualquier usuario mediante el inicio de sesión de desarrollo.
- `EMAIL_HOST_USER` y `DEFAULT_FROM_EMAIL` **deben ser la misma cuenta de
  Gmail**. Si no, Gmail reescribe el remitente.
- `AUTH_ENABLED_SYSTEMS=password` oculta los botones de Google, Facebook y LDAP,
  que de todos modos no están configurados. Los votantes no los usan: entran con
  sus credenciales de votante de cada elección (ver
  `docs/credenciales-de-votante.md`).
- Los demás ajustes opcionales (`SITE_TITLE`, `WELCOME_MESSAGE`,
  `HELP_EMAIL_ADDRESS`, `HELIOS_VOTER_TOKEN_EXPIRY_HOURS`, ...) están en
  `settings.py`; busque `get_from_env`.

## 5. Arrancar

```bash
cd /opt/app
sudo docker compose up -d --build          # la primera construcción es lenta en una e2-micro; déjela terminar
sudo docker compose exec web python manage.py migrate
sudo docker compose ps                      # los cuatro servicios "Up"; db y broker "healthy"
```

Cree la cuenta de administración, que es la que crea las elecciones:

```bash
sudo docker compose exec web python manage.py shell -c \
  "from helios_auth.auth_systems.password import create_user; create_user('admin', '<contraseña larga>', '<Nombre del administrador>')"
```

Inicie sesión en `http://<IP>/auth/password/login`.

> La contraseña de administración se guarda **en texto plano** en la tabla
> `helios_auth_user` (así funciona Helios original). Use una contraseña que no
> se use en ningún otro sitio y trate las copias de seguridad como secretas.

## 6. Prueba antes de la elección real

Haga todo esto con una **elección de prueba** y dos o tres votantes cuyos
correos pueda leer:

1. `http://<IP>/` carga y `http://<IP>/static/helios/css/civic.css` responde 200.
2. Cree una elección, agregue una pregunta y genere la clave del fiduciario
   (guarde bien el archivo con la clave secreta del fiduciario: sin él no se
   puede descifrar).
3. Suba un padrón CSV pequeño y confirme que el worker lo procesa:
   `sudo docker compose logs --tail=50 worker`.
4. Congele la papeleta y envíe el correo a los votantes. Compruebe que el
   correo llega y que su enlace funciona.
5. Emita un voto, cierre la votación, calcule el escrutinio cifrado, descifre
   como fiduciario y publique el resultado.

Después borre la elección de prueba (o déjela; no molesta) y configure la real.

## 7. Durante la elección

- **Registros:** `cd /opt/app && sudo docker compose logs -f --tail=100 web worker`
- **Reiniciar un servicio atascado:** `sudo docker compose restart worker`
- **Haga una copia de seguridad antes de enviar los correos a los votantes y
  justo después de cerrar la votación** (sección 9). Toma segundos.
- No detenga la VM (la IP podría cambiar; ver sección 2).

## 8. Desplegar un cambio de código

Desde su propia computadora, con el cambio ya integrado en `master` en GitHub:

```bash
gcloud compute ssh helios-server --zone=us-central1-a --command \
  "sudo git -C /opt/app pull --ff-only origin master && cd /opt/app && sudo docker compose up -d --build web worker"
```

O use `deploy-production.sh`, en la raíz del repositorio. Hace lo mismo, con un
ensayo previo que no cambia nada, y al final comprueba que el sitio responde.
Entra con la clave SSH que creó `gcloud compute ssh`:

```bash
HOST=<IP> bash deploy-production.sh          # ensayo, no cambia nada
HOST=<IP> bash deploy-production.sh --go     # desplegar
```

Si el cambio incluye una migración, ejecute también
`sudo docker compose exec web python manage.py migrate`. Cuente con unos 30
segundos sin servicio. Si la cabina de votación se ve mal, pida a los votantes
que recarguen sin caché (Cmd/Ctrl-Shift-R).

## 9. Copia de seguridad y restauración

**Copia de seguridad:** se ejecuta desde su computadora. Genera un volcado
comprimido en formato personalizado y una copia en SQL plano, y los descarga:

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

La copia contiene todas las elecciones, el padrón (nombres y correos), las
papeletas cifradas, los escrutinios y la contraseña de administración (en texto
plano). Guárdela en un lugar privado y mantenga una segunda copia. **Nunca la
suba a git.**

**Compruebe que la copia se puede restaurar** antes de confiar en ella.
Cárguela en una base de datos desechable y compare los conteos con el sitio en
vivo:

```bash
cd /opt/app; C=$(sudo docker compose ps -q db)
sudo docker cp /tmp/helios.dump $C:/tmp/helios.dump
sudo docker compose exec -T db sh -c '
  createdb -U $POSTGRES_USER restore_test
  pg_restore -U $POSTGRES_USER -d restore_test --no-owner /tmp/helios.dump
  psql -U $POSTGRES_USER -d restore_test -c "select short_name, (select count(*) from helios_voter v where v.election_id=e.id) voters from helios_election e;"
  dropdb -U $POSTGRES_USER restore_test'
```

**Restaurar en una instalación nueva:** siga las secciones 1–4 y, en lugar de
la sección 5:

```bash
cd /opt/app
sudo docker compose up -d db                  # solo la base de datos, vacía
C=$(sudo docker compose ps -q db)
sudo docker cp helios.dump $C:/tmp/helios.dump   # después de copiarla a la VM con gcloud compute scp
sudo docker compose exec -T db sh -c 'pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --no-owner /tmp/helios.dump'
sudo docker compose up -d --build
sudo docker compose exec web python manage.py migrate   # aplica solo las migraciones posteriores a la copia
```

La restauración no necesita el `.env` anterior. Las contraseñas de los votantes
se guardan como hashes con sal y no dependen de `SECRET_KEY`, así que un `.env`
nuevo funciona. Si la IP cambió, los enlaces de los correos ya enviados
apuntarán a la dirección vieja.

## 10. Eliminar la instalación después de la elección

1. Asegúrese de que el resultado esté **publicado** en la interfaz (o al menos
   escrutado y descifrado) y de que todas las personas que necesitan la página
   de resultados ya la vieron.
2. Haga una copia de seguridad final (sección 9) y compruebe que se restaura.
3. Elimine los recursos:

```bash
gcloud compute instances delete helios-server --zone=us-central1-a --delete-disks=all
gcloud compute firewall-rules delete allow-web
gcloud compute instances list; gcloud compute disks list; gcloud compute addresses list   # todo vacío
```

Esto destruye la base de datos y el `.env`. No se puede deshacer: solo queda la
copia de seguridad. Puede conservar el proyecto (ya vacío) para la próxima
elección o borrarlo: `gcloud projects delete <id>`.

Si más adelante entra por SSH a una VM nueva que recibió la misma IP, borre la
clave de host vieja: `ssh-keygen -R <IP>`.

## Limitaciones conocidas de esta instalación

- **Solo HTTP, sin TLS.** Las papeletas se cifran en el navegador antes de
  enviarse, así que el secreto del voto no depende de TLS. Pero las contraseñas
  de los votantes, la de administración y las cookies de sesión viajan sin
  cifrar, y nada le garantiza al votante que el código de la cabina que recibió
  es el auténtico. Para la próxima elección, considere apuntar un dominio a la
  VM y poner delante de `web` un proxy inverso con TLS (por ejemplo, Caddy).
  Luego ponga `SSL=1` y cambie `URL_HOST`, `SECURE_URL_HOST` y `ALLOWED_HOSTS`
  al dominio `https://`.
- **Una sola VM pequeña, sin redundancia.** Suficiente para un padrón de unos
  cientos de votantes. Para miles, use un tipo de máquina más grande.
- El límite de envío de Gmail (unos 500 al día) limita a cuántos votantes se
  puede escribir por día.

## Historial

| Elección | Instalada | Eliminada | Copia de seguridad |
|---|---|---|---|
| ECS 2026 (`Elecciones2026`, 104 votantes, 70 papeletas) | 2026-08-14 | 2026-09-16 | En poder del dueño del repositorio (`pg_dump` personalizado + SQL, verificada con una restauración de prueba) |
