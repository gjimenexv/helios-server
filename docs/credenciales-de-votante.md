# Credenciales de votante: nadie puede ver la contraseña de nadie

Este documento describe cómo Helios (esta instalación) entrega credenciales a los
votantes de tipo `password`, y qué garantiza y qué no garantiza ese diseño.

## El problema que resuelve

Hasta ahora, Helios generaba una contraseña por votante, la guardaba **en claro**
en la base de datos y la enviaba en el cuerpo del correo. Eso dejaba copias
legibles de cada credencial en, al menos, cuatro sitios: la tabla `helios_voter`,
cualquier copia de seguridad de la base de datos, la carpeta "Enviados" del buzón
remitente y los registros del proveedor de correo. Cualquiera con acceso a uno de
esos sitios podía suplantar a cualquier votante, y esa posibilidad debilita la
afirmación de que el voto lo emitió la persona correcta.

## El flujo actual

1. Al cargar el padrón, el votante se crea **sin credencial alguna**.
2. Al enviarle correo, el servidor emite un **token de un solo uso** de 256 bits.
   Guarda únicamente su SHA-256 (`Voter.login_token_hash`) y envía el token en un
   enlace personal. Ese instante es el único en que el token existe fuera del
   buzón del votante.
3. El votante abre el enlace y **elige su propia contraseña**. Se guarda solo su
   hash (`Voter.voter_password_hash`, con el hasher de Django). El token se
   consume: su hash se borra y se registra `login_token_used_at`.
4. A partir de ahí el votante entra con su ID y su contraseña. El servidor no
   puede leerla, solo comprobarla.
5. Si la olvida, el sistema **no puede reenviársela**. Pide un enlace nuevo, que
   invalida el anterior; hasta que lo use, su contraseña actual sigue sirviendo.

Un votante que ya eligió contraseña no recibe enlaces nuevos en los correos
posteriores: solo se le recuerda cómo pedir uno.

## Parámetros

| Ajuste | Por defecto | Qué hace |
|---|---|---|
| `HELIOS_VOTER_TOKEN_EXPIRY_HOURS` | `336` (14 días) | Caducidad del enlace de un solo uso |
| `HELIOS_VOTER_PASSWORD_MIN_LENGTH` | `8` | Longitud mínima de la contraseña elegida |

## Qué garantiza

- Ninguna contraseña de votante existe en claro en la base de datos, en las copias
  de seguridad, en los correos enviados ni en los registros del proveedor de correo.
- El administrador de la elección nunca conoce la contraseña de ningún votante.
- Una copia del correo que quede en la bandeja de salida deja de ser útil en
  cuanto el votante usa su enlace, o cuando este caduca.
- Un uso indebido del enlace deja rastro: el votante legítimo encuentra su enlace
  ya consumido.

## Qué NO garantiza

- **Un operador con acceso a la base de datos puede emitir un enlace nuevo** hacia
  un correo que controle. El hashing no protege contra eso; protegen la
  verificabilidad de Helios (el votante detecta un rastreador de voto que no
  emitió), el registro de auditoría y la separación de funciones entre quien
  administra la elección y quien administra el servidor.
- **El token viaja en la ruta de la URL**, así que aparece en el historial del
  navegador del votante y puede aparecer en los registros de acceso del servidor
  web hasta que se consume. Si ese registro es una preocupación, configure el
  servidor para no registrar la ruta de `/setup-credentials/`.
- La seguridad del buzón del votante sigue siendo un supuesto: quien lea su correo
  antes que él puede fijar la contraseña en su lugar.

## Nota sobre las cuentas de administrador

Este cambio cubre las credenciales de **votante**. El sistema de autenticación por
contraseña de `helios_auth` (usuarios administradores) todavía guarda la contraseña
en claro en `User.info['password']` (ver `helios_auth/auth_systems/password.py`) y
la reenvía por correo en el flujo de "contraseña olvidada". Si su despliegue usa
ese sistema de autenticación, conviene aplicarle el mismo tratamiento.
