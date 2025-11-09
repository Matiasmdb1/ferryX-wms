# bigmomma/urls.py
from django.contrib import admin
from django.urls import path, include  # <-- ¡Asegúrate de que 'include' esté aquí!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ¡¡ESTA ES LA ÚNICA LÍNEA QUE NECESITAS!! ---
    # Le dice a Django: "Deja que 'allauth' maneje TODO
    # lo que empiece con /accounts/ (login, logout, signup, google, etc.)"
    path('accounts/', include('allauth.urls')),
    
    # --- (BORRAMOS TODAS LAS LÍNEAS ANTIGUAS DE 'accounts/') ---
    
    # Esta línea carga todas las URLs de tu app (panel, ventas, etc.)
    # ¡PERO LA CAMBIAMOS PARA QUE NO INCLUYA 'accounts/'!
    path('', include('inventario.urls', namespace='inventario')),
]