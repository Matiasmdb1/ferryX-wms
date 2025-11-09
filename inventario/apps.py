from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'


# inventario/apps.py
from django.apps import AppConfig

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'

    # --- ¡¡AÑADE ESTA FUNCIÓN!! ---
    def ready(self):
        # Esto le dice a Django que cargue el archivo signals.py
        import inventario.signals