from pathlib import Path
import os
import dj_database_url # <--
from pathlib import Path
from django.urls import reverse_lazy  #
BASE_DIR = Path(__file__).resolve().parent.parent

# === Seguridad ===
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "a_&vg9ba0csscoshc#l7guszc8iqqi)hk6lvp$ct&z9i1)6f*z")
DEBUG = 'RENDER' not in os.environ
#ALLOWED_HOSTS = ["*"]  # en producción usa tu dominio/IP

ALLOWED_HOSTS = []

# 'RENDER' es la variable que Render nos da
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# === Apps instaladas ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inventario",
    'django.contrib.sites',  # Requerido por allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', #
]

# 2. Añade los 'AUTHENTICATION_BACKENDS'
# (Puedes poner esto debajo de INSTALLED_APPS)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# 3. Añade 'SITE_ID = 1'
# (allauth lo requiere, ponlo en cualquier lugar)
SITE_ID = 1


# === Middleware ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    'allauth.account.middleware.AccountMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'inventario.middleware.SetupWizardMiddleware',
]

ROOT_URLCONF = "bigmomma.urls"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Carpeta global de templates
        "APP_DIRS": True,  # También busca dentro de cada app /templates/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.dev",  # permite cualquier subdominio ngrok
]
WSGI_APPLICATION = "bigmomma.wsgi.application"

# === Base de datos ===
DATABASES = {
    'default': dj_database_url.config(
        # Render nos dará una variable "DATABASE_URL"
        # Si no la encuentra (porque estamos en tu PC), 
        # usará tu archivo db.sqlite3 como respaldo.
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# === Validación de contraseñas ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === Idioma y zona horaria ===
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# === Archivos estáticos ===
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "bigmomma" / "static",   # donde tú guardas estilos, js, etc.
]
STATIC_ROOT = BASE_DIR / "staticfiles"  # para producción con collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# === Archivos de usuario (media) ===
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# === Autenticación ===
LOGIN_URL = "login"
# en settings.py
LOGIN_REDIRECT_URL = 'inventario:pagina_precios'  # Después del login, ¿a dónde va?

# Cuando un usuario hace logout, ¿a dónde va?
LOGOUT_REDIRECT_URL = 'inventario:index'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AZURE_DOCINT_ENDPOINT = "https://recetafactura.cognitiveservices.azure.com/"

# Pega aquí tu "Clave 1"
AZURE_DOCINT_KEY = "whxLFWoGjkPWKEUc96PuE7N09xkTzyGM0pwVa0VvHkZc3cFUw9hCJQQJ99BJACZoyfiXJ3w3AAALACOG0GxE"


# BORRA ESTA LÍNEA de settings.py
AUTH_USER_MODEL = 'inventario.User'



# 4. Añade la configuración de ALLAUTH
# (Pon este bloque grande al final de tu settings.py)

# --- CONFIGURACIÓN DE DJANGO-ALLAUTH ---
ACCOUNT_EMAIL_REQUIRED = True         # Pide el email
ACCOUNT_UNIQUE_EMAIL = True           # Fuerza a que el email sea único (¡tu meta!)
ACCOUNT_USERNAME_REQUIRED = False       # No pediremos 'username' en el registro
ACCOUNT_AUTHENTICATION_METHOD = 'email' # El usuario iniciará sesión con email
ACCOUNT_EMAIL_VERIFICATION = 'none'   # 'none' para desarrollo, 'mandatory' para producción
SOCIALACCOUNT_AUTO_SIGNUP = True      # Si el usuario usa Google, se registra automáticamente
LOGIN_REDIRECT_URL = reverse_lazy('inventario:panel') # A dónde va después de login
ACCOUNT_LOGOUT_REDIRECT_URL = reverse_lazy('inventario:index') # A dónde va después de logout
# --- ¡¡AÑADE ESTA LÍNEA!! ---
# Esto omite la molesta página de "confirmación"
SOCIALACCOUNT_LOGIN_ON_GET = True
# --- FIN DE LA LÍNEA ---

# Configuración del proveedor de Google
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # ... (tu client_id y secret) ...
    }
}
# Configuración del proveedor de Google
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            # --- ¡¡AQUÍ PEGAS TUS LLAVES!! ---
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', '503890582377-n73ug6gtnrj8jqs1ikfefcnvsisfhi63.apps.googleusercontent.com'),
            'secret': os.environ.get('GOOGLE_SECRET', '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'),
        },
        'SCOPE': [ # Lo que le pedimos a Google
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}