from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    """Modelo de usuario personalizado"""
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Personalización de la página
    nombre_tienda = models.CharField(max_length=200, blank=True, null=True, 
                                     help_text="Nombre personalizado para tu página/tienda. Si está vacío, se usará tu nombre de usuario.")
    banner_imagen = models.ImageField(
        upload_to='banners/',
        blank=True,
        null=True,
        help_text="Imagen de cabecera para tu página pública."
    )
    
    # Dirección
    calle = models.CharField(max_length=200, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    
    # Billeteras virtuales
    mercadopago_activa = models.BooleanField(default=False)
    mercadopago_cuenta = models.CharField(max_length=200, blank=True, null=True)
    
    lemon_activa = models.BooleanField(default=False)
    lemon_cuenta = models.CharField(max_length=200, blank=True, null=True)
    
    brubank_activa = models.BooleanField(default=False)
    brubank_cuenta = models.CharField(max_length=200, blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'username']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.email
    
    def calcular_reputacion(self):
        """Calcula la reputación promedio basada en las calificaciones recibidas"""
        calificaciones = self.calificaciones_recibidas.all()
        if not calificaciones.exists():
            return None
        promedio = calificaciones.aggregate(Avg('estrellas'))['estrellas__avg']
        return round(promedio, 2) if promedio else None
    
    def total_calificaciones(self):
        """Retorna el total de calificaciones recibidas"""
        return self.calificaciones_recibidas.count()


class Product(models.Model):
    """Modelo de producto"""
    CONDICION_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('Usado', 'Usado'),
        ('Reacondicionado', 'Reacondicionado'),
    ]
    
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Pausado', 'Pausado'),
        ('Vendido', 'Vendido'),
        ('Eliminado', 'Eliminado'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    categoria = models.CharField(max_length=100)
    condicion = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='Nuevo')
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=1)
    envio_gratis = models.BooleanField(default=False)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos_publicados')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activo')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    visitas = models.IntegerField(default=0)
    
    # Datos para cotizar envíos
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    alto_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ancho_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    largo_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_publicacion']
    
    def __str__(self):
        return self.titulo


class ProductImage(models.Model):
    """Modelo para imágenes de productos"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
    
    def __str__(self):
        return f"Imagen de {self.product.titulo}"


class Comision(models.Model):
    """Modelo para comisiones por categoría"""
    categoria = models.CharField(max_length=100, unique=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Porcentaje de comisión (ej: 10.50 = 10.5%)")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Comisión'
        verbose_name_plural = 'Comisiones'
        ordering = ['categoria']
    
    def __str__(self):
        return f"{self.categoria}: {self.porcentaje}%"
    
    def calcular_comision(self, precio):
        """Calcula la comisión sobre un precio"""
        return (precio * self.porcentaje) / 100


class Order(models.Model):
    """Modelo para órdenes de compra/venta"""
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmada', 'Confirmada'),
        ('Enviada', 'Enviada'),
        ('Entregada', 'Entregada'),
        ('Cancelada', 'Cancelada'),
        ('Rechazada', 'Rechazada'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('mercadopago', 'Mercado Pago'),
        ('lemon', 'Lemon'),
        ('brubank', 'Brubank'),
    ]
    
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compras')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas')
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ordenes')
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    direccion_entrega = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    transaccion_id = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Orden #{self.id} - {self.comprador.nombre} -> {self.vendedor.nombre}"
    
    def save(self, *args, **kwargs):
        # Calcular precio total automáticamente
        self.precio_total = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)


class Rating(models.Model):
    """Modelo para calificaciones de usuarios (como en MercadoLibre)"""
    ESTRELLAS_CHOICES = [
        (1, '1 estrella'),
        (2, '2 estrellas'),
        (3, '3 estrellas'),
        (4, '4 estrellas'),
        (5, '5 estrellas'),
    ]
    
    calificador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_dadas')
    calificado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_recibidas')
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='calificaciones', null=True, blank=True)
    estrellas = models.IntegerField(choices=ESTRELLAS_CHOICES)
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ['calificador', 'orden']  # Un usuario solo puede calificar una orden una vez
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.calificador.nombre} -> {self.calificado.nombre}: {self.estrellas} estrellas"


class Question(models.Model):
    """Modelo para preguntas sobre productos"""
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='preguntas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preguntas_realizadas')
    pregunta = models.TextField()
    respuesta = models.TextField(blank=True, null=True)
    respondida_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='preguntas_respondidas')
    fecha_pregunta = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'
        ordering = ['-fecha_pregunta']
    
    def __str__(self):
        return f"Pregunta sobre {self.producto.titulo}"


class Offer(models.Model):
    """Modelo para ofertas/negociación de precios"""
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aceptada', 'Aceptada'),
        ('Rechazada', 'Rechazada'),
        ('Expirada', 'Expirada'),
    ]
    
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ofertas')
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ofertas_realizadas')
    precio_ofertado = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    mensaje = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Oferta de ${self.precio_ofertado} para {self.producto.titulo}"


class Message(models.Model):
    """Modelo para mensajería entre comprador y vendedor"""
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mensajes', null=True, blank=True)
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    asunto = models.CharField(max_length=200, blank=True, null=True)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"Mensaje de {self.remitente.nombre} a {self.destinatario.nombre}"


class Carrier(models.Model):
    """Proveedor logístico"""
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Proveedor Logístico'
        verbose_name_plural = 'Proveedores Logísticos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Shipment(models.Model):
    """Envío asociado a una orden"""
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Cotizado', 'Cotizado'),
        ('Creado', 'Creado'),
        ('Despachado', 'Despachado'),
        ('En camino', 'En camino'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
        ('Error', 'Error'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='envios')
    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    moneda = models.CharField(max_length=10, default='ARS')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    tracking_number = models.CharField(max_length=200, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    etiqueta_url = models.URLField(blank=True, null=True)
    dias_estimados = models.IntegerField(null=True, blank=True)
    proveedor_envio_id = models.CharField(max_length=200, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Envío #{self.id} - Orden #{self.order.id}"


class TrackingEvent(models.Model):
    """Eventos de tracking de un envío"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking')
    estado = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_evento = models.DateTimeField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Evento de Tracking'
        verbose_name_plural = 'Eventos de Tracking'
        ordering = ['-fecha_evento']
    
    def __str__(self):
        return f"{self.estado} - Envío #{self.shipment.id}"
