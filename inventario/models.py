# ============================================================
#  IMPORTACIONES
# ============================================================
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
# <--- AQUI: Importamos 'Sum' para calcular stocks totales
from django.db import models, transaction
from django.db.models import Sum, Q, F
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission

# -----------------------------------------------------------------
# MODELO 1: LA EMPRESA (EL "DUEÑO" DE TODO)
# -----------------------------------------------------------------
class SuscripcionCliente(models.Model):
    nombre_empresa = models.CharField(max_length=255)

    PLAN_ESENCIAL = 'esencial'
    PLAN_TRAZABILIDAD = 'trazabilidad'
    PLAN_MULTI_SUCURSAL = 'multi_sucursal'

    PLAN_CHOICES = [
        (PLAN_ESENCIAL, 'Esencial (PYME)'),
        (PLAN_TRAZABILIDAD, 'Trazabilidad (Pro)'),
        (PLAN_MULTI_SUCURSAL, 'Multi-Sucursal (Empresa)'),
    ]
    plan_actual = models.CharField(
        max_length=30,
        choices=PLAN_CHOICES,
        default=PLAN_ESENCIAL 
    )
    subscription_status = models.CharField(max_length=20, default="trialing")
    ha_completado_onboarding = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre_empresa} - Plan {self.get_plan_actual_display()}"

    def puede_crear_sucursal(self):
        if self.plan_actual in [self.PLAN_ESENCIAL, self.PLAN_TRAZABILIDAD]:
            return self.sucursales.count() == 0
        return self.plan_actual == self.PLAN_MULTI_SUCURSAL

    def puede_crear_ubicacion(self, sucursal):
        if self.plan_actual == self.PLAN_ESENCIAL:
            return sucursal.ubicaciones.count() == 0
        return self.plan_actual in [self.PLAN_TRAZABILIDAD, self.PLAN_MULTI_SUCURSAL]


# -----------------------------------------------------------------
# MODELO 2: EL USUARIO/EMPLEADO (Sin cambios)
# -----------------------------------------------------------------
class User(AbstractUser):
    suscripcion = models.ForeignKey(
        SuscripcionCliente, 
        on_delete=models.CASCADE,
        related_name="miembros", 
        null=True,
        blank=True
    )
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="inventario_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="inventario_user_permissions",
        related_query_name="user",
    )


# ---------- Helper global (Sin cambios) ----------
def fmt1(value) -> str:
    try:
        d = Decimal(value or 0)
    except Exception:
        return str(value)
    q = d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{int(q)}" if q == q.to_integral() else f"{q.normalize():f}"

# =========================
#  Unidades (Sin cambios)
# =========================
class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50, unique=True) 
    def __str__(self):
        return self.nombre

# =========================================================
#  INICIO: LÓGICA DE WMS
# =========================================================

class Sucursal(models.Model):
    suscripcion = models.ForeignKey(
        SuscripcionCliente, 
        on_delete=models.CASCADE, 
        related_name="sucursales"
    )
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True)
    es_principal = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ("suscripcion", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.suscripcion.nombre_empresa})"

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.suscripcion.puede_crear_sucursal():
                raise ValidationError(f"Tu plan ({self.suscripcion.get_plan_actual_display()}) solo permite 1 sucursal.")
        super().save(*args, **kwargs)


class Ubicacion(models.Model):
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name="ubicaciones"
    )
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("sucursal", "nombre")
        ordering = ["sucursal__nombre", "nombre"]
    
    def __str__(self):
        return f"[{self.sucursal.nombre}] > {self.nombre}"

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.sucursal.suscripcion.puede_crear_ubicacion(self.sucursal):
                 raise ValidationError(f"Tu plan ({self.sucursal.suscripcion.get_plan_actual_display()}) solo permite 1 ubicación por sucursal.")
        super().save(*args, **kwargs)


# =========================
#  Materias Primas (Modificado)
# =========================
class MateriaPrima(models.Model):
    suscripcion = models.ForeignKey(SuscripcionCliente, on_delete=models.CASCADE, related_name="materias_primas")
    nombre = models.CharField(max_length=120) 
    unidad = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT) 

    # (Campos 'stock' y 'stock_minimo' eliminados de aquí)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["nombre"] 
        unique_together = ("suscripcion", "nombre")
    
    def __str__(self):
        return self.nombre
    
    @property
    def stock_total(self) -> Decimal:
        total = self.stock_por_ubicacion.aggregate(
            total=Sum('stock')
        )['total']
        return total or Decimal("0")

    @property
    def stock_minimo_total(self) -> Decimal:
        total = self.stock_por_ubicacion.aggregate(
            total=Sum('stock_minimo')
        )['total']
        return total or Decimal("0")

    @property
    def stock_total_fmt(self) -> str: return fmt1(self.stock_total)
    
    @property
    def stock_minimo_total_fmt(self) -> str: return fmt1(self.stock_minimo_total)

    # (Funciones de formato sin cambios)
    def _fmt_decimal_short(self, x: Decimal, max_dec: int = 1) -> str:
        d = Decimal(x or 0); q = d.quantize(Decimal(10) ** -max_dec, rounding=ROUND_HALF_UP); return f"{int(q)}" if q == q.to_integral() else f"{q.normalize():f}"
    
    def format_qty(self, qty: Decimal) -> str:
        d = Decimal(qty or 0); u = (self.unidad.nombre or "").lower()
        if u == "kg":
            if d >= 1: return f"{self._fmt_decimal_short(d)} kg"
            g = (d * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP); return f"{int(g)} g"
        if u in ("l", "lt", "litro", "litros"):
            if d >= 1: return f"{self._fmt_decimal_short(d)} l"
            ml = (d * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP); return f"{int(ml)} ml"
        return f"{self._fmt_decimal_short(d)} {self.unidad.nombre}"


class StockPorUbicacion(models.Model):
    ubicacion = models.ForeignKey(
        Ubicacion, 
        on_delete=models.CASCADE, 
        related_name="stock_items"
    )
    mp = models.ForeignKey(
        MateriaPrima, 
        on_delete=models.CASCADE, 
        related_name="stock_por_ubicacion"
    )
    stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        unique_together = ("ubicacion", "mp")
        ordering = ["ubicacion__sucursal__nombre", "ubicacion__nombre", "mp__nombre"]

    def __str__(self):
        return f"{self.ubicacion} | {self.mp.nombre}: {fmt1(self.stock)}"


# =========================
#  Kardex (¡CORREGIDO!)
# =========================
class MovimientoMP(models.Model):
    INGRESO = "INGRESO"; CONSUMO = "CONSUMO"; AJUSTE_POS = "AJUSTE_POS"; AJUSTE_NEG = "AJUSTE_NEG"; MERMA = "MERMA"
    TIPOS = [(INGRESO, "Ingreso"), (CONSUMO, "Consumo"), (AJUSTE_POS, "Ajuste (+)"), (AJUSTE_NEG, "Ajuste (-)"), (MERMA, "Merma")]
    
    mp = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT, related_name="movimientos")
    
    # <--- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
    # Este campo 'tipo' faltaba.
    tipo = models.CharField(max_length=12, choices=TIPOS)
    
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="movimientos_mp",
    )
    
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    fecha = models.DateTimeField(default=timezone.now)
    nota = models.CharField(max_length=250, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta: 
        ordering = ["-fecha"] 
    
    def __str__(self): return f"{self.ubicacion} · {self.mp} · {self.tipo} · {fmt1(self.cantidad)}"
    
    @property
    def cantidad_signed(self) -> Decimal: 
        return self.cantidad if self.tipo in [self.INGRESO, self.AJUSTE_POS] else -self.cantidad
    
    # (Lógica save() y delete() sin cambios)
    def save(self, *args, **kwargs):
        with transaction.atomic():
            delta = Decimal("0")
            if self.pk: 
                old_mov = MovimientoMP.objects.select_for_update().get(pk=self.pk)
                delta = self.cantidad_signed - old_mov.cantidad_signed
            else: 
                delta = self.cantidad_signed
            
            super().save(*args, **kwargs) 
            
            stock_item, created = StockPorUbicacion.objects.select_for_update().get_or_create(
                ubicacion=self.ubicacion,
                mp=self.mp,
                defaults={'stock': Decimal("0")} 
            )
            
            stock_item.stock = (stock_item.stock or Decimal("0")) + (delta or Decimal("0"))
            stock_item.save(update_fields=["stock"])
    
    def delete(self, *args, **kwargs):
        with transaction.atomic():
            try:
                stock_item = StockPorUbicacion.objects.select_for_update().get(
                    ubicacion=self.ubicacion, 
                    mp=self.mp
                )
                stock_item.stock = (stock_item.stock or Decimal("0")) - (self.cantidad_signed or Decimal("0"))
                stock_item.save(update_fields=["stock"])
            except StockPorUbicacion.DoesNotExist:
                pass
            super().delete(*args, **kwargs)

# =========================
#  Productos (Sin cambios)
# =========================
class Producto(models.Model):
    suscripcion = models.ForeignKey(SuscripcionCliente, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=120) 
    unidad = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT) 
    vida_util_dias = models.PositiveIntegerField(default=3) 
    activo = models.BooleanField(default=True)
    class Meta:
        ordering = ["nombre"]
        unique_together = ("suscripcion", "nombre")
    def __str__(self): return self.nombre
    # (helpers de formato sin cambios)
    def _fmt_decimal_short(self, x: Decimal, max_dec: int = 1) -> str:
        d = Decimal(x or 0); q = d.quantize(Decimal(10) ** -max_dec, rounding=ROUND_HALF_UP); return f"{int(q)}" if q == q.to_integral() else f"{q.normalize():f}"
    def format_qty(self, qty: Decimal) -> str:
        u = (self.unidad.nombre or "").lower(); d = Decimal(qty or 0)
        if u == "kg":
            if d >= 1: return f"{self._fmt_decimal_short(d)} kg"
            g = (d * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP); return f"{int(g)} g"
        if u in ("l", "lt", "litro", "litros"):
            if d >= 1: return f"{self._fmt_decimal_short(d)} l"
            ml = (d * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP); return f"{int(ml)} ml"
        return f"{self._fmt_decimal_short(d)} {self.unidad.nombre}"

# =========================
#  Recetas (Sin cambios)
# =========================
class Receta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="recetas")
    nombre = models.CharField(max_length=120, default="Tradicional")
    version = models.PositiveIntegerField(default=1)
    rendimiento_por_lote = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    descripcion = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    activo = models.BooleanField(default=True)
    class Meta:
        unique_together = ("producto", "nombre", "version")
        ordering = ["producto__nombre", "-version"] 
    def __str__(self): return f"{self.producto.nombre} - {self.nombre} v{self.version}"

class RecetaLinea(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name="lineas")
    mp = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT) 
    cantidad = models.DecimalField(max_digits=12, decimal_places=3) 
    class Meta:
        unique_together = ("receta", "mp")
        ordering = ["mp__nombre"]
    def __str__(self): return f"{self.receta} → {self.mp} x {fmt1(self.cantidad)}"
    def por_lote_fmt(self) -> str: return self.mp.format_qty(self.cantidad)
    def total_para(self, lotes) -> Decimal: return Decimal(self.cantidad) * Decimal(lotes)
    def total_para_fmt(self, lotes) -> str: return self.mp.format_qty(self.total_para(lotes))

# =========================
#  Producción / Lotes (Modificado)
# =========================
class OrdenProduccion(models.Model):
    BORRADOR = "BORRADOR"; CONSUMIDA = "CONSUMIDA"; ESTADOS = [(BORRADOR, "Borrador"), (CONSUMIDA, "Consumida")]
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT)
    lotes = models.DecimalField(max_digits=12, decimal_places=3, default=1) 
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=BORRADOR)
    nota = models.CharField(max_length=250, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="ordenes_produccion",
        null=True # Permitir null temporalmente
    )

    class Meta: ordering = ["-fecha"]
    def __str__(self): return f"OP #{self.id or '—'} · {self.producto} · {fmt1(self.lotes)} lote(s)"
    
    # (Propiedades sin cambios)
    @property
    def unidades_totales(self): return (self.receta.rendimiento_por_lote or Decimal("0")) * (self.lotes or Decimal("0"))
    @property
    def unidades_totales_fmt(self) -> str: return self.producto.format_qty(self.unidades_totales)
    @property
    def detalle_consumo(self):
        rows = [];
        for ln in self.receta.lineas.select_related("mp"):
            total = Decimal(ln.cantidad) * Decimal(self.lotes or 0)
            rows.append({"mp": ln.mp, "por_lote": ln.por_lote_fmt(), "total_fmt": ln.mp.format_qty(total)})
        return rows
    
    def validar_stock(self):
        if not self.sucursal:
            raise ValidationError("La Orden de Producción no tiene una sucursal asignada.")

        faltantes = []
        for ln in self.receta.lineas.select_related("mp"):
            requerido = Decimal(ln.cantidad) * Decimal(self.lotes)
            
            stock_disponible = StockPorUbicacion.objects.filter(
                mp=ln.mp, 
                ubicacion__sucursal=self.sucursal
            ).aggregate(total=Sum('stock'))['total'] or Decimal("0")
            
            if stock_disponible < requerido:
                faltantes.append(f"{ln.mp.nombre}: req {fmt1(requerido)} / disp {fmt1(stock_disponible)}")
        
        if faltantes: raise ValidationError("Stock insuficiente en esta sucursal → " + "; ".join(faltantes))
    
    def consumir_mp(self, user=None):
        for ln in self.receta.lineas.select_related("mp"):
            pendiente = Decimal(ln.cantidad) * Decimal(self.lotes)
            
            stock_items = StockPorUbicacion.objects.filter(
                mp=ln.mp,
                ubicacion__sucursal=self.sucursal,
                stock__gt=0
            ).order_by('ubicacion__nombre') 

            for item in stock_items:
                if pendiente <= 0: break
                
                tomar = min(pendiente, item.stock)
                
                if tomar > 0:
                    MovimientoMP.objects.create(
                        mp=ln.mp, 
                        ubicacion=item.ubicacion, 
                        tipo=MovimientoMP.CONSUMO, # <--- Usa el campo 'tipo'
                        cantidad=tomar, 
                        nota=f"OP {self.pk} · {self.producto}", 
                        created_by=user
                    )
                    pendiente -= tomar
            
            if pendiente > 0:
                raise ValidationError(f"Error de consistencia al consumir {ln.mp.nombre}")
    
    def ejecutar(self, user=None):
        if self.estado == self.CONSUMIDA: return 
        self.validar_stock() 
        
        ubicacion_destino = Ubicacion.objects.filter(sucursal=self.sucursal).first()
        if not ubicacion_destino:
            raise ValidationError(f"La sucursal {self.sucursal} no tiene ubicaciones para recibir el producto.")

        with transaction.atomic():
            self.consumir_mp(user=user); self.estado = self.CONSUMIDA; self.save(update_fields=["estado"])
            
            unidades = self.unidades_totales; fecha_prod = self.fecha
            venc = (fecha_prod + timedelta(days=self.producto.vida_util_dias)).date()
            codigo = LoteProducto.generar_codigo(self.producto, fecha_prod)
            
            LoteProducto.objects.create(
                producto=self.producto, 
                codigo=codigo, 
                op=self, 
                fecha_produccion=fecha_prod, 
                fecha_vencimiento=venc, 
                cantidad_inicial=unidades, 
                cantidad_disponible=unidades, 
                created_by=user,
                ubicacion=ubicacion_destino
            )

class LoteProducto(models.Model):
    OK = "OK"; POR_RALLAR = "RALLAR"; VENCIDO = "VENCIDO"
    ESTADOS = [(OK, "OK"), (POR_RALLAR, "Por pan rallado"), (VENCIDO, "Vencido")]
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="lotes")
    codigo = models.CharField(max_length=30, unique=True) 
    op = models.ForeignKey(OrdenProduccion, null=True, blank=True, on_delete=models.SET_NULL, related_name="lotes_creados")
    
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="lotes_producto",
        null=True # Permitir null temporalmente
    )
    
    fecha_produccion = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    cantidad_inicial = models.DecimalField(max_digits=12, decimal_places=3)
    cantidad_disponible = models.DecimalField(max_digits=12, decimal_places=3)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=OK)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta: ordering = ["fecha_vencimiento", "-cantidad_disponible"]
    def __str__(self): return f"{self.codigo} · {self.producto} @ {self.ubicacion}"
    
    # (Propiedades sin cambios)
    @property
    def cantidad_inicial_fmt(self) -> str: return self.producto.format_qty(self.cantidad_inicial)
    @property
    def cantidad_disponible_fmt(self) -> str: return self.producto.format_qty(self.cantidad_disponible)
    @staticmethod
    def generar_codigo(producto, fecha_dt):
        base = f"{producto.id}-{fecha_dt.strftime('%Y%m%d')}"
        n = LoteProducto.objects.filter(producto__suscripcion=producto.suscripcion, producto=producto, fecha_produccion__date=fecha_dt.date()).count() + 1
        return f"{base}-{n:03d}" 
    @property
    def dias_restantes(self): return (self.fecha_vencimiento - timezone.localdate()).days
    def _calcular_estado(self):
        d = self.dias_restantes
        if d < 0: return self.VENCIDO
        elif d <= 1: return self.POR_RALLAR
        return self.OK
    def save(self, *args, **kwargs):
        self.estado = self._calcular_estado()
        super().save(*args, **kwargs)

# =========================
#  Ventas (Modificado)
# =========================
class Venta(models.Model):
    BORRADOR = "BORRADOR"; CONFIRMADA = "CONFIRMADA"; ESTADOS = [(BORRADOR, "Borrador"), (CONFIRMADA, "Confirmada")]
    suscripcion = models.ForeignKey(SuscripcionCliente, on_delete=models.CASCADE, related_name="ventas")
    
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="ventas",
        null=True # Permitir null temporalmente
    )
    
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=BORRADOR)
    nota = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta: ordering = ["-fecha"]
    def __str__(self): return f"Venta #{self.id or '—'} ({self.sucursal.nombre})"
    
    def validar_stock(self):
        if not self.sucursal:
            raise ValidationError("La Venta no tiene una sucursal asignada.")
        if self.lineas.count() == 0: raise ValidationError("La venta no tiene líneas.")
        
        faltantes = []
        for ln in self.lineas.select_related("producto"):
            qs = LoteProducto.objects.filter(
                producto=ln.producto, 
                ubicacion__sucursal=self.sucursal, 
                estado__in=[LoteProducto.OK, LoteProducto.POR_RALLAR], 
                cantidad_disponible__gt=0
            ).order_by("fecha_vencimiento", "created_at")
            
            disp = sum((l.cantidad_disponible or Decimal("0")) for l in qs)
            if disp < ln.cantidad:
                faltantes.append(f"{ln.producto}: req {fmt1(ln.cantidad)} / disp {fmt1(disp)}")
        
        if faltantes: raise ValidationError(f"Stock insuficiente en {self.sucursal.nombre} → " + "; ".join(faltantes))
    
    @transaction.atomic 
    def consumir_fifo(self, user=None):
        if self.estado == self.CONFIRMADA: return 
        self.validar_stock() 
        
        for ln in self.lineas.select_related("producto"):
            pendiente = Decimal(ln.cantidad) 
            
            lotes = LoteProducto.objects.select_for_update().filter(
                producto=ln.producto, 
                ubicacion__sucursal=self.sucursal, 
                estado__in=[LoteProducto.OK, LoteProducto.POR_RALLAR], 
                cantidad_disponible__gt=0
            ).order_by("fecha_vencimiento", "created_at")
            
            for lote in lotes:
                if pendiente <= 0: break 
                tomar = min(pendiente, lote.cantidad_disponible)
                if tomar > 0:
                    lote.cantidad_disponible = (lote.cantidad_disponible or Decimal("0")) - tomar; lote.save()
                    VentaConsumo.objects.create(venta=self, linea=ln, lote=lote, cantidad=tomar, created_by=user)
                    pendiente -= tomar
            
            if pendiente > 0: raise ValidationError(f"Stock insuficiente durante consumo: {ln.producto}")
        
        self.estado = self.CONFIRMADA; self.save(update_fields=["estado"])

# (VentaLinea y VentaConsumo sin cambios estructurales)
class VentaLinea(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3) 
    def __str__(self): return f"{self.producto} x {fmt1(self.cantidad)}"
    @property
    def cantidad_fmt(self) -> str: return self.producto.format_qty(self.cantidad)

class VentaConsumo(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="consumos")
    linea = models.ForeignKey(VentaLinea, on_delete=models.CASCADE, related_name="consumos")
    lote = models.ForeignKey(LoteProducto, on_delete=models.PROTECT, related_name="consumos")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta: ordering = ["created_at"]
    def __str__(self): return f"{self.venta_id} · {self.lote.codigo} · {fmt1(self.cantidad)}"
    @property
    def cantidad_fmt(self) -> str: return self.lote.producto.format_qty(self.cantidad)

# =========================
#  Históricos (Sin cambios)
# =========================
class HistoricoVenta(models.Model):
    suscripcion = models.ForeignKey(SuscripcionCliente, on_delete=models.CASCADE, related_name="historico_ventas")
    fecha = models.DateField()
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    class Meta: ordering = ["fecha"]
    def __str__(self): return f"{self.fecha} · {self.producto} · {self.cantidad}"