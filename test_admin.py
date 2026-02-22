"""
Script para verificar y crear superusuario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mandale_project.settings')
django.setup()

from api.models import User

print("=" * 50)
print("VERIFICAR/CREAR SUPERUSUARIO")
print("=" * 50)
print()

email = input("Email del usuario a verificar/crear: ")

try:
    user = User.objects.get(email=email)
    print(f"\n✅ Usuario encontrado: {user.email}")
    print(f"   Nombre: {user.nombre}")
    print(f"   Es superusuario: {user.is_superuser}")
    print(f"   Es staff: {user.is_staff}")
    print(f"   Está activo: {user.is_active}")
    
    if not user.is_superuser:
        respuesta = input("\n¿Quieres hacerlo superusuario? (s/n): ")
        if respuesta.lower() == 's':
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print("✅ Usuario convertido a superusuario")
        else:
            print("❌ No se modificó el usuario")
    else:
        print("\n✅ El usuario ya es superusuario")
        
except User.DoesNotExist:
    print(f"\n❌ No existe un usuario con el email {email}")
    respuesta = input("¿Quieres crearlo como superusuario? (s/n): ")
    if respuesta.lower() == 's':
        nombre = input("Nombre: ")
        username = input("Username: ")
        password = input("Contraseña: ")
        
        user = User.objects.create_superuser(
            email=email,
            username=username,
            nombre=nombre,
            password=password
        )
        print(f"\n✅ Superusuario creado: {user.email}")
