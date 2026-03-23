SECRET_KEY = "test"
DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
INSTALLED_APPS = ["library"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MIGRATION_MODULES = {"library": None}
ROOT_URLCONF = "library.urls"
