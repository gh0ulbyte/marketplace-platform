from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login as auth_login
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from .models import (
    User, Product, ProductImage, Order, Rating, Question, Offer, Message,
    Carrier, Shipment, TrackingEvent
)
from .serializers import (
    UserRegistrationSerializer, UserSerializer, ProductSerializer,
    ProductListSerializer, WalletSerializer, PaymentSerializer,
    OrderSerializer, RatingSerializer, QuestionSerializer, OfferSerializer, MessageSerializer,
    CarrierSerializer, ShipmentSerializer, TrackingEventSerializer, ShippingQuoteSerializer
)


# ==================== AUTENTICACIÓN ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Registro de nuevo usuario"""
    # Crear una copia mutable de los datos
    data = request.data.copy()
    
    # Verificar si el email ya existe
    email = data.get('email')
    if email:
        if User.objects.filter(email=email).exists():
            return Response(
                {'message': 'Este email ya está registrado. Por favor, usa otro email o inicia sesión.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Verificar si el username ya existe (si se proporciona)
    username = data.get('username') or email
    if username:
        if User.objects.filter(username=username).exists():
            # Si el username ya existe, generar uno único
            import random
            base_username = username.split('@')[0] if '@' in username else username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{random.randint(1000, 9999)}"
            data['username'] = username
    
    serializer = UserRegistrationSerializer(data=data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Usuario registrado exitosamente',
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'message': f'Error al crear la cuenta: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Mejorar mensajes de error
    error_messages = []
    for field, errors in serializer.errors.items():
        if field == 'email':
            error_messages.append('Este email ya está registrado o no es válido.')
        elif field == 'password':
            if 'password' in str(errors).lower():
                error_messages.append('La contraseña no cumple con los requisitos de seguridad.')
            else:
                error_messages.append(f'Error en la contraseña: {errors[0]}')
        elif field == 'password2':
            error_messages.append('Las contraseñas no coinciden.')
        else:
            error_messages.append(f'{field}: {errors[0]}')
    
    return Response(
        {'message': ' '.join(error_messages) if error_messages else 'Error al crear la cuenta'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login de usuario"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'message': 'Por favor ingresa email y contraseña'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'message': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if user.check_password(password):
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        
        # Si es superusuario, crear sesión de Django para acceso al admin panel
        if user.is_superuser:
            auth_login(request, user)
        
        # Determinar redirección basada en si es superusuario
        # FORZAR que sea string para evitar problemas
        redirect_url = '/admin-panel/' if user.is_superuser else '/'
        
        # Crear respuesta con toda la información necesaria
        response_data = {
            'message': 'Login exitoso',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data,
            'redirect_to': str(redirect_url),  # FORZAR a string
            'is_superuser': True if user.is_superuser else False,  # FORZAR booleano explícito
            'is_staff': True if user.is_staff else False
        }
        
        # Log para debugging
        print(f"🔐 LOGIN: {user.email} | is_superuser: {user.is_superuser} | redirect_to: {redirect_url}")
        
        return Response(response_data)
    else:
        return Response(
            {'message': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def get_profile(request):
    """Obtener o actualizar perfil del usuario autenticado"""
    try:
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'message': 'Usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Error en get_profile: {e}")
        return Response(
            {'message': f'Error al procesar el perfil: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """Cerrar sesión del usuario"""
    # Cerrar sesión de Django si el usuario está autenticado
    if request.user.is_authenticated:
        from django.contrib.auth import logout as django_logout
        django_logout(request)
    
    return Response({
        'message': 'Sesión cerrada exitosamente'
    }, status=status.HTTP_200_OK)


# ==================== PRODUCTOS ====================

class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar productos"""
    queryset = Product.objects.filter(estado='Activo')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Para aceptar archivos
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Product.objects.filter(estado='Activo')
        
        # Filtros
        categoria = self.request.query_params.get('categoria', None)
        busqueda = self.request.query_params.get('busqueda', None)
        ordenar_por = self.request.query_params.get('ordenar_por', 'fecha')  # fecha, visitas
        
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        if busqueda:
            queryset = queryset.filter(
                Q(titulo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
            )
        
        # Ordenamiento
        if ordenar_por == 'visitas':
            queryset = queryset.order_by('-visitas', '-fecha_publicacion')
        else:
            queryset = queryset.order_by('-fecha_publicacion')
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear producto con imágenes"""
        # Preparar datos del formulario
        data = request.data.copy()
        
        # Convertir tipos si vienen de FormData (vienen como strings)
        if 'precio' in data:
            try:
                data['precio'] = float(data['precio'])
            except (ValueError, TypeError):
                pass
        
        if 'stock' in data:
            try:
                data['stock'] = int(data['stock'])
            except (ValueError, TypeError):
                pass
        
        if 'envio_gratis' in data:
            # FormData envía 'true'/'false' como strings o como boolean
            if isinstance(data['envio_gratis'], str):
                data['envio_gratis'] = data['envio_gratis'].lower() in ('true', '1', 'on')
            else:
                data['envio_gratis'] = bool(data['envio_gratis'])
        
        # Crear el producto primero
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save(vendedor=request.user)
        
        # Procesar imágenes si se enviaron
        imagenes = request.FILES.getlist('imagenes')
        if imagenes:
            for imagen in imagenes[:5]:  # Máximo 5 imágenes
                ProductImage.objects.create(product=producto, imagen=imagen)
        
        # Obtener el serializer con las imágenes
        response_serializer = self.get_serializer(producto)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        serializer.save(vendedor=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.visitas += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_productos')
    def mis_productos(self, request):
        """Obtener productos del usuario autenticado"""
        try:
            print(f"🛍️ Mis productos - Usuario: {request.user.email}")
            productos = Product.objects.filter(vendedor=request.user).order_by('-fecha_publicacion')
            print(f"   Productos encontrados: {productos.count()}")
            serializer = ProductListSerializer(productos, many=True)
            print(f"   Datos serializados: {len(serializer.data)} productos")
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Error en mis_productos: {e}")
            return Response(
                {'message': f'Error al obtener productos: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.vendedor != request.user:
            return Response(
                {'message': 'No tienes permiso para editar este producto'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.vendedor != request.user:
            return Response(
                {'message': 'No tienes permiso para eliminar este producto'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.estado = 'Eliminado'
        instance.save()
        return Response({'message': 'Producto eliminado exitosamente'})


# ==================== PAGOS / BILLETERAS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conectar_billetera(request):
    """Conectar billetera virtual"""
    serializer = WalletSerializer(data=request.data)
    if serializer.is_valid():
        tipo = serializer.validated_data['tipo']
        cuenta = serializer.validated_data['cuenta']
        
        user = request.user
        if tipo == 'mercadopago':
            user.mercadopago_activa = True
            user.mercadopago_cuenta = cuenta
        elif tipo == 'lemon':
            user.lemon_activa = True
            user.lemon_cuenta = cuenta
        elif tipo == 'brubank':
            user.brubank_activa = True
            user.brubank_cuenta = cuenta
        
        user.save()
        return Response({
            'message': f'Billetera {tipo} conectada exitosamente',
            'billeteras': {
                'mercadopago': {'activa': user.mercadopago_activa, 'cuenta': user.mercadopago_cuenta},
                'lemon': {'activa': user.lemon_activa, 'cuenta': user.lemon_cuenta},
                'brubank': {'activa': user.brubank_activa, 'cuenta': user.brubank_cuenta},
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def desconectar_billetera(request):
    """Desconectar billetera virtual"""
    tipo = request.data.get('tipo')
    if tipo not in ['mercadopago', 'lemon', 'brubank']:
        return Response(
            {'message': 'Tipo de billetera no válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    if tipo == 'mercadopago':
        user.mercadopago_activa = False
        user.mercadopago_cuenta = ''
    elif tipo == 'lemon':
        user.lemon_activa = False
        user.lemon_cuenta = ''
    elif tipo == 'brubank':
        user.brubank_activa = False
        user.brubank_cuenta = ''
    
    user.save()
    return Response({
        'message': f'Billetera {tipo} desconectada',
        'billeteras': {
            'mercadopago': {'activa': user.mercadopago_activa, 'cuenta': user.mercadopago_cuenta},
            'lemon': {'activa': user.lemon_activa, 'cuenta': user.lemon_cuenta},
            'brubank': {'activa': user.brubank_activa, 'cuenta': user.brubank_cuenta},
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_billeteras(request):
    """Obtener billeteras del usuario"""
    user = request.user
    return Response({
        'mercadopago': {'activa': user.mercadopago_activa, 'cuenta': user.mercadopago_cuenta},
        'lemon': {'activa': user.lemon_activa, 'cuenta': user.lemon_cuenta},
        'brubank': {'activa': user.brubank_activa, 'cuenta': user.brubank_cuenta},
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def procesar_pago(request):
    """Procesar pago (simulado)"""
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        tipo = serializer.validated_data['tipo']
        monto = serializer.validated_data['monto']
        
        user = request.user
        # Verificar que la billetera esté conectada
        if tipo == 'mercadopago' and not user.mercadopago_activa:
            return Response(
                {'message': f'La billetera {tipo} no está conectada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif tipo == 'lemon' and not user.lemon_activa:
            return Response(
                {'message': f'La billetera {tipo} no está conectada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif tipo == 'brubank' and not user.brubank_activa:
            return Response(
                {'message': f'La billetera {tipo} no está conectada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simular procesamiento de pago
        import time
        time.sleep(0.5)  # Simular delay
        
        return Response({
            'message': 'Pago procesado exitosamente',
            'transaccion': {
                'id': f'{tipo.upper()}-{int(time.time())}',
                'tipo': tipo,
                'monto': str(monto),
                'estado': 'Completado',
                'fecha': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def metodos_disponibles(request):
    """Obtener métodos de pago disponibles"""
    return Response({
        'metodos': [
            {
                'id': 'mercadopago',
                'nombre': 'Mercado Pago',
                'descripcion': 'Paga con tu cuenta de Mercado Pago',
                'icono': '💳'
            },
            {
                'id': 'lemon',
                'nombre': 'Lemon',
                'descripcion': 'Paga con tu billetera Lemon',
                'icono': '🍋'
            },
            {
                'id': 'brubank',
                'nombre': 'Brubank',
                'descripcion': 'Paga con tu cuenta Brubank',
                'icono': '🏦'
            }
        ]
    })


# ==================== COMPRAS Y VENTAS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_orden(request):
    """Crear una orden de compra"""
    producto_id = request.data.get('producto_id')
    cantidad = int(request.data.get('cantidad', 1))
    metodo_pago = request.data.get('metodo_pago')
    direccion_entrega = request.data.get('direccion_entrega', '')
    
    try:
        producto = Product.objects.get(id=producto_id, estado='Activo')
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado o no disponible'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verificar stock
    if producto.stock < cantidad:
        return Response(
            {'message': f'Stock insuficiente. Disponible: {producto.stock}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # No permitir comprar tu propio producto
    if producto.vendedor == request.user:
        return Response(
            {'message': 'No puedes comprar tu propio producto'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar método de pago
    if metodo_pago == 'mercadopago' and not request.user.mercadopago_activa:
        return Response(
            {'message': 'Mercado Pago no está conectado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif metodo_pago == 'lemon' and not request.user.lemon_activa:
        return Response(
            {'message': 'Lemon no está conectado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif metodo_pago == 'brubank' and not request.user.brubank_activa:
        return Response(
            {'message': 'Brubank no está conectado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Crear orden
    orden = Order.objects.create(
        comprador=request.user,
        vendedor=producto.vendedor,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=producto.precio,
        metodo_pago=metodo_pago,
        direccion_entrega=direccion_entrega
    )
    
    # Reducir stock
    producto.stock -= cantidad
    if producto.stock == 0:
        producto.estado = 'Vendido'
    producto.save()
    
    serializer = OrderSerializer(orden)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_compras(request):
    """Obtener compras del usuario"""
    compras = Order.objects.filter(comprador=request.user).order_by('-fecha_creacion')
    serializer = OrderSerializer(compras, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_ventas(request):
    """Obtener ventas del usuario"""
    ventas = Order.objects.filter(vendedor=request.user).order_by('-fecha_creacion')
    serializer = OrderSerializer(ventas, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def actualizar_estado_orden(request, orden_id):
    """Actualizar estado de una orden (solo vendedor)"""
    try:
        orden = Order.objects.get(id=orden_id)
    except Order.DoesNotExist:
        return Response(
            {'message': 'Orden no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if orden.vendedor != request.user:
        return Response(
            {'message': 'No tienes permiso para actualizar esta orden'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    nuevo_estado = request.data.get('estado')
    if nuevo_estado not in dict(Order.ESTADO_CHOICES):
        return Response(
            {'message': 'Estado inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    orden.estado = nuevo_estado
    orden.save()
    
    serializer = OrderSerializer(orden)
    return Response(serializer.data)


# ==================== CALIFICACIONES ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_calificacion(request):
    """Crear una calificación"""
    orden_id = request.data.get('orden_id')
    estrellas = int(request.data.get('estrellas'))
    comentario = request.data.get('comentario', '')
    
    try:
        orden = Order.objects.get(id=orden_id)
    except Order.DoesNotExist:
        return Response(
            {'message': 'Orden no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Solo el comprador puede calificar
    if orden.comprador != request.user:
        return Response(
            {'message': 'Solo el comprador puede calificar esta orden'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Verificar que no haya calificado antes
    if Rating.objects.filter(calificador=request.user, orden=orden).exists():
        return Response(
            {'message': 'Ya calificaste esta orden'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Crear calificación
    rating = Rating.objects.create(
        calificador=request.user,
        calificado=orden.vendedor,
        orden=orden,
        estrellas=estrellas,
        comentario=comentario
    )
    
    serializer = RatingSerializer(rating)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def calificaciones_usuario(request, user_id):
    """Obtener calificaciones de un usuario"""
    try:
        usuario = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'message': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    calificaciones = Rating.objects.filter(calificado=usuario).order_by('-fecha_creacion')
    serializer = RatingSerializer(calificaciones, many=True)
    
    return Response({
        'calificaciones': serializer.data,
        'reputacion': usuario.calcular_reputacion(),
        'total': usuario.total_calificaciones()
    })


# ==================== PREGUNTAS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pregunta(request):
    """Crear una pregunta sobre un producto"""
    producto_id = request.data.get('producto_id')
    pregunta_texto = request.data.get('pregunta')
    
    try:
        producto = Product.objects.get(id=producto_id, estado='Activo')
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    pregunta = Question.objects.create(
        producto=producto,
        usuario=request.user,
        pregunta=pregunta_texto
    )
    
    serializer = QuestionSerializer(pregunta)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def preguntas_producto(request, producto_id):
    """Obtener preguntas de un producto"""
    try:
        producto = Product.objects.get(id=producto_id)
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    preguntas = Question.objects.filter(producto=producto).order_by('-fecha_pregunta')
    serializer = QuestionSerializer(preguntas, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def responder_pregunta(request, pregunta_id):
    """Responder una pregunta (solo el vendedor)"""
    respuesta_texto = request.data.get('respuesta')
    
    try:
        pregunta = Question.objects.get(id=pregunta_id)
    except Question.DoesNotExist:
        return Response(
            {'message': 'Pregunta no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Solo el vendedor puede responder
    if pregunta.producto.vendedor != request.user:
        return Response(
            {'message': 'Solo el vendedor puede responder esta pregunta'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from django.utils import timezone
    pregunta.respuesta = respuesta_texto
    pregunta.respondida_por = request.user
    pregunta.fecha_respuesta = timezone.now()
    pregunta.save()
    
    serializer = QuestionSerializer(pregunta)
    return Response(serializer.data)


# ==================== OFERTAS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_oferta(request):
    """Crear una oferta de precio"""
    producto_id = request.data.get('producto_id')
    precio_ofertado = float(request.data.get('precio_ofertado'))
    mensaje = request.data.get('mensaje', '')
    
    try:
        producto = Product.objects.get(id=producto_id, estado='Activo')
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # No permitir ofertar tu propio producto
    if producto.vendedor == request.user:
        return Response(
            {'message': 'No puedes ofertar tu propio producto'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # La oferta debe ser menor al precio
    if precio_ofertado >= float(producto.precio):
        return Response(
            {'message': 'La oferta debe ser menor al precio del producto'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    oferta = Offer.objects.create(
        producto=producto,
        comprador=request.user,
        precio_ofertado=precio_ofertado,
        mensaje=mensaje
    )
    
    serializer = OfferSerializer(oferta)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ofertas_producto(request, producto_id):
    """Obtener ofertas de un producto (solo vendedor)"""
    try:
        producto = Product.objects.get(id=producto_id)
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if producto.vendedor != request.user:
        return Response(
            {'message': 'Solo el vendedor puede ver las ofertas'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    ofertas = Offer.objects.filter(producto=producto).order_by('-fecha_creacion')
    serializer = OfferSerializer(ofertas, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def responder_oferta(request, oferta_id):
    """Aceptar o rechazar una oferta (solo vendedor)"""
    accion = request.data.get('accion')  # 'aceptar' o 'rechazar'
    
    try:
        oferta = Offer.objects.get(id=oferta_id)
    except Offer.DoesNotExist:
        return Response(
            {'message': 'Oferta no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if oferta.producto.vendedor != request.user:
        return Response(
            {'message': 'Solo el vendedor puede responder esta oferta'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if oferta.estado != 'Pendiente':
        return Response(
            {'message': 'Esta oferta ya fue respondida'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from django.utils import timezone
    if accion == 'aceptar':
        oferta.estado = 'Aceptada'
        # Actualizar precio del producto con el precio ofertado
        oferta.producto.precio = oferta.precio_ofertado
        oferta.producto.save()
    elif accion == 'rechazar':
        oferta.estado = 'Rechazada'
    else:
        return Response(
            {'message': 'Acción inválida. Use "aceptar" o "rechazar"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    oferta.fecha_respuesta = timezone.now()
    oferta.save()
    
    serializer = OfferSerializer(oferta)
    return Response(serializer.data)


# ==================== MENSAJERÍA ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_mensaje(request):
    """Enviar un mensaje"""
    destinatario_id = request.data.get('destinatario_id')
    mensaje_texto = request.data.get('mensaje')
    asunto = request.data.get('asunto', '')
    orden_id = request.data.get('orden_id', None)
    
    try:
        destinatario = User.objects.get(id=destinatario_id)
    except User.DoesNotExist:
        return Response(
            {'message': 'Destinatario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    orden = None
    if orden_id:
        try:
            orden = Order.objects.get(id=orden_id)
            # Verificar que el usuario esté relacionado con la orden
            if request.user != orden.comprador and request.user != orden.vendedor:
                return Response(
                    {'message': 'No tienes permiso para enviar mensajes sobre esta orden'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Order.DoesNotExist:
            pass
    
    mensaje = Message.objects.create(
        orden=orden,
        remitente=request.user,
        destinatario=destinatario,
        asunto=asunto,
        mensaje=mensaje_texto
    )
    
    serializer = MessageSerializer(mensaje)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_mensajes(request):
    """Obtener mensajes del usuario"""
    mensajes = Message.objects.filter(
        Q(remitente=request.user) | Q(destinatario=request.user)
    ).order_by('-fecha_envio')
    
    serializer = MessageSerializer(mensajes, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def marcar_mensaje_leido(request, mensaje_id):
    """Marcar un mensaje como leído"""
    try:
        mensaje = Message.objects.get(id=mensaje_id)
    except Message.DoesNotExist:
        return Response(
            {'message': 'Mensaje no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Solo el destinatario puede marcar como leído
    if mensaje.destinatario != request.user:
        return Response(
            {'message': 'No tienes permiso para marcar este mensaje'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    mensaje.leido = True
    mensaje.save()
    
    serializer = MessageSerializer(mensaje)
    return Response(serializer.data)


# ==================== ENVÍOS / LOGÍSTICA ====================

def _asegurar_proveedores_default():
    """Crea proveedores básicos si no existen"""
    if Carrier.objects.exists():
        return
    Carrier.objects.bulk_create([
        Carrier(codigo='envio_pack', nombre='EnvioPack', activo=True),
        Carrier(codigo='moova', nombre='Moova', activo=True),
        Carrier(codigo='andreani', nombre='Andreani', activo=False),
        Carrier(codigo='oca', nombre='OCA', activo=False),
    ])


def _get_shipping_data(product, cantidad, data):
    """Arma datos de envío a partir de producto o payload"""
    peso_kg = data.get('peso_kg') or product.peso_kg
    alto_cm = data.get('alto_cm') or product.alto_cm
    ancho_cm = data.get('ancho_cm') or product.ancho_cm
    largo_cm = data.get('largo_cm') or product.largo_cm
    
    if not peso_kg:
        return None, "Falta peso del producto para cotizar."
    
    return {
        'peso_kg': float(peso_kg) * int(cantidad),
        'alto_cm': float(alto_cm or 0),
        'ancho_cm': float(ancho_cm or 0),
        'largo_cm': float(largo_cm or 0),
    }, None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipping_quote(request):
    """Cotizar envíos con proveedores disponibles"""
    _asegurar_proveedores_default()
    
    serializer = ShippingQuoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad', 1)
    
    if not producto_id:
        return Response(
            {'message': 'producto_id es requerido para cotizar.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product = Product.objects.get(id=producto_id, estado='Activo')
    except Product.DoesNotExist:
        return Response(
            {'message': 'Producto no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    shipping_data, error = _get_shipping_data(product, cantidad, data)
    if error:
        return Response({'message': error}, status=status.HTTP_400_BAD_REQUEST)
    
    # Simulación de cotización. Aquí se integrará la API real del proveedor.
    carriers = Carrier.objects.filter(activo=True)
    opciones = []
    for idx, carrier in enumerate(carriers, start=1):
        base = 1200 + (shipping_data['peso_kg'] * 350)
        extra = 0 if product.envio_gratis else 0
        costo = round(base + (idx * 250) + extra, 2)
        opciones.append({
            'carrier_id': carrier.id,
            'carrier_codigo': carrier.codigo,
            'carrier_nombre': carrier.nombre,
            'costo': costo,
            'moneda': 'ARS',
            'dias_estimados': 2 + idx
        })
    
    return Response({
        'producto_id': product.id,
        'cantidad': cantidad,
        'origen_cp': data.get('origen_cp'),
        'destino_cp': data.get('destino_cp'),
        'opciones': opciones
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipping_create(request):
    """Crear envío asociado a una orden"""
    order_id = request.data.get('order_id')
    carrier_id = request.data.get('carrier_id')
    costo = request.data.get('costo')
    dias_estimados = request.data.get('dias_estimados')
    
    if not order_id or not carrier_id:
        return Response(
            {'message': 'order_id y carrier_id son requeridos.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'message': 'Orden no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Solo comprador o vendedor pueden crear el envío
    if request.user != order.comprador and request.user != order.vendedor:
        return Response({'message': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        carrier = Carrier.objects.get(id=carrier_id, activo=True)
    except Carrier.DoesNotExist:
        return Response({'message': 'Proveedor inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    
    shipment = Shipment.objects.create(
        order=order,
        carrier=carrier,
        costo=costo or None,
        dias_estimados=dias_estimados or None,
        estado='Creado'
    )
    
    serializer = ShipmentSerializer(shipment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def shipping_webhook(request):
    """Webhook para actualizar estados de envíos"""
    secret = getattr(settings, 'SHIPPING_WEBHOOK_SECRET', None)
    if secret:
        header_secret = request.headers.get('X-Webhook-Secret')
        if header_secret != secret:
            return Response({'message': 'Webhook no autorizado.'}, status=status.HTTP_403_FORBIDDEN)
    
    payload = request.data
    proveedor_envio_id = payload.get('proveedor_envio_id')
    tracking_number = payload.get('tracking_number')
    estado = payload.get('estado')
    descripcion = payload.get('descripcion')
    fecha_evento = payload.get('fecha_evento')
    
    shipment = None
    if proveedor_envio_id:
        shipment = Shipment.objects.filter(proveedor_envio_id=proveedor_envio_id).first()
    if not shipment and tracking_number:
        shipment = Shipment.objects.filter(tracking_number=tracking_number).first()
    
    if not shipment:
        return Response({'message': 'Envío no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    if estado:
        shipment.estado = estado
    if payload.get('tracking_url'):
        shipment.tracking_url = payload.get('tracking_url')
    if payload.get('etiqueta_url'):
        shipment.etiqueta_url = payload.get('etiqueta_url')
    if payload.get('tracking_number'):
        shipment.tracking_number = payload.get('tracking_number')
    shipment.metadata = payload
    shipment.save()
    
    if fecha_evento:
        try:
            evento_fecha = timezone.datetime.fromisoformat(fecha_evento)
        except ValueError:
            evento_fecha = timezone.now()
    else:
        evento_fecha = timezone.now()
    
    TrackingEvent.objects.create(
        shipment=shipment,
        estado=estado or 'Actualizado',
        descripcion=descripcion,
        fecha_evento=evento_fecha
    )
    
    return Response({'message': 'Webhook procesado correctamente.'})
