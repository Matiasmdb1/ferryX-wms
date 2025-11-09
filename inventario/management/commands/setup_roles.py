# inventario/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

APP = "inventario"  # ⚠️ Si tu app NO se llama "inventario", cámbialo aquí.

ROLES = {
    "Administrador": {"all": True},  # todos los permisos del app 'inventario'

    # Puede crear MPs y registrar movimientos (compras/ajustes/mermas),
    # crear órdenes de producción (consume MP según receta)
    "Abastecedor": {
        # Materias primas / Kardex
        f"{APP}.add_materiaprima",
        f"{APP}.view_materiaprima",
        f"{APP}.add_movimientomp",
        f"{APP}.view_movimientomp",

        # Producción + Recetas (solo ver recetas/productos, crear OP)
        f"{APP}.view_producto",
        f"{APP}.view_receta",
        f"{APP}.add_ordenproduccion",
        f"{APP}.view_ordenproduccion",
    },

    # Solo lectura de inventario y producción
    "Monitor": {
        f"{APP}.view_materiaprima",
        f"{APP}.view_movimientomp",
        f"{APP}.view_producto",
        f"{APP}.view_receta",
        f"{APP}.view_ordenproduccion",
    },

    # Por ahora solo lectura de MP (Ventas llegará en el Módulo 4)
    "Vendedor": {
        f"{APP}.view_materiaprima",
    },
}

class Command(BaseCommand):
    help = "Crea/actualiza grupos y asigna permisos del app de inventario y producción"

    def handle(self, *args, **kwargs):
        for nombre, conf in ROLES.items():
            g, _ = Group.objects.get_or_create(name=nombre)

            if conf == {"all": True}:
                perms = Permission.objects.filter(content_type__app_label=APP)
            else:
                codenames = [p.split(".")[1] for p in conf]
                perms = Permission.objects.filter(
                    content_type__app_label=APP,
                    codename__in=codenames
                )

                # Aviso si faltara algún permiso (p.ej., no corriste migraciones)
                found = set(perms.values_list("codename", flat=True))
                missing = set(codenames) - found
                if missing:
                    self.stdout.write(self.style.WARNING(
                        f"[{nombre}] Permisos no encontrados (¿falta makemigrations/migrate?): {sorted(missing)}"
                    ))

            g.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS("Grupos y permisos configurados."))
