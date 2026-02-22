from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Product, ProductImage, Order, Rating, Question, Offer, Message,
    Carrier, Shipment, TrackingEvent
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'nombre', 'password', 'password2', 'telefono', 'username')
        extra_kwargs = {
            'email': {'required': True},
            'nombre': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        
        # Obtener username, usar email si no se proporciona
        username = validated_data.get('username', validated_data['email'])
        
        # Si el username ya existe, generar uno único
        if User.objects.filter(username=username).exists():
            import random
            base_username = username.split('@')[0] if '@' in username else username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{random.randint(1000, 9999)}"
        
        user = User.objects.create_user(
            email=validated_data['email'],
            username=username,
            nombre=validated_data['nombre'],
            password=validated_data['password'],
            telefono=validated_data.get('telefono', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    is_superuser = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    reputacion = serializers.SerializerMethodField()
    total_calificaciones = serializers.SerializerMethodField()
    
    def get_is_superuser(self, obj):
        return bool(obj.is_superuser)
    
    def get_is_staff(self, obj):
        return bool(obj.is_staff)
    
    def get_reputacion(self, obj):
        return obj.calcular_reputacion()
    
    def get_total_calificaciones(self, obj):
        return obj.total_calificaciones()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'nombre', 'username', 'telefono',
            'calle', 'ciudad', 'provincia', 'codigo_postal', 'fecha_creacion',
            'mercadopago_activa', 'mercadopago_cuenta',
            'lemon_activa', 'lemon_cuenta',
            'brubank_activa', 'brubank_cuenta',
            'nombre_tienda', 'banner_imagen',
            'is_superuser', 'is_staff', 'reputacion', 'total_calificaciones',
        )
        read_only_fields = (
            'id', 'fecha_creacion', 'is_superuser', 'is_staff',
            'reputacion', 'total_calificaciones',
        )


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'imagen', 'fecha_subida')


class ProductSerializer(serializers.ModelSerializer):
    vendedor = UserSerializer(read_only=True)
    vendedor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='vendedor',
        write_only=True,
        required=False,
    )
    imagenes = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ('id', 'titulo', 'descripcion', 'precio', 'categoria', 
                  'condicion', 'stock', 'envio_gratis', 'vendedor', 'vendedor_id',
                  'estado', 'fecha_publicacion', 'visitas', 'imagenes',
                  'peso_kg', 'alto_cm', 'ancho_cm', 'largo_cm')
        read_only_fields = ('id', 'fecha_publicacion', 'visitas', 'vendedor')
    
    def create(self, validated_data):
        # El vendedor se asigna automáticamente desde el request
        validated_data.pop('vendedor_id', None)
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar productos"""
    vendedor_nombre = serializers.CharField(source='vendedor.nombre', read_only=True)
    imagenes = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ('id', 'titulo', 'precio', 'categoria', 'condicion', 
                  'envio_gratis', 'vendedor_nombre', 'estado', 
                  'fecha_publicacion', 'visitas', 'imagenes')


class WalletSerializer(serializers.Serializer):
    """Serializer para gestionar billeteras"""
    tipo = serializers.ChoiceField(choices=['mercadopago', 'lemon', 'brubank'])
    cuenta = serializers.CharField(max_length=200)


class PaymentSerializer(serializers.Serializer):
    """Serializer para procesar pagos"""
    tipo = serializers.ChoiceField(choices=['mercadopago', 'lemon', 'brubank'])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    producto_id = serializers.IntegerField(required=False)
    descripcion = serializers.CharField(max_length=500, required=False)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer para órdenes de compra"""
    comprador = UserSerializer(read_only=True)
    vendedor = UserSerializer(read_only=True)
    producto = ProductSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='producto',
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = ('id', 'comprador', 'vendedor', 'producto', 'producto_id', 'cantidad',
                  'precio_unitario', 'precio_total', 'metodo_pago', 'estado',
                  'direccion_entrega', 'fecha_creacion', 'fecha_actualizacion', 'transaccion_id')
        read_only_fields = ('id', 'comprador', 'vendedor', 'precio_total', 'fecha_creacion', 'fecha_actualizacion')


class RatingSerializer(serializers.ModelSerializer):
    """Serializer para calificaciones"""
    calificador = UserSerializer(read_only=True)
    calificado = UserSerializer(read_only=True)
    orden_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source='orden',
        write_only=True
    )
    
    class Meta:
        model = Rating
        fields = ('id', 'calificador', 'calificado', 'orden', 'orden_id', 'estrellas',
                  'comentario', 'fecha_creacion')
        read_only_fields = ('id', 'calificador', 'calificado', 'fecha_creacion')


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer para preguntas sobre productos"""
    usuario = UserSerializer(read_only=True)
    respondida_por = UserSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='producto',
        write_only=True
    )
    
    class Meta:
        model = Question
        fields = ('id', 'producto', 'producto_id', 'usuario', 'pregunta', 'respuesta',
                  'respondida_por', 'fecha_pregunta', 'fecha_respuesta')
        read_only_fields = ('id', 'usuario', 'respondida_por', 'fecha_pregunta', 'fecha_respuesta')


class OfferSerializer(serializers.ModelSerializer):
    """Serializer para ofertas de precio"""
    comprador = UserSerializer(read_only=True)
    producto = ProductSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='producto',
        write_only=True
    )
    
    class Meta:
        model = Offer
        fields = ('id', 'producto', 'producto_id', 'comprador', 'precio_ofertado',
                  'mensaje', 'estado', 'fecha_creacion', 'fecha_respuesta')
        read_only_fields = ('id', 'comprador', 'estado', 'fecha_creacion', 'fecha_respuesta')


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajería"""
    remitente = UserSerializer(read_only=True)
    destinatario = UserSerializer(read_only=True)
    orden_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source='orden',
        write_only=True,
        required=False,
        allow_null=True
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='destinatario',
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = ('id', 'orden', 'orden_id', 'remitente', 'destinatario', 'destinatario_id',
                  'asunto', 'mensaje', 'leido', 'fecha_envio')
        read_only_fields = ('id', 'remitente', 'fecha_envio')


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ('id', 'codigo', 'nombre', 'activo')


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = ('id', 'estado', 'descripcion', 'fecha_evento')


class ShipmentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    carrier = CarrierSerializer(read_only=True)
    carrier_id = serializers.PrimaryKeyRelatedField(
        queryset=Carrier.objects.all(),
        source='carrier',
        write_only=True,
        required=False,
        allow_null=True
    )
    tracking = TrackingEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shipment
        fields = (
            'id', 'order', 'carrier', 'carrier_id', 'costo', 'moneda',
            'estado', 'tracking_number', 'tracking_url', 'etiqueta_url',
            'dias_estimados', 'proveedor_envio_id', 'metadata',
            'fecha_creacion', 'fecha_actualizacion', 'tracking'
        )
        read_only_fields = ('id', 'fecha_creacion', 'fecha_actualizacion')


class ShippingQuoteSerializer(serializers.Serializer):
    """Serializer para cotizar envíos"""
    producto_id = serializers.IntegerField(required=False)
    cantidad = serializers.IntegerField(required=False, default=1, min_value=1)
    origen_cp = serializers.CharField(max_length=10)
    destino_cp = serializers.CharField(max_length=10)
    peso_kg = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    alto_cm = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    ancho_cm = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    largo_cm = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
