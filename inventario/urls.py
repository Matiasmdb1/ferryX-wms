# inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # ============================================================
    # VISTAS PÚBLICAS Y DE SUSCRIPCIÓN (FASE 1 y 2)
    # ============================================================
    path('', views.index, name='index'),
    path('precios/', views.pagina_precios, name='pagina_precios'),
    path('suscribir/<str:plan_id>/', views.SimularSuscripcionView.as_view(), name='simular_suscripcion'),
    path('mi-cuenta/', views.ver_suscripcion, name='ver_suscripcion'),

    # ============================================================
    # VISTAS DEL WIZARD DE ONBOARDING (FASE 3)
    # ============================================================
    
    # --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
    # El middleware (y tu URL antigua) buscan 'wizard_bienvenida'.
    # Ahora apuntamos ese nombre a la NUEVA vista (Fase 3, Paso 1).
    path('wizard/bienvenida/', views.WizardConfigEmpresaView.as_view(), name='wizard_bienvenida'),
    
    # El resto del nuevo flujo del wizard
    path('wizard/sucursal/', views.WizardCrearSucursalView.as_view(), name='wizard_crear_sucursal'),
    path('wizard/ubicacion/', views.WizardCrearUbicacionView.as_view(), name='wizard_crear_ubicacion'),
    path('wizard/materias-primas/', views.wizard_materias_primas, name='wizard_materias_primas'),
    
    # NOTA: Eliminamos 'wizard_productos' (la vista de lista) para simplificar
    # el flujo, pero MANTENEMOS la URL para 'crear' el producto.
    path('wizard/crear-producto/', views.ProductoCreateView.as_view(), name='wizard_crear_producto'),

    path('wizard/stock-inicial/', views.wizard_stock_inicial, name='wizard_stock_inicial'),
    path('wizard/finalizar/', views.wizard_finalizar, name='wizard_finalizar'),
    

    # ============================================================
    # VISTAS CRUD DE BODEGAS (¡NUEVAS!)
    # ============================================================
    # (Para que funcionen los enlaces de base.html)
    path('bodegas/', views.SucursalListView.as_view(), name='sucursal_list'),
    path('bodegas/crear/', views.SucursalCreateView.as_view(), name='sucursal_create'),
    path('ubicaciones/', views.UbicacionListView.as_view(), name='ubicacion_list'),
    path('ubicaciones/crear/', views.UbicacionCreateView.as_view(), name='ubicacion_create'),

    # ============================================================
    # VISTAS CORE DEL ERP
    # ============================================================

    # --- Dashboard ---
    path('panel/', views.panel, name='panel'),
    path('panel/csv/', views.panel_csv, name='panel_csv'),

    # --- Materias Primas / Kardex ---
    path('mp/', views.MPListView.as_view(), name='mp_list'),
    path('mp/nueva/', views.MPCreateView.as_view(), name='mp_create'),
    path('mp/ingreso/', views.MPIngresoView.as_view(), name='mp_ingreso'),
    path('mp/ajuste/', views.MPAjusteView.as_view(), name='mp_ajuste'),
    path('mp/merma/', views.MPMermaView.as_view(), name='mp_merma'),
    path('kardex/', views.kardex, name='kardex'),

    # --- Recetas / Productos ---
    path('recetas/', views.RecetaListView.as_view(), name='receta_list'),
    path('recetas/nueva/', views.RecetaCreateView.as_view(), name='receta_create'),
    path('recetas/<int:pk>/', views.RecetaDetailView.as_view(), name='receta_detail'),
    path('recetas/<int:pk>/editar/', views.RecetaUpdateView.as_view(), name='receta_update'),

    # --- Producción (OPs) ---
    path('produccion/', views.OPListView.as_view(), name='op_list'),
    path('produccion/nueva/', views.OPCreateView.as_view(), name='op_create'),
    path('produccion/<int:pk>/', views.OPDetailView.as_view(), name='op_detail'),

    # --- Lotes ---
    path('lotes/', views.LoteListView.as_view(), name='lote_list'),
    path('lotes/<int:pk>/', views.LoteDetailView.as_view(), name='lote_detail'),

    # --- Ventas ---
    path('ventas/', views.VentaListView.as_view(), name='venta_list'),
    path('ventas/nueva/', views.VentaCreateView.as_view(), name='venta_create'),
    path('ventas/<int:pk>/', views.VentaDetailView.as_view(), name='venta_detail'),

    # ============================================================
    # VISTAS DE IA E INTEGRACIONES
    # ============================================================
    path('ia/predecir/', views.predict_view, name='predict'),
    path('ia/cargar-excel/', views.CargarExcelVentasView.as_view(), name='cargar_excel'),
    path('ia/procesar-factura/', views.procesar_factura, name='procesar_factura'),
    path('ia/guardar-factura/', views.guardar_ingreso_factura, name='guardar_ingreso_factura'),
    path('reporte/stock-global/', views.reporte_stock_global, name='reporte_stock_global'),
]