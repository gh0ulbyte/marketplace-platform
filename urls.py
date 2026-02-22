"""
URL configuration for mandale project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from api import admin_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Login para admin panel
    path('accounts/login/', admin_views.admin_login_view, name='admin_login'),
    
    # Panel de administración personalizado
    path('admin-panel/', admin_views.admin_panel, name='admin_panel'),
    path('admin-panel/productos/', admin_views.gestionar_productos, name='gestionar_productos'),
    path('admin-panel/comisiones/', admin_views.gestionar_comisiones, name='gestionar_comisiones'),
    path('admin-panel/estadisticas/', admin_views.estadisticas, name='estadisticas'),
    path('admin-panel/producto/<int:producto_id>/cambiar-estado/', admin_views.cambiar_estado_producto, name='cambiar_estado_producto'),
    
    # Páginas públicas
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index.html', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login'),
    path('registro.html', TemplateView.as_view(template_name='registro.html'), name='registro'),
    path('publicar-producto.html', TemplateView.as_view(template_name='publicar-producto.html'), name='publicar'),
    path('mi-pagina.html', TemplateView.as_view(template_name='mi-pagina.html'), name='mi_pagina'),
    path('perfil.html', TemplateView.as_view(template_name='perfil.html'), name='perfil'),
    path('producto-detalle.html', TemplateView.as_view(template_name='producto-detalle.html'), name='producto_detalle'),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
