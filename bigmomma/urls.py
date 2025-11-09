# bigmomma/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from inventario import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    # Esto activa todas las URLs de allauth (login, logout, google, etc.)
    path('accounts/', include('allauth.urls')),
    # home

    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
    # incluye TODAS las rutas del app inventario (mp, kardex, producción, etc.)
    path("", include(("inventario.urls", "inventario"))),
    path('accounts/', include('django.contrib.auth.urls')),
    
]
