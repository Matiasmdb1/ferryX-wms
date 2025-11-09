from django.contrib import admin
from .models import (
    UnidadMedida, MateriaPrima, MovimientoMP,
    Producto, Receta, RecetaLinea, OrdenProduccion,
    LoteProducto, Venta, VentaLinea, VentaConsumo,
    
    # <--- Registramos los nuevos modelos
    Sucursal, Ubicacion, StockPorUbicacion
)

# ============================================================
#  NUEVOS MODELOS WMS
# ============================================================

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "suscripcion", "es_principal", "activa")
    list_filter = ("suscripcion", "es_principal", "activa")
    search_fields = ("nombre", "suscripcion__nombre_empresa")

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sucursal", "activo")
    list_filter = ("sucursal", "activo", "sucursal__suscripcion")
    search_fields = ("nombre", "sucursal__nombre")
    autocomplete_fields = ("sucursal",)

@admin.register(StockPorUbicacion)
class StockPorUbicacionAdmin(admin.ModelAdmin):
    list_display = ("mp", "get_sucursal", "ubicacion", "stock", "stock_minimo")
    list_filter = ("ubicacion__sucursal", "mp")
    search_fields = ("mp__nombre", "ubicacion__nombre", "ubicacion__sucursal__nombre")
    list_editable = ("stock", "stock_minimo")
    autocomplete_fields = ("mp", "ubicacion") 
    ordering = ("mp__nombre", "ubicacion__sucursal__nombre", "ubicacion__nombre")

    @admin.display(description="Sucursal", ordering="ubicacion__sucursal")
    def get_sucursal(self, obj):
        return obj.ubicacion.sucursal

# ============================================================
#  MODELOS EXISTENTES (Actualizados)
# ============================================================

@admin.register(UnidadMedida)
class UMAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

@admin.register(MateriaPrima)
class MPAdmin(admin.ModelAdmin):
    # <--- 'stock' y 'stock_minimo' eliminados de list_display
    list_display = ("id", "nombre", "unidad", "activo", "get_stock_total_fmt")
    list_filter = ("unidad", "activo")
    search_fields = ("nombre",)
    
    @admin.display(description="Stock Total (Calculado)")
    def get_stock_total_fmt(self, obj):
        return obj.stock_total_fmt

@admin.register(MovimientoMP)
class MovAdmin(admin.ModelAdmin):
    # <--- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
    # 'tipo' ahora existe y puede ser usado
    list_display = ("id", "fecha", "mp", "ubicacion", "tipo", "cantidad", "created_by")
    list_filter = ("tipo", "mp", "ubicacion__sucursal")
    search_fields = ("mp__nombre", "nota", "ubicacion__nombre")
    date_hierarchy = "fecha"
    autocomplete_fields = ("mp", "ubicacion")

# -------- Productos / Recetas --------
class RecetaLineaInline(admin.TabularInline):
    model = RecetaLinea
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "unidad", "vida_util_dias", "activo")
    list_filter = ("unidad", "activo")
    search_fields = ("nombre",)

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ("id", "producto", "nombre", "version", "rendimiento_por_lote", "activo", "creada_en")
    list_filter = ("producto", "activo", "version")
    search_fields = ("producto__nombre", "nombre")
    inlines = [RecetaLineaInline]

# -------- Producción / Lotes --------
@admin.register(OrdenProduccion)
class OPAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "sucursal", "producto", "receta", "lotes", "estado", "created_by")
    list_filter = ("estado", "producto", "sucursal")
    search_fields = ("id", "producto__nombre", "receta__nombre", "sucursal__nombre")
    date_hierarchy = "fecha"

@admin.register(LoteProducto)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "producto", "ubicacion", "cantidad_disponible", "fecha_produccion", "fecha_vencimiento", "estado")
    list_filter = ("estado", "producto", "ubicacion__sucursal")
    search_fields = ("codigo", "producto__nombre", "ubicacion__nombre")
    date_hierarchy = "fecha_produccion"

# -------- Ventas --------
class VentaLineaInline(admin.TabularInline):
    model = VentaLinea
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "sucursal", "estado", "created_by")
    list_filter = ("estado", "sucursal")
    inlines = [VentaLineaInline]
    date_hierarchy = "fecha"

@admin.register(VentaLinea)
class VentaLineaAdmin(admin.ModelAdmin):
    list_display = ("venta", "producto", "cantidad")
    search_fields = ("venta__id", "producto__nombre")

@admin.register(VentaConsumo)
class VentaConsumoAdmin(admin.ModelAdmin): # <--- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! (ModelAdmin)
    list_display = ("venta", "linea", "lote", "cantidad", "created_at")
    list_filter = ("lote__producto",)
    date_hierarchy = "created_at"
    ordering = ("created_at",)
    search_fields = ("venta__id", "lote__codigo", "linea__producto__nombre")