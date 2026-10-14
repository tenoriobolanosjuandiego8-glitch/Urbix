# URBIX — Movilidad Inteligente en Popayán

Backend Django + frontend HTML/CSS/JS (reutilizado como templates de Django),
mapa con Leaflet + OpenStreetMap, API REST con Django REST Framework.

## 1. Requisitos

- Python 3.11+
- pip

## 2. Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env          # y ajusta los valores si lo necesitas

# 4. Migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Datos iniciales (rutas, buses, restaurantes, hoteles, eventos, usuarios demo)
python manage.py seed_data

# 6. Ejecutar
python manage.py runserver
```

Abre http://127.0.0.1:8000/

## Despliegue en Render

El archivo `render.yaml` configura un servicio web Django y una base de datos
PostgreSQL. Para desplegarlo, en Render selecciona **New > Blueprint**, conecta
este repositorio y confirma los recursos declarados. Render instalará las
dependencias, recopilará los archivos estáticos y ejecutará las migraciones.

Render genera `DJANGO_SECRET_KEY` y conecta `DATABASE_URL` automáticamente.
Para cargar los datos iniciales de demostración, ejecuta una vez
`python manage.py seed_data` desde el Shell del servicio.

Los archivos subidos por usuarios se guardan en el disco efímero del servicio;
para conservarlos entre despliegues, configura almacenamiento externo antes de
usar cargas de imágenes en producción.

## 3. Usuarios de prueba (creados por `seed_data`)

| Rol           | Correo               | Contraseña       |
|---------------|-----------------------|------------------|
| Administrador | admin@urbix.co        | admin12345       |
| Usuario       | usuario@urbix.co      | usuario12345     |
| Conductor     | conductor@urbix.co    | conductor12345   |

Panel de administración de Django: http://127.0.0.1:8000/admin/

## 4. Simular movimiento de buses (GPS)

Mientras no haya hardware GPS real conectado, puedes simular el movimiento
de los buses en su ruta:

```bash
python manage.py simulate_gps --interval 5
```

Esto actualiza la posición de cada bus cada 5 segundos; el mapa (`/mapa/`)
consulta `map:data` cada 4 segundos y se actualiza solo.

## 5. Estructura del proyecto

```
urbix/
├── manage.py
├── requirements.txt
├── .env.example
├── config/            # settings, urls raíz, wsgi/asgi
├── accounts/          # usuarios, roles, conductores, autenticación
├── buses/             # flota de buses
├── routes/             # rutas, paraderos, horarios
├── gps/                # ubicaciones GPS (real y simulado)
├── map/                # vista del mapa + endpoint JSON
├── restaurants/        # restaurantes (CRUD)
├── hotels/              # hoteles (CRUD)
├── tourism/             # lugares turísticos (CRUD)
├── events/              # eventos (CRUD)
├── notifications/       # sistema de notificaciones
├── reports/              # reportes de conductores, vueltas
├── interactions/         # favoritos, comentarios, calificaciones, historial (genéricos)
├── dashboard/             # paneles usuario/conductor/admin, splash, seed_data
├── api/                    # API REST (Django REST Framework)
├── templates/               # base.html, partials (sidebar/navbar/footer), templates por app
├── static/                   # css, js, imágenes (reutilizados del frontend original)
└── media/                     # archivos subidos (fotos, imágenes de contenido)
```

## 6. Base de datos

- **Desarrollo**: SQLite (`db.sqlite3`), cero configuración.
- **Producción**: PostgreSQL. En tu `.env`:

```
DJANGO_DB_ENGINE=postgres
DJANGO_DB_NAME=urbix
DJANGO_DB_USER=urbix
DJANGO_DB_PASSWORD=tu_password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=5432
```

y añade `psycopg2-binary` a `requirements.txt` (ya está listado, solo
descomenta la línea).

## 7. Roles y permisos

Cada usuario tiene un `role`: `usuario`, `conductor` o `administrador`.
El sidebar y las vistas cambian según el rol (`accounts/decorators.py`:
`admin_required`, `driver_required`, `user_required`). El superusuario de
Django (`is_superuser`) tiene acceso administrativo aunque su `role` sea
distinto.

## 8. API REST (para una futura app móvil)

Base: `/api/v1/`

- `POST /api/v1/auth/token/` — login, retorna token
- `GET /api/v1/rutas/`, `/api/v1/buses/`, `/api/v1/restaurantes/`,
  `/api/v1/hoteles/`, `/api/v1/turismo/`, `/api/v1/eventos/`
- `GET/POST /api/v1/favoritos/`, `/api/v1/comentarios/`
- `GET/POST /api/v1/gps/` (conductor autenticado publica su posición)
- `GET /api/v1/mapa/` — foto completa del mapa (rutas + buses)

Autenticación por token: header `Authorization: Token <token>`.

## 9. Seguridad implementada

- CSRF (middleware + `{% csrf_token %}` en todos los formularios)
- XSS: autoescape de templates de Django (activo por defecto)
- SQL Injection: se usa exclusivamente el ORM de Django
- Contraseñas: hash con PBKDF2 (Django por defecto)
- Variables de entorno para secretos (`.env`, nunca subir a git)
- Registro de errores (`logs/errors.log`) y de actividad (`logs/activity.log`,
  además de la tabla `ActivityLog` para acciones que modifican datos)
- Cabeceras de seguridad activas automáticamente cuando `DEBUG=False`
  (HSTS, cookies seguras, `X-Frame-Options`, etc.)

## 11. Asistente IA (chatbot + búsqueda inteligente + recomendaciones)

URBIX incluye 3 funciones de inteligencia artificial en la app `assistant/`:

1. **Chatbot** — botón flotante (abajo a la derecha) visible para usuarios
   con sesión iniciada. Responde preguntas sobre rutas, restaurantes,
   hoteles, turismo y eventos usando los datos reales de tu base de datos.
2. **Buscador inteligente** — en `/asistente/buscar/` (o la barra de
   búsqueda del navbar). Escribes una frase natural como *"algo económico
   para comer cerca del centro"* y la IA la interpreta y busca en la BD.
3. **Recomendaciones personalizadas** — sección "Recomendado para ti" en
   la pantalla de inicio. Esta NO usa IA (no tiene costo): se basa en las
   categorías de tus favoritos guardados.

### Activar el chatbot y el buscador

1. Crea una cuenta gratuita en https://console.anthropic.com
2. Genera una API key en https://console.anthropic.com/settings/keys
3. Pégala en tu archivo `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
   ```
4. Instala la librería (ya está en `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```
5. Reinicia el servidor (`Ctrl+C` y `python manage.py runserver` de nuevo).

Si no configuras la clave, el chatbot y el buscador simplemente muestran
un mensaje explicando que falta activarlos — el resto de la app sigue
funcionando normal.

**Costo:** la API de Anthropic cobra por uso (no es gratis ilimitado),
pero el modelo usado (`claude-sonnet-4-5`) es económico para este volumen
de uso. Revisa precios actuales en https://www.anthropic.com/pricing

## 13. Datos reales de transporte de Popayán

`seed_data` ahora crea las **4 empresas reales** de transporte urbano de
Popayán con sus rutas reales (barrios y sectores que cubren, según
información pública): **Transpubenza** (9 rutas), **Translibertad**
(6 rutas), **Sotracauca** (5 rutas) y **Transtambo** (4 rutas) — 24 rutas
en total, cada una con su color propio en el mapa.

**Aviso importante:** las coordenadas de los barrios son *aproximadas*
(ubicadas a criterio alrededor del centro de Popayán para que el mapa
se vea bien), no son coordenadas GPS exactas. Para producción real,
corrígelas una por una desde `/admin/` → Paraderos y lugares.

### Buscador "¿qué bus pasa por aquí?"

En `/rutas/paraderos/` cualquier usuario puede buscar un barrio,
universidad, hospital, parque, etc. y ver qué rutas (de qué empresa)
pasan cerca — útil para decidir qué bus tomar.

### Que los buses sigan las calles reales (como Uber/inDriver)

Por defecto, el mapa dibuja líneas rectas entre paraderos. Para que
sigan el trazado real de las calles:

1. Crea una cuenta gratis (sin tarjeta) en https://openrouteservice.org/dev/#/signup
2. Copia tu API key y agrégala a `.env`:
   ```
   OPENROUTESERVICE_API_KEY=tu-clave-aqui
   ```
3. Corre:
   ```bash
   python manage.py snap_routes_to_streets
   ```
Esto calcula el recorrido real de cada ruta y lo guarda; el mapa lo usa
automáticamente a partir de ahí. Si no lo activas, la app sigue
funcionando normal con líneas rectas.

**Nota sobre Google Maps:** decidimos NO usar la API de Directions de
Google porque exige tarjeta de crédito y cobra pasado el límite
gratuito. OpenRouteService hace lo mismo sin ese requisito.

## 15. Centro Empresarial URBIX

Módulo nuevo para que negocios locales (restaurantes, hoteles, cafeterías,
farmacias, gimnasios, etc.) se registren y aparezcan en la plataforma.

- **Registro** (`/empresas-urbix/registro/`): cualquier usuario logueado
  puede registrar su negocio. Al hacerlo, su rol pasa a `empresa`.
- **Verificación**: todo negocio nuevo queda en estado *"Pendiente de
  verificación"* — no aparece públicamente hasta que un administrador
  lo apruebe desde `/empresas-urbix/admin/`.
- **Planes**: Gratuito, Destacado y Premium (afecta el orden en el
  directorio). Por ahora el administrador asigna el plan manualmente
  desde su panel — no hay cobro real todavía.
- **Pasarelas de pago**: el modelo `Subscription` ya tiene los campos
  para conectar Wompi, Mercado Pago, PayU o Stripe cuando decidas
  cobrar de verdad; hoy solo registra pagos manuales.
- **Panel de la empresa** (`/empresas-urbix/panel/`): visitas, clics,
  apariciones en búsquedas, promociones, reseñas (con respuesta del
  negocio) y calificación promedio.
- **Reseñas**: reutiliza el sistema de comentarios/calificaciones que
  ya existía para restaurantes/hoteles — funciona igual para negocios,
  incluyendo denunciar contenido inapropiado.

## 16. Seguridad reforzada en esta versión

- **Bloqueo por fuerza bruta**: 5 intentos fallidos de login en 15
  minutos bloquean ese correo temporalmente (`accounts.LoginAttempt`).
- **Cabeceras de seguridad HTTP**: Content-Security-Policy,
  Referrer-Policy, Permissions-Policy y X-Content-Type-Options en
  todas las respuestas (`config/security_middleware.py`, sin
  dependencias nuevas).
- **Validación de archivos subidos**: toda imagen (perfil, negocios,
  restaurantes, hoteles, turismo, eventos) se valida por extensión,
  tamaño (máx. 5 MB) y contenido real del archivo — no basta con
  cambiarle la extensión a un archivo malicioso.
- **CSRF corregido**: se eliminó un `csrf_exempt` que combinado con
  sesión autenticada era explotable en el endpoint de reporte de GPS;
  ahora además valida que el conductor solo pueda reportar la posición
  de su propio bus asignado.
- **Falla segura**: si despliegas con `DEBUG=False` y se te olvidó
  configurar `DJANGO_SECRET_KEY`, la app rehúsa arrancar en vez de
  usar la clave de ejemplo insegura.
- **Auditoría**: `ActivityLog` (ya existente) + `LoginAttempt`, ambos
  visibles y buscables desde `/admin/`.

**Nota honesta:** esto es un endurecimiento real pero no un pentest
profesional. Antes de manejar datos de pago reales o usuarios masivos,
te recomiendo una auditoría de seguridad externa.

## 17. Pendiente / próximos pasos

- Tests automatizados más exhaustivos (hay una base en cada app; amplíalos
  según vayas agregando lógica de negocio)
- Notificaciones push reales (el modelo `Notification` ya está listo;
  falta integrar un proveedor como Firebase Cloud Messaging)
- WebSockets/Channels para GPS verdaderamente en tiempo real (hoy se
  actualiza por polling cada 4 segundos, que es más simple y funciona bien
  para un MVP)
- Documentación ampliada (diagramas ER/clases) — el diccionario de datos
  está en los `models.py` de cada app, comentados en español
