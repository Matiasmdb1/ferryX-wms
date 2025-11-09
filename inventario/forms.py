# inventario/forms.py
# ============================================================
#  IMPORTACIONES
# ============================================================
from decimal import Decimal, ROUND_HALF_UP
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

# <--- ¡CORRECCIÓN! ---
# Se importa Sum de models y Coalesce de functions
from django.db.models import Sum
from django.db.models.functions import Coalesce

from .models import User 

from .models import (
    MateriaPrima, MovimientoMP,
    OrdenProduccion, Receta, RecetaLinea, Producto,
    Venta, VentaLinea,
    SuscripcionCliente,
    # <--- AQUI: Importamos los nuevos modelos WMS
    Sucursal, Ubicacion, StockPorUbicacion
)

# ============================================================
#  FORMULARIOS DE USUARIO (Sin cambios)
# ============================================================
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",) 

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

NUM_WIDGET = forms.NumberInput(attrs={"step": "0.1", "inputmode": "decimal"})

class SmartDecimalField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('decimal_places', 1) 
        kwargs.setdefault('max_digits', 12)
        kwargs.setdefault('widget', NUM_WIDGET)
        super().__init__(*args, **kwargs)
    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace(" ", "").replace(",", ".")
        val = super().to_python(value)
        if val is None: return None
        rounding_decimal = Decimal(10) ** -self.decimal_places
        return val.quantize(rounding_decimal, rounding=ROUND_HALF_UP)
    def prepare_value(self, value):
        try: d = Decimal(str(value))
        except Exception: return value
        rounding_decimal = Decimal(10) ** -self.decimal_places
        q = d.quantize(rounding_decimal, rounding=ROUND_HALF_UP)
        return str(int(q)) if q == q.to_integral() else f"{q.normalize():f}"

# =========================
#  Materias Primas / Movimientos
# =========================

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        fields = ("nombre", "unidad", "activo") # 'stock_minimo' eliminado
    def save(self, commit=True, user=None):
        instancia = super().save(commit=False)
        if user and user.suscripcion:
            instancia.suscripcion = user.suscripcion
        if commit:
            instancia.save()
        return instancia


class MovimientoIngresoForm(forms.ModelForm):
    cantidad = SmartDecimalField(min_value=Decimal("0.1")) 
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            suscripcion = user.suscripcion
            self.fields['mp'].queryset = MateriaPrima.objects.filter(suscripcion=suscripcion, activo=True)
            self.fields['ubicacion'].queryset = Ubicacion.objects.filter(
                sucursal__suscripcion=suscripcion,
                activo=True
            ).select_related('sucursal')
            primera_ubicacion = self.fields['ubicacion'].queryset.first()
            if primera_ubicacion:
                self.fields['ubicacion'].initial = primera_ubicacion
            
    class Meta:
        model = MovimientoMP
        fields = ["mp", "ubicacion", "cantidad", "nota"] 
    def save(self, user=None, commit=True):
        obj = super().save(commit=False); obj.tipo = MovimientoMP.INGRESO
        if user: obj.created_by = user
        if commit: obj.save()
        return obj


class MovimientoAjusteForm(forms.ModelForm):
    TIPO = forms.ChoiceField(choices=[(MovimientoMP.AJUSTE_POS, "Ajuste (+)"), (MovimientoMP.AJUSTE_NEG, "Ajuste (-)")])
    cantidad = SmartDecimalField(min_value=Decimal("0.1")) 

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            suscripcion = user.suscripcion
            self.fields['mp'].queryset = MateriaPrima.objects.filter(suscripcion=suscripcion, activo=True)
            self.fields['ubicacion'].queryset = Ubicacion.objects.filter(
                sucursal__suscripcion=suscripcion,
                activo=True
            ).select_related('sucursal')
            primera_ubicacion = self.fields['ubicacion'].queryset.first()
            if primera_ubicacion:
                self.fields['ubicacion'].initial = primera_ubicacion

    class Meta:
        model = MovimientoMP
        fields = ["mp", "ubicacion", "TIPO", "cantidad", "nota"]
    
    def save(self, user=None, commit=True):
        obj = super().save(commit=False); obj.tipo = self.cleaned_data["TIPO"]
        if user: obj.created_by = user
        if commit: obj.save()
        return obj

class MovimientoMermaForm(forms.ModelForm):
    cantidad = SmartDecimalField(min_value=Decimal("0.1")) 
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            suscripcion = user.suscripcion
            self.fields['mp'].queryset = MateriaPrima.objects.filter(suscripcion=suscripcion, activo=True)
            self.fields['ubicacion'].queryset = Ubicacion.objects.filter(
                sucursal__suscripcion=suscripcion,
                activo=True
            ).select_related('sucursal')
            primera_ubicacion = self.fields['ubicacion'].queryset.first()
            if primera_ubicacion:
                self.fields['ubicacion'].initial = primera_ubicacion

    class Meta:
        model = MovimientoMP
        fields = ["mp", "ubicacion", "cantidad", "nota"]
    def save(self, user=None, commit=True):
        obj = super().save(commit=False); obj.tipo = MovimientoMP.MERMA
        if user: obj.created_by = user
        if commit: obj.save()
        return obj

# =========================
#  Recetas (Sin cambios)
# =========================
class RecetaForm(forms.ModelForm):
    nombre = forms.CharField(label="Nombre de la receta", widget=forms.TextInput(attrs={"placeholder": "Ej: Tradicional, Integral, Completos …"}))
    rendimiento_por_lote = SmartDecimalField(
        min_value=Decimal("0.1"), 
        label="Rendimiento por lote (en unidad del producto)"
    )
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            self.fields['producto'].queryset = Producto.objects.filter(suscripcion=user.suscripcion, activo=True)
    class Meta:
        model = Receta
        fields = ["producto", "nombre", "version", "rendimiento_por_lote", "activo"]

class RecetaLineaForm(forms.ModelForm):
    cantidad_valor = SmartDecimalField(
        min_value=Decimal("0.001"),
        decimal_places=3, 
        widget=forms.NumberInput(attrs={"step": "1", "inputmode": "decimal"}),
        label="Cantidad"
    )
    cantidad_unidad = forms.ChoiceField(choices=[("auto", "—")], label="Unidad")
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            self.fields['mp'].queryset = MateriaPrima.objects.filter(suscripcion=user.suscripcion, activo=True)
    class Meta:
        model = RecetaLinea
        fields = ["mp"] 
    def clean(self):
        c = super().clean(); mp = c.get("mp"); val = c.get("cantidad_valor"); uin = c.get("cantidad_unidad") 
        if not mp or not val: return c
        unidad_base = (mp.unidad.nombre or "").lower(); cantidad_base = Decimal(val) 
        if unidad_base == "kg":
            if uin and uin.lower() == "g": cantidad_base = Decimal(val) / Decimal("1000")
        elif unidad_base in ("l", "lt", "litro", "litros"):
            if uin and uin.lower() == "ml": cantidad_base = Decimal(val) / Decimal("1000")
        self.cleaned_data["cantidad_base"] = cantidad_base
        return c
    def save(self, commit=True):
        inst = super().save(commit=False); inst.cantidad = self.cleaned_data.get("cantidad_base") or Decimal("0")
        if commit: inst.save()
        return inst

class RecetaLineaBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean(); mps = set(); at_least_one = False
        for form in self.forms: 
            if not getattr(form, "cleaned_data", None): continue
            if form.cleaned_data.get("DELETE"): continue
            mp = form.cleaned_data.get("mp")
            if mp:
                at_least_one = True
                if mp in mps: form.add_error("mp", "La materia prima está duplicada.")
                mps.add(mp)
        if not at_least_one:
            raise forms.ValidationError("La receta debe tener al menos un ingrediente.")

RecetaLineaFormSet = inlineformset_factory(Receta, RecetaLinea, form=RecetaLineaForm, formset=RecetaLineaBaseFormSet, extra=1, can_delete=True)

# =========================
#  Producción (OP)
# =========================
class OrdenProduccionForm(forms.ModelForm):
    confirmar_y_ejecutar = forms.BooleanField(required=False, label="Confirmar y ejecutar (descontar MP y generar lote)")
    lotes = SmartDecimalField(label="Cantidad a producir", min_value=Decimal("0.1")) 

    class Meta:
        model = OrdenProduccion
        fields = ["sucursal", "producto", "receta", "lotes", "nota", "confirmar_y_ejecutar"]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None); super().__init__(*args, **kwargs)
        
        if user and user.suscripcion:
            suscripcion = user.suscripcion
            self.fields['producto'].queryset = Producto.objects.filter(suscripcion=suscripcion, activo=True)
            
            self.fields['sucursal'].queryset = Sucursal.objects.filter(
                suscripcion=suscripcion, 
                activa=True
            )
            
            sucursal_principal = self.fields['sucursal'].queryset.filter(es_principal=True).first()
            if sucursal_principal:
                self.fields['sucursal'].initial = sucursal_principal
            elif self.fields['sucursal'].queryset.exists():
                self.fields['sucursal'].initial = self.fields['sucursal'].queryset.first()

            prod = None
            if self.data.get("producto"): 
                try:
                    prod_id = int(self.data.get("producto"))
                    prod = Producto.objects.get(pk=prod_id, suscripcion=suscripcion)
                except (Producto.DoesNotExist, TypeError, ValueError): prod = None
            elif self.instance and self.instance.pk: prod = self.instance.producto
            
            if prod:
                self.fields["receta"].queryset = Receta.objects.filter(producto=prod, activo=True)
                self.fields["lotes"].label = f"Cantidad a producir ({prod.unidad.nombre})"
            else:
                self.fields["receta"].queryset = Receta.objects.none()
    
    def clean(self):
        c = super().clean()
        prod = c.get("producto"); rec = c.get("receta"); lotes = c.get("lotes")
        sucursal = c.get("sucursal")

        if rec and prod and rec.producto_id != prod.id:
            raise forms.ValidationError("La receta seleccionada no corresponde a ese producto.")
        
        if lotes and lotes <= 0: self.add_error("lotes", "La cantidad a producir debe ser > 0.")
        
        if c.get("confirmar_y_ejecutar") and rec and lotes and sucursal:
            faltantes = []
            for ln in rec.lineas.select_related("mp", "mp__unidad"):
                req = (ln.cantidad or Decimal("0")) * lotes
                
                stock_en_sucursal = StockPorUbicacion.objects.filter(
                    mp=ln.mp,
                    ubicacion__sucursal=sucursal
                ).aggregate(
                    total=Coalesce(Sum('stock'), Decimal('0.0'))
                )['total']
                
                disp = stock_en_sucursal
                
                if disp < req:
                    req_fmt = ln.mp.format_qty(req)
                    disp_fmt = ln.mp.format_qty(disp)
                    faltantes.append(f"{ln.mp.nombre}: req {req_fmt} / stock {disp_fmt}")
            
            if faltantes: 
                raise forms.ValidationError(
                    f"Stock insuficiente en {sucursal.nombre} → " + "; ".join(faltantes)
                )
        return c

# =========================
#  Ventas
# =========================
class VentaForm(forms.ModelForm):
    confirmar_y_consumir = forms.BooleanField(required=False, label="Confirmar venta y consumir lotes (FEFO)")
    
    class Meta:
        model = Venta
        fields = ["sucursal", "nota", "confirmar_y_consumir"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None); super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            suscripcion = user.suscripcion
            self.fields['sucursal'].queryset = Sucursal.objects.filter(
                suscripcion=suscripcion, 
                activa=True
            )
            sucursal_principal = self.fields['sucursal'].queryset.filter(es_principal=True).first()
            if sucursal_principal:
                self.fields['sucursal'].initial = sucursal_principal
            elif self.fields['sucursal'].queryset.exists():
                self.fields['sucursal'].initial = self.fields['sucursal'].queryset.first()

    def save(self, commit=True, user=None):
        instancia = super().save(commit=False)
        if user and user.suscripcion:
            instancia.suscripcion = user.suscripcion
        if commit: instancia.save()
        return instancia

class VentaLineaForm(forms.ModelForm):
    cantidad = SmartDecimalField(min_value=Decimal("0.1")) 
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.suscripcion:
            self.fields['producto'].queryset = Producto.objects.filter(suscripcion=user.suscripcion, activo=True)
    class Meta:
        model = VentaLinea
        fields = ("producto", "cantidad")

class VentaLineaBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean(); at_least_one = False; productos = {} 
        for form in self.forms:
            if not getattr(form, "cleaned_data", None): continue
            if form.cleaned_data.get("DELETE"): continue
            prod = form.cleaned_data.get("producto"); qty = form.cleaned_data.get("cantidad")
            if not prod and not qty: continue
            at_least_one = True
            if qty and qty <= 0: form.add_error("cantidad", "La cantidad debe ser > 0.")
            if prod in productos: form.add_error("producto", "Producto repetido en otra línea. Combínalas.")
            productos[prod] = True
        if not at_least_one:
            raise forms.ValidationError("La venta debe tener al menos una línea.")

VentaLineaFormSet = inlineformset_factory(Venta, VentaLinea, form=VentaLineaForm, formset=VentaLineaBaseFormSet, extra=2, can_delete=True)


# ============================================================
# FORMULARIOS DEL WIZARD Y WMS (¡NUEVOS!)
# ============================================================

class SuscripcionConfigForm(forms.ModelForm):
    """
    Formulario para el Paso 1 del Wizard: Configurar Nombre de Empresa.
    """
    nombre_empresa = forms.CharField(label="Nombre de tu Empresa (Fantasía)", required=True)
    class Meta:
        model = SuscripcionCliente
        fields = ["nombre_empresa"]

class SucursalForm(forms.ModelForm):
    """
    Formulario para crear/editar Bodegas (Sucursales).
    Usado en el Paso 2 del Wizard y en el CRUD de Bodegas.
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Capturamos el user
        super().__init__(*args, **kwargs)

    class Meta:
        model = Sucursal
        fields = ["nombre", "direccion"]
    
    def clean_nombre(self):
        # Validación de Límite de Plan
        nombre = self.cleaned_data.get("nombre")
        if self.user and self.user.suscripcion and not self.instance.pk: # Solo al crear
            suscripcion = self.user.suscripcion
            if not suscripcion.puede_crear_sucursal():
                raise forms.ValidationError(
                    f"Tu plan ({suscripcion.get_plan_actual_display()}) no permite crear más bodegas."
                )
        return nombre

class UbicacionForm(forms.ModelForm):
    """
    Formulario para crear/editar Ubicaciones (Racks).
    Usado en el Paso 3 del Wizard y en el CRUD de Ubicaciones.
    """
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and self.user.suscripcion:
            suscripcion = self.user.suscripcion
            
            # 1. Filtramos el queryset SÍ o SÍ
            sucursal_qs = Sucursal.objects.filter(
                suscripcion=suscripcion, activa=True
            )
            self.fields['sucursal'].queryset = sucursal_qs
            
            # 2. Comprobamos el plan para la UI
            plan = suscripcion.plan_actual
            if plan == SuscripcionCliente.PLAN_ESENCIAL or plan == SuscripcionCliente.PLAN_TRAZABILIDAD:
                # En planes de 1 sola bodega, la pre-seleccionamos y ocultamos
                if sucursal_qs.exists():
                    self.fields['sucursal'].initial = sucursal_qs.first()
                    self.fields['sucursal'].widget = forms.HiddenInput()
            else:
                # En plan Multi-Sucursal, mostramos el selector
                # pero pre-seleccionamos la principal si existe
                suc_principal = sucursal_qs.filter(es_principal=True).first()
                if suc_principal:
                    self.fields['sucursal'].initial = suc_principal
                elif sucursal_qs.exists():
                    self.fields['sucursal'].initial = sucursal_qs.first()

    class Meta:
        model = Ubicacion
        fields = ["sucursal", "nombre"] 

    def clean(self):
        cleaned_data = super().clean()
        sucursal = cleaned_data.get("sucursal")
        
        # Si el campo estaba oculto, 'sucursal' puede estar None
        # Debemos re-asignarlo desde el 'initial' o 'queryset'
        if not sucursal and self.user and self.user.suscripcion:
            plan = self.user.suscripcion.plan_actual
            if plan == SuscripcionCliente.PLAN_ESENCIAL or plan == SuscripcionCliente.PLAN_TRAZABILIDAD:
                sucursal_qs = self.fields['sucursal'].queryset
                if sucursal_qs.exists():
                    cleaned_data['sucursal'] = sucursal_qs.first()
                    sucursal = cleaned_data['sucursal']

        if not sucursal:
            # Si AÚN no hay sucursal, es un error real
            raise forms.ValidationError("Debe seleccionar una bodega.")

        # Ahora validamos los límites del plan
        if self.user and self.user.suscripcion and sucursal and not self.instance.pk: # Solo al crear
            suscripcion = self.user.suscripcion
            if not suscripcion.puede_crear_ubicacion(sucursal):
                raise forms.ValidationError(
                    f"Tu plan ({suscripcion.get_plan_actual_display()}) no permite crear más ubicaciones en esta bodega."
                )
        return cleaned_data


# =========================
#  Formularios de Carga de Archivos
# =========================
class UploadFileForm(forms.Form):
    file = forms.FileField(label="Archivo CSV/Excel", help_text="Sube un archivo con columnas 'fecha' y 'valor'")

class UploadInvoiceForm(forms.Form):
    invoice_file = forms.FileField(label="Subir factura (imagen o PDF)", widget=forms.ClearableFileInput(attrs={'class': '...'}))