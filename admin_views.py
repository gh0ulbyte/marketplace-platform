from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Product, User, Comision


def is_superuser(user):
    """Verifica que el usuario sea superusuario"""
    return user.is_authenticated and user.is_superuser


@login_required
def admin_login_view(request):
    """Vista de login para el panel de administración"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password) and user.is_superuser:
                    auth_login(request, user)
                    next_url = request.GET.get('next', '/admin-panel/')
                    return redirect(next_url)
                else:
                    return render(request, 'admin_login.html', {
                        'error': 'Credenciales inválidas o no tienes permisos de administrador'
                    })
            except User.DoesNotExist:
                return render(request, 'admin_login.html', {
                    'error': 'Usuario no encontrado'
                })
    
    return render(request, 'admin_login.html')


@user_passes_test(is_superuser)
def admin_panel(request):
    """Panel principal de administración - Backend completo"""
    user = request.user
    
    # Estadísticas generales
    total_productos = Product.objects.count()
    productos_activos = Product.objects.filter(estado='Activo').count()
    productos_pausados = Product.objects.filter(estado='Pausado').count()
    productos_vendidos = Product.objects.filter(estado='Vendido').count()
    
    total_usuarios = User.objects.count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    
    # Productos recientes
    productos_recientes = Product.objects.select_related('vendedor').order_by('-fecha_publicacion')[:10]
    
    # Productos pendientes de revisión (nuevos)
    productos_pendientes = Product.objects.filter(
        estado='Activo',
        fecha_publicacion__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Estadísticas por categoría
    productos_por_categoria = Product.objects.values('categoria').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # Comisiones
    comisiones = Comision.objects.filter(activa=True).order_by('categoria')
    
    # ========== MÉTRICAS FINANCIERAS ==========
    
    # Valor total de productos activos
    valor_total_activos = Product.objects.filter(estado='Activo').aggregate(
        total=Sum('precio')
    )['total'] or 0
    
    # Valor de productos vendidos
    valor_vendidos = Product.objects.filter(estado='Vendido').aggregate(
        total=Sum('precio')
    )['total'] or 0
    
    # Calcular comisiones potenciales (si todos los activos se vendieran)
    comisiones_potenciales = 0
    for producto in Product.objects.filter(estado='Activo').select_related():
        try:
            comision = Comision.objects.get(categoria=producto.categoria, activa=True)
            comisiones_potenciales += comision.calcular_comision(producto.precio)
        except Comision.DoesNotExist:
            pass
    
    # Comisiones de productos vendidos
    comisiones_reales = 0
    for producto in Product.objects.filter(estado='Vendido').select_related():
        try:
            comision = Comision.objects.get(categoria=producto.categoria, activa=True)
            comisiones_reales += comision.calcular_comision(producto.precio)
        except Comision.DoesNotExist:
            pass
    
    # Productos vendidos este mes
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    productos_vendidos_mes = Product.objects.filter(
        estado='Vendido',
        fecha_publicacion__gte=inicio_mes
    ).count()
    
    valor_vendido_mes = Product.objects.filter(
        estado='Vendido',
        fecha_publicacion__gte=inicio_mes
    ).aggregate(total=Sum('precio'))['total'] or 0
    
    comisiones_mes = 0
    for producto in Product.objects.filter(estado='Vendido', fecha_publicacion__gte=inicio_mes):
        try:
            comision = Comision.objects.get(categoria=producto.categoria, activa=True)
            comisiones_mes += comision.calcular_comision(producto.precio)
        except Comision.DoesNotExist:
            pass
    
    # Top categorías por valor
    categorias_valor = []
    for cat_data in Product.objects.filter(estado='Activo').values('categoria').annotate(
        valor_total=Sum('precio'),
        cantidad=Count('id')
    ).order_by('-valor_total')[:5]:
        # Calcular comisión potencial para cada categoría
        try:
            comision = Comision.objects.get(categoria=cat_data['categoria'], activa=True)
            cat_data['comision_potencial'] = (cat_data['valor_total'] * comision.porcentaje) / 100
        except Comision.DoesNotExist:
            cat_data['comision_potencial'] = 0
        categorias_valor.append(cat_data)
    
    context = {
        'user': user,  # Pasar el usuario al template
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'productos_pausados': productos_pausados,
        'productos_vendidos': productos_vendidos,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'productos_pendientes': productos_pendientes,
        'productos_recientes': productos_recientes,
        'productos_por_categoria': productos_por_categoria,
        'comisiones': comisiones,
        # Métricas financieras
        'valor_total_activos': valor_total_activos,
        'valor_vendidos': valor_vendidos,
        'comisiones_potenciales': comisiones_potenciales,
        'comisiones_reales': comisiones_reales,
        'productos_vendidos_mes': productos_vendidos_mes,
        'valor_vendido_mes': valor_vendido_mes,
        'comisiones_mes': comisiones_mes,
        'categorias_valor': categorias_valor,
    }
    
    return render(request, 'admin_panel.html', context)


@user_passes_test(is_superuser)
def gestionar_productos(request):
    """Gestión de productos"""
    estado = request.GET.get('estado', 'todos')
    categoria = request.GET.get('categoria', '')
    busqueda = request.GET.get('busqueda', '')
    
    productos = Product.objects.select_related('vendedor').all()
    
    if estado != 'todos':
        productos = productos.filter(estado=estado)
    
    if categoria:
        productos = productos.filter(categoria=categoria)
    
    if busqueda:
        productos = productos.filter(
            Q(titulo__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(vendedor__email__icontains=busqueda)
        )
    
    productos = productos.order_by('-fecha_publicacion')
    
    categorias = Product.objects.values_list('categoria', flat=True).distinct()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'estado_actual': estado,
        'categoria_actual': categoria,
        'busqueda_actual': busqueda,
    }
    
    return render(request, 'admin_productos.html', context)


@user_passes_test(is_superuser)
def gestionar_comisiones(request):
    """Gestión de comisiones"""
    comisiones = Comision.objects.all().order_by('categoria')
    
    # Obtener todas las categorías de productos para crear comisiones faltantes
    categorias_productos = Product.objects.values_list('categoria', flat=True).distinct()
    categorias_con_comision = Comision.objects.values_list('categoria', flat=True)
    categorias_sin_comision = set(categorias_productos) - set(categorias_con_comision)
    
    if request.method == 'POST':
        categoria = request.POST.get('categoria')
        porcentaje = request.POST.get('porcentaje')
        accion = request.POST.get('accion')
        
        if accion == 'crear' and categoria and porcentaje:
            Comision.objects.create(
                categoria=categoria,
                porcentaje=float(porcentaje),
                activa=True
            )
            return redirect('gestionar_comisiones')
        
        elif accion == 'actualizar':
            comision_id = request.POST.get('comision_id')
            try:
                comision = Comision.objects.get(id=comision_id)
                if 'porcentaje' in request.POST:
                    comision.porcentaje = float(request.POST.get('porcentaje'))
                if 'activa' in request.POST:
                    comision.activa = request.POST.get('activa') == 'on'
                comision.save()
                return redirect('gestionar_comisiones')
            except Comision.DoesNotExist:
                pass
    
    context = {
        'comisiones': comisiones,
        'categorias_sin_comision': categorias_sin_comision,
    }
    
    return render(request, 'admin_comisiones.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def cambiar_estado_producto(request, producto_id):
    """Cambiar estado de un producto (AJAX)"""
    try:
        producto = Product.objects.get(id=producto_id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in ['Activo', 'Pausado', 'Vendido', 'Eliminado']:
            producto.estado = nuevo_estado
            producto.save()
            return JsonResponse({'success': True, 'estado': nuevo_estado})
        else:
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'})


@user_passes_test(is_superuser)
def estadisticas(request):
    """Página de estadísticas"""
    
    # Estadísticas de productos
    productos_por_estado = Product.objects.values('estado').annotate(
        total=Count('id')
    )
    
    productos_por_categoria = Product.objects.values('categoria').annotate(
        total=Count('id'),
        total_activos=Count('id', filter=Q(estado='Activo'))
    ).order_by('-total')
    
    # Productos por mes
    productos_por_mes = Product.objects.extra(
        select={'mes': "strftime('%%Y-%%m', fecha_publicacion)"}
    ).values('mes').annotate(total=Count('id')).order_by('mes')
    
    # Usuarios más activos
    usuarios_activos = User.objects.annotate(
        productos_count=Count('productos_publicados')
    ).filter(productos_count__gt=0).order_by('-productos_count')[:10]
    
    # Valor total de productos activos
    valor_total = Product.objects.filter(estado='Activo').aggregate(
        total=Sum('precio')
    )['total'] or 0
    
    context = {
        'productos_por_estado': productos_por_estado,
        'productos_por_categoria': productos_por_categoria,
        'productos_por_mes': productos_por_mes,
        'usuarios_activos': usuarios_activos,
        'valor_total': valor_total,
    }
    
    return render(request, 'admin_estadisticas.html', context)
