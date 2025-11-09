from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from .models import SuscripcionCliente
import re 
from django.contrib.auth import logout
# --- ¡¡AQUÍ!! Importamos los modelos para chequear el progreso ---
from .models import Ubicacion, MateriaPrima, MovimientoMP

# ============================================================
# LISTA DE CAMINOS PERMITIDOS
# ============================================================
try:
    # Esta lista sigue siendo VITAL. Define la "zona del wizard"
    WIZARD_PATHS = [
        reverse('logout'),
        reverse('inventario:wizard_bienvenida'),
        reverse('inventario:wizard_crear_sucursal'),
        reverse('inventario:wizard_crear_ubicacion'),
        reverse('inventario:wizard_materias_primas'),
        reverse('inventario:wizard_stock_inicial'),
        reverse('inventario:wizard_finalizar'),
        reverse('inventario:wizard_crear_producto'),
        reverse('inventario:mp_create'),
        reverse('inventario:mp_ingreso'),
        reverse('inventario:reporte_stock_global'),
    ]
    
    PRE_SUSCRIPCION_PATHS = [
        reverse('inventario:pagina_precios'),
        reverse('inventario:index'), 
        reverse('signup'),
        reverse('login'),
        reverse('logout'),
    ]

except NoReverseMatch as e:
    print(f"¡ADVERTENCIA! Error al cargar URLs del middleware: {e}")
    WIZARD_PATHS = []
    PRE_SUSCRIPCION_PATHS = []

# ============================================================
# MIDDLEWARE
# ============================================================

class SetupWizardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. EXCLUSIONES (Sin cambios)
        if (not request.user.is_authenticated or 
            request.user.is_superuser or
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.path.startswith('/media/') or 
            request.path.startswith('/static/') or
            request.path.startswith('/admin/')):
            
            return self.get_response(request)

        # 2. CHEQUEO DE SEGURIDAD (Sin cambios)
        if not hasattr(request.user, 'suscripcion'):
            logout(request)
            return redirect('login')
        
        # 3. LÓGICA PRINCIPAL (¡MODIFICADA!)
        suscripcion = request.user.suscripcion

        if suscripcion is None:
            # --- CASO 1: Usuario SIN suscripción (Fase 1 -> Fase 2) ---
            if request.path.startswith('/suscribir/'):
                return self.get_response(request)
            if request.path in PRE_SUSCRIPCION_PATHS:
                return self.get_response(request)
            return redirect('inventario:pagina_precios')

        else:
            # --- CASO 2: Usuario CON suscripción (Fase 3: Wizard) ---
            if suscripcion.ha_completado_onboarding:
                # ¡Usuario 100% activo! Dejarlo pasar.
                return self.get_response(request)
            
            # --- ¡¡AQUÍ EMPIEZA LA NUEVA LÓGICA DE REDIRECCIÓN!! ---
            #
            # Si el usuario NO ha terminado, calculamos a dónde debe ir.
            # Esta es la lógica que te "redirige al paso correcto".
            
            paso_destino_nombre = None
            
            # 1. ¿Ha configurado el nombre de la empresa?
            if suscripcion.nombre_empresa.startswith('Empresa de'):
                paso_destino_nombre = 'inventario:wizard_bienvenida' # Paso 1
            
            # 2. ¿Ha creado su primera bodega?
            elif suscripcion.sucursales.count() == 0:
                paso_destino_nombre = 'inventario:wizard_crear_sucursal' # Paso 2
            
            # 3. ¿Ha creado su primera ubicación?
            elif Ubicacion.objects.filter(sucursal__suscripcion=suscripcion).count() == 0:
                paso_destino_nombre = 'inventario:wizard_crear_ubicacion' # Paso 3
            
            # 4. ¿Ha creado alguna materia prima?
            elif MateriaPrima.objects.filter(suscripcion=suscripcion).count() == 0:
                paso_destino_nombre = 'inventario:wizard_materias_primas' # Paso 4
                
            # 5. ¿Ha registrado su stock inicial?
            elif MovimientoMP.objects.filter(mp__suscripcion=suscripcion, tipo=MovimientoMP.INGRESO).count() == 0:
                paso_destino_nombre = 'inventario:wizard_stock_inicial' # Paso 5
            
            # 6. Si pasó todo, solo le falta finalizar
            else:
                paso_destino_nombre = 'inventario:wizard_finalizar' # Paso 6

            # --- FIN DE LA LÓGICA DE REDIRECCIÓN ---
            
            # Ahora, aplicamos la regla:
            
            # Si el usuario ya está en CUALQUIER página del wizard...
            if request.path in WIZARD_PATHS:
                # ...lo dejamos tranquilo.
                # Esto es VITAL para que pueda navegar hacia "atrás"
                # o recargar la página del paso en el que está.
                return self.get_response(request)
            
            # Si el usuario intenta ir a CUALQUIER OTRO LADO 
            # (como /panel/ o /ventas/)...
            if paso_destino_nombre:
                # ...lo redirigimos al paso que le corresponde.
                return redirect(paso_destino_nombre)

        return self.get_response(request)