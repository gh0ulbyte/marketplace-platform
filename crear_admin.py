"""
Script para crear un superusuario de forma interactiva
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mandale_project.settings')
django.setup()

from api.models import User

print("=" * 50)
print("CREAR SUPERUSUARIO - mandale")
print("=" * 50)
print()

email = input("Email: ")
nombre = input("Nombre completo: ")
username = input("Nombre de usuario: ")

# Verificar si el usuario ya existe
if User.objects.filter(email=email).exists():
    print(f"\n❌ Error: Ya existe un usuario con el email {email}")
    exit()

if User.objects.filter(username=username).exists():
    print(f"\n❌ Error: Ya existe un usuario con el username {username}")
    exit()

print("\n⚠️  IMPORTANTE: Escribe la contraseña (no se mostrará en pantalla)")
print("   Escribe la misma contraseña dos veces exactamente igual")
print()

password1 = input("Contraseña: ")
password2 = input("Contraseña (confirmar): ")

if password1 != password2:
    print("\n❌ Error: Las contraseñas no coinciden")
    exit()

if not password1 or len(password1) < 8:
    print("\n❌ Error: La contraseña debe tener al menos 8 caracteres")
    exit()

try:
    user = User.objects.create_superuser(
        email=email,
        username=username,
        nombre=nombre,
        password=password1
    )
    print("\n✅ ¡Superusuario creado exitosamente!")
    print(f"   Email: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   Nombre: {user.nombre}")
    print("\n🔐 Ahora puedes acceder a:")
    print("   http://localhost:8000/admin-panel/")
    print("   http://localhost:8000/admin/")
except Exception as e:
    print(f"\n❌ Error al crear el usuario: {e}")
