from django.dispatch import receiver
from django.db.models.signals import post_save
from allauth.account.signals import user_signed_up
from django.contrib.auth.models import Group, User # Importa tu User

@receiver(user_signed_up)
def handle_social_signup(request, user, **kwargs):
    """
    Se ejecuta justo después de que un usuario se registra
    usando una red social (Google).
    """
    user.is_staff = True  # Permitirle tener permisos
    try:
        # Buscamos el grupo "Gerente" (creado por tu migración)
        gerente_group = Group.objects.get(name='Gerente')
        user.groups.add(gerente_group)
    except Group.DoesNotExist:
        # Manejar error si el grupo no existe (aunque no debería pasar)
        print("ADVERTENCIA: El grupo 'Gerente' no existe. El usuario no tendrá permisos.")
        pass
    user.save()