from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, ProductImage, Comision


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nombre', 'telefono', 'fecha_creacion', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'fecha_creacion')
    search_fields = ('email', 'nombre')
    readonly_fields = ('fecha_creacion',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Personal', {'fields': ('nombre', 'telefono')}),
        ('Dirección', {'fields': ('calle', 'ciudad', 'provincia', 'codigo_postal')}),
        ('Billeteras', {'fields': (
            'mercadopago_activa', 'mercadopago_cuenta',
            'lemon_activa', 'lemon_cuenta',
            'brubank_activa', 'brubank_cuenta'
        )}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Solo superusuarios pueden ver otros superusuarios
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'vendedor', 'precio_formateado', 'categoria', 'estado', 'fecha_publicacion', 'visitas')
    list_filter = ('estado', 'categoria', 'condicion', 'fecha_publicacion')
    search_fields = ('titulo', 'descripcion', 'vendedor__email')
    readonly_fields = ('fecha_publicacion', 'visitas')
    list_editable = ('estado',)
    actions = ['aprobar_productos', 'pausar_productos', 'eliminar_productos']
    
    def precio_formateado(self, obj):
        return f"${obj.precio:,.2f}"
    precio_formateado.short_description = 'Precio'
    
    
    def aprobar_productos(self, request, queryset):
        queryset.update(estado='Activo')
        self.message_user(request, f'{queryset.count()} productos aprobados.')
    aprobar_productos.short_description = 'Aprobar productos seleccionados'
    
    def pausar_productos(self, request, queryset):
        queryset.update(estado='Pausado')
        self.message_user(request, f'{queryset.count()} productos pausados.')
    pausar_productos.short_description = 'Pausar productos seleccionados'
    
    def eliminar_productos(self, request, queryset):
        queryset.update(estado='Eliminado')
        self.message_user(request, f'{queryset.count()} productos eliminados.')
    eliminar_productos.short_description = 'Eliminar productos seleccionados'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'fecha_subida')
    list_filter = ('fecha_subida',)


@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'porcentaje', 'activa', 'fecha_actualizacion')
    list_filter = ('activa', 'fecha_creacion')
    search_fields = ('categoria',)
    list_editable = ('porcentaje', 'activa')
