# inventario/migrations/0002_crear_grupos_default.py
# (O el número que te haya tocado)

from django.db import migrations

# Lista de grupos y los permisos que deben tener
# (Usamos los 'codenames' de los permisos)
GRUPOS_Y_PERMISOS = {
    'Gerente': [
        'view_suscripcioncliente',
        'view_sucursal', 'add_sucursal', 'change_sucursal', 'delete_sucursal',
        'view_ubicacion', 'add_ubicacion', 'change_ubicacion', 'delete_ubicacion',
        'view_stockporubicacion', 'add_stockporubicacion', 'change_stockporubicacion', 'delete_stockporubicacion',
        'view_materiaprima', 'add_materiaprima', 'change_materiaprima', 'delete_materiaprima',
        'view_movimientomp', 'add_movimientomp', 'change_movimientomp', 'delete_movimientomp',
        'view_producto', 'add_producto', 'change_producto', 'delete_producto',
        'view_receta', 'add_receta', 'change_receta', 'delete_receta',
        'view_ordenproduccion', 'add_ordenproduccion', 'change_ordenproduccion', 'delete_ordenproduccion',
        'view_loteproducto', 'add_loteproducto', 'change_loteproducto', 'delete_loteproducto',
        'view_venta', 'add_venta', 'change_venta', 'delete_venta',
        'view_user', 'add_user', 'change_user', 'delete_user', # <-- Permiso para invitar equipo
        'can_run_predictions', # <-- Permiso de IA
    ],
    'Bodeguero': [
        'view_sucursal',
        'view_ubicacion',
        'view_stockporubicacion', 'change_stockporubicacion', # Puede ver y AJUSTAR stock
        'view_materiaprima',
        'view_movimientomp', 'add_movimientomp', # Puede hacer ingresos, ajustes, mermas
        'view_producto',
        'view_receta',
        'view_ordenproduccion', 'add_ordenproduccion', 'change_ordenproduccion', # Puede crear y ejecutar OPs
        'view_loteproducto',
    ],
    'Vendedor': [
        'view_sucursal',
        'view_ubicacion',
        'view_stockporubicacion', # Puede ver cuánto stock hay
        'view_producto',
        'view_loteproducto',
        'view_venta', 'add_venta', 'change_venta', # Puede crear y confirmar ventas
    ]
}


def crear_grupos_default(apps, schema_editor):
    # Obtenemos los modelos de la versión "histórica" de Django
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Nos aseguramos de que solo buscamos permisos de nuestra app 'inventario'
    content_types = ContentType.objects.filter(app_label='inventario')
    
    # Obtenemos todos los permisos de la app 'inventario' en un diccionario
    # para búsqueda rápida
    permisos_inventario = Permission.objects.filter(
        content_type__in=content_types
    ).values_list('codename', 'pk')
    
    # Creamos un diccionario { 'codename': permission_id }
    mapa_permisos = dict(permisos_inventario)

    print("\n") # Espacio para legibilidad

    # Iteramos sobre los grupos que definimos arriba
    for nombre_grupo, lista_codenames in GRUPOS_Y_PERMISOS.items():
        
        # Buscamos o creamos el grupo
        grupo, created = Group.objects.get_or_create(name=nombre_grupo)
        
        if created:
            print(f"  Grupo '{nombre_grupo}' CREADO.")
        else:
            print(f"  Grupo '{nombre_grupo}' ya existía, actualizando permisos.")

        # Preparamos la lista de IDs de permisos para este grupo
        permisos_para_grupo = []
        for codename in lista_codenames:
            if codename in mapa_permisos:
                permisos_para_grupo.append(mapa_permisos[codename])
            else:
                # Advertencia si un permiso no se encontró
                print(f"    ¡ADVERTENCIA! El permiso '{codename}' no se encontró y no será asignado.")

        # Asignamos la lista de permisos al grupo
        grupo.permissions.set(permisos_para_grupo)

    print("\nMigración de grupos completada.")


class Migration(migrations.Migration):

    # Le decimos a Django que esta migración debe correr DESPUÉS
    # de la migración inicial que crea las tablas
    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        # Ejecutamos nuestra función
        migrations.RunPython(crear_grupos_default),
    ]