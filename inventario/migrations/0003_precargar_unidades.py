# inventario/migrations/0003_precargar_unidades.py
# (O el número que te haya tocado)

from django.db import migrations

# Lista de unidades que queremos crear
UNIDADES_DEFAULT = [
    'Unidad (un)',
    'Kilos (kg)',
    'Gramos (g)',
    'Litros (lt)',
    'Mililitros (ml)',
]

def precargar_unidades(apps, schema_editor):
    """
    Esta función crea las Unidades de Medida básicas
    en la base de datos.
    """
    # Obtenemos el modelo 'UnidadMedida' de la app 'inventario'
    # Es importante usar apps.get_model() en las migraciones
    UnidadMedida = apps.get_model('inventario', 'UnidadMedida')
    
    print("\n") # Espacio para legibilidad
    print("  Precargando Unidades de Medida...")
    
    unidades_creadas = 0
    for nombre_unidad in UNIDADES_DEFAULT:
        # Usamos get_or_create para no duplicar si ya existen
        obj, created = UnidadMedida.objects.get_or_create(nombre=nombre_unidad)
        if created:
            unidades_creadas += 1
    
    print(f"  ... {unidades_creadas} nuevas unidades creadas.")

class Migration(migrations.Migration):

    # Esta migración debe correr DESPUÉS de la que crea los grupos
    dependencies = [
        ('inventario', '0002_crear_grupos_default'), 
        # (Si tu migración de grupos tiene otro número, ajústalo aquí)
    ]

    operations = [
        # Ejecutamos nuestra función 'precargar_unidades'
        migrations.RunPython(precargar_unidades),
    ]