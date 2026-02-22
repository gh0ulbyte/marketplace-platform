// Esperar a que auth.js cargue
// Usar función para evitar conflictos de declaración global
function getApiUrl() {
    if (window.authUtils && window.authUtils.API_URL) {
        return window.authUtils.API_URL;
    }
    return 'http://localhost:8000/api';
}

let currentProduct = null;
let currentUser = null;
let currentShippingOptions = [];
const DEFAULT_ORIGIN_CP = '1000';

// Obtener ID del producto de la URL
function getProductIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// Cargar producto
async function loadProduct() {
    const API_URL = getApiUrl();
    const productId = getProductIdFromUrl();
    if (!productId) {
        document.getElementById('loadingMessage').innerHTML = '<p style="color: red;">Producto no encontrado</p>';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/products/${productId}/`);
        if (!response.ok) {
            throw new Error('Producto no encontrado');
        }

        currentProduct = await response.json();
        displayProduct(currentProduct);
        loadQuestions(productId);
        checkIfSeller();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingMessage').innerHTML = `<p style="color: red;">Error al cargar el producto: ${error.message}</p>`;
    }
}

// Mostrar producto
function displayProduct(product) {
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('productDetail').style.display = 'block';

    // Título y condición
    document.getElementById('conditionBadge').textContent = product.condicion;
    document.getElementById('productTitle').textContent = product.titulo;
    
    // Precio
    const precio = parseFloat(product.precio);
    document.getElementById('productPrice').textContent = `$${precio.toLocaleString('es-AR')}`;
    
    // Envío
    document.getElementById('shippingInfo').textContent = product.envio_gratis ? '🚚 Envío gratis' : '💰 Con costo de envío';
    
    // Descripción
    document.getElementById('productDescription').textContent = product.descripcion;
    
    // Stock
    const stock = product.stock || 0;
    document.getElementById('stockInfo').textContent = stock > 0 ? `${stock} disponibles` : 'Sin stock';
    document.getElementById('quantityInput').max = stock;
    
    if (stock === 0) {
        document.getElementById('buyButton').disabled = true;
        document.getElementById('buyButton').textContent = 'Sin stock';
    }
    
    // Imágenes
    if (product.imagenes && product.imagenes.length > 0) {
        const mainImage = document.getElementById('mainImage');
        const firstImage = product.imagenes[0].imagen;
        mainImage.src = firstImage.startsWith('http') ? firstImage : `http://localhost:8000${firstImage}`;
        
        const thumbnails = document.getElementById('thumbnailImages');
        product.imagenes.forEach((img, index) => {
            const thumb = document.createElement('img');
            thumb.className = 'thumbnail' + (index === 0 ? ' active' : '');
            thumb.src = img.imagen.startsWith('http') ? img.imagen : `http://localhost:8000${img.imagen}`;
            thumb.onclick = () => {
                mainImage.src = thumb.src;
                document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            };
            thumbnails.appendChild(thumb);
        });
    } else {
        document.getElementById('mainImage').src = '';
        document.getElementById('mainImage').style.display = 'none';
    }
    
    // Vendedor
    if (product.vendedor) {
        document.getElementById('sellerName').textContent = product.vendedor.nombre_tienda || product.vendedor.nombre || product.vendedor.username;
        document.getElementById('sellerLink').href = `mi-pagina.html?user_id=${product.vendedor.id}`;
        
        // Reputación
        loadSellerRating(product.vendedor.id);
    }
}

// Cargar reputación del vendedor
async function loadSellerRating(userId) {
    const API_URL = getApiUrl();
    try {
        const response = await fetch(`${API_URL}/ratings/usuario/${userId}`);
        if (response.ok) {
            const data = await response.json();
            const ratingDiv = document.getElementById('sellerRating');
            
            if (data.reputacion) {
                const stars = '⭐'.repeat(Math.round(data.reputacion));
                ratingDiv.innerHTML = `
                    <span class="stars">${stars}</span>
                    <span>${data.reputacion.toFixed(1)} (${data.total} calificaciones)</span>
                `;
            } else {
                ratingDiv.innerHTML = '<span>Sin calificaciones aún</span>';
            }
        }
    } catch (error) {
        console.error('Error cargando reputación:', error);
    }
}

// Verificar si el usuario es el vendedor
async function checkIfSeller() {
    const API_URL = getApiUrl();
    const token = window.authUtils?.getToken();
    if (!token) return;
    
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            
            if (currentProduct && currentUser && currentProduct.vendedor && currentProduct.vendedor.id === currentUser.id) {
                // Es el vendedor, mostrar tab de ofertas
                document.getElementById('offersTab').style.display = 'block';
                document.getElementById('buyButton').style.display = 'none';
                document.getElementById('offerButton').style.display = 'none';
                loadOffers();
            } else {
                // No es el vendedor, mostrar formularios
                document.getElementById('askQuestionForm').style.display = 'block';
                document.getElementById('makeOfferForm').style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error verificando usuario:', error);
    }
}

// Cargar preguntas
async function loadQuestions(productId) {
    const API_URL = getApiUrl();
    try {
        const response = await fetch(`${API_URL}/questions/producto/${productId}`);
        if (response.ok) {
            const questions = await response.json();
            displayQuestions(questions);
        }
    } catch (error) {
        console.error('Error cargando preguntas:', error);
    }
}

// Mostrar preguntas
function displayQuestions(questions) {
    const container = document.getElementById('questionsList');
    
    if (questions.length === 0) {
        container.innerHTML = '<p style="color: var(--text-gray);">Aún no hay preguntas. ¡Sé el primero en preguntar!</p>';
        return;
    }
    
    container.innerHTML = questions.map(q => `
        <div class="question-item">
            <div class="question-header">
                <span class="question-user">${q.usuario.nombre || q.usuario.username}</span>
                <span class="question-date">${new Date(q.fecha_pregunta).toLocaleDateString('es-AR')}</span>
            </div>
            <div class="question-text">${q.pregunta}</div>
            ${q.respuesta ? `
                <div class="answer-section">
                    <div class="answer-header">Respuesta del vendedor:</div>
                    <div>${q.respuesta}</div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Enviar pregunta
async function enviarPregunta() {
    const token = window.authUtils?.getToken();
    if (!token) {
        alert('Debes iniciar sesión para hacer una pregunta');
        window.location.href = 'login.html';
        return;
    }
    
    const questionText = document.getElementById('questionText').value.trim();
    if (!questionText) {
        alert('Por favor escribe una pregunta');
        return;
    }
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/questions/crear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                producto_id: getProductIdFromUrl(),
                pregunta: questionText
            })
        });
        
        if (response.ok) {
            alert('Pregunta enviada exitosamente');
            document.getElementById('questionText').value = '';
            loadQuestions(getProductIdFromUrl());
        } else {
            const error = await response.json();
            alert('Error: ' + (error.message || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Cargar ofertas (solo vendedor)
async function loadOffers() {
    const productId = getProductIdFromUrl();
    const token = window.authUtils?.getToken();
    if (!token) return;
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/offers/producto/${productId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const offers = await response.json();
            displayOffers(offers);
        }
    } catch (error) {
        console.error('Error cargando ofertas:', error);
    }
}

// Mostrar ofertas
function displayOffers(offers) {
    const container = document.getElementById('offersList');
    
    if (offers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-gray);">Aún no hay ofertas para este producto.</p>';
        return;
    }
    
    container.innerHTML = offers.map(o => `
        <div class="question-item">
            <div class="question-header">
                <span class="question-user">${o.comprador.nombre || o.comprador.username}</span>
                <span class="question-date">${new Date(o.fecha_creacion).toLocaleDateString('es-AR')}</span>
            </div>
            <div class="question-text">
                <strong>Oferta: $${parseFloat(o.precio_ofertado).toLocaleString('es-AR')}</strong>
                ${o.mensaje ? `<p style="margin-top: 10px;">${o.mensaje}</p>` : ''}
            </div>
            ${o.estado === 'Pendiente' ? `
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <button onclick="responderOferta(${o.id}, 'aceptar')" style="padding: 8px 20px; background: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer;">Aceptar</button>
                    <button onclick="responderOferta(${o.id}, 'rechazar')" style="padding: 8px 20px; background: #ccc; color: black; border: none; border-radius: 4px; cursor: pointer;">Rechazar</button>
                </div>
            ` : `<div style="margin-top: 10px; color: ${o.estado === 'Aceptada' ? 'green' : 'red'}; font-weight: 600;">Estado: ${o.estado}</div>`}
        </div>
    `).join('');
}

// Responder oferta
async function responderOferta(ofertaId, accion) {
    const token = window.authUtils?.getToken();
    if (!token) return;
    
    if (!confirm(`¿Estás seguro de que deseas ${accion === 'aceptar' ? 'aceptar' : 'rechazar'} esta oferta?`)) {
        return;
    }
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/offers/${ofertaId}/responder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ accion })
        });
        
        if (response.ok) {
            alert(`Oferta ${accion === 'aceptar' ? 'aceptada' : 'rechazada'} exitosamente`);
            loadOffers();
            loadProduct(); // Recargar producto por si cambió el precio
        } else {
            const error = await response.json();
            alert('Error: ' + (error.message || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Enviar oferta
async function enviarOferta() {
    const token = window.authUtils?.getToken();
    if (!token) {
        alert('Debes iniciar sesión para hacer una oferta');
        window.location.href = 'login.html';
        return;
    }
    
    const offerPrice = parseFloat(document.getElementById('offerPrice').value);
    const offerMessage = document.getElementById('offerMessage').value.trim();
    
    if (!offerPrice || offerPrice <= 0) {
        alert('Por favor ingresa un precio válido');
        return;
    }
    
    if (offerPrice >= parseFloat(currentProduct.precio)) {
        alert('La oferta debe ser menor al precio del producto');
        return;
    }
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/offers/crear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                producto_id: getProductIdFromUrl(),
                precio_ofertado: offerPrice,
                mensaje: offerMessage
            })
        });
        
        if (response.ok) {
            alert('Oferta enviada exitosamente. El vendedor será notificado.');
            document.getElementById('offerPrice').value = '';
            document.getElementById('offerMessage').value = '';
        } else {
            const error = await response.json();
            alert('Error: ' + (error.message || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Mostrar modal de compra
function mostrarModalCompra() {
    const token = window.authUtils?.getToken();
    if (!token) {
        alert('Debes iniciar sesión para comprar');
        window.location.href = 'login.html';
        return;
    }
    
    const cantidad = parseInt(document.getElementById('quantityInput').value) || 1;
    const precioTotal = parseFloat(currentProduct.precio) * cantidad;
    
    document.getElementById('buyModalContent').innerHTML = `
        <p><strong>Producto:</strong> ${currentProduct.titulo}</p>
        <p><strong>Cantidad:</strong> ${cantidad}</p>
        <p><strong>Precio unitario:</strong> $${parseFloat(currentProduct.precio).toLocaleString('es-AR')}</p>
        <p><strong>Total:</strong> $${precioTotal.toLocaleString('es-AR')}</p>
        <div style="margin-top: 20px;">
            <label>Dirección de entrega:</label>
            <textarea id="deliveryAddress" rows="3" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px; margin-top: 5px;"></textarea>
        </div>
        <div style="margin-top: 15px;">
            <label>Código postal de destino:</label>
            <div style="display: flex; gap: 10px; margin-top: 5px;">
                <input type="text" id="destinoCp" placeholder="Ej: 5000" style="flex: 1; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px;">
                <button onclick="cotizarEnvio()" style="padding: 10px 16px; background: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer;">Cotizar</button>
            </div>
            <small style="color: var(--text-gray);">Origen por defecto: ${DEFAULT_ORIGIN_CP}</small>
        </div>
        <div style="margin-top: 15px;">
            <label>Opciones de envío:</label>
            <select id="shippingOption" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px; margin-top: 5px;">
                <option value="">Cotizá para ver opciones</option>
            </select>
        </div>
        <div style="margin-top: 15px;">
            <label>Método de pago:</label>
            <select id="paymentMethod" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px; margin-top: 5px;">
                <option value="">Seleccionar método de pago</option>
            </select>
        </div>
    `;
    
    loadPaymentMethods();
    document.getElementById('buyModal').style.display = 'flex';
}

// Cerrar modal
function cerrarModalCompra() {
    document.getElementById('buyModal').style.display = 'none';
}

// Cargar métodos de pago
async function loadPaymentMethods() {
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/payments/metodos-disponibles`);
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('paymentMethod');
            select.innerHTML = '<option value="">Seleccionar método de pago</option>';
            
            data.metodos.forEach(method => {
                const option = document.createElement('option');
                option.value = method.id;
                option.textContent = `${method.icono} ${method.nombre}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error cargando métodos de pago:', error);
    }
}

// Confirmar compra
async function confirmarCompra() {
    const token = window.authUtils?.getToken();
    if (!token) return;
    
    const cantidad = parseInt(document.getElementById('quantityInput').value) || 1;
    const metodoPago = document.getElementById('paymentMethod').value;
    const direccionEntrega = document.getElementById('deliveryAddress').value.trim();
    const shippingOptionId = document.getElementById('shippingOption').value;
    
    if (!metodoPago) {
        alert('Por favor selecciona un método de pago');
        return;
    }
    
    if (!direccionEntrega) {
        alert('Por favor ingresa una dirección de entrega');
        return;
    }
    
    if (!shippingOptionId) {
        alert('Por favor selecciona una opción de envío');
        return;
    }
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/orders/crear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                producto_id: getProductIdFromUrl(),
                cantidad: cantidad,
                metodo_pago: metodoPago,
                direccion_entrega: direccionEntrega
            })
        });
        
        if (response.ok) {
            const order = await response.json();
            const selectedOption = currentShippingOptions.find(opt => String(opt.carrier_id) === String(shippingOptionId));
            if (selectedOption) {
                await fetch(`${API_URL}/shipping/create`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        order_id: order.id,
                        carrier_id: selectedOption.carrier_id,
                        costo: selectedOption.costo,
                        dias_estimados: selectedOption.dias_estimados
                    })
                });
            }
            alert('¡Compra realizada exitosamente!');
            cerrarModalCompra();
            window.location.href = 'perfil.html';
        } else {
            const error = await response.json();
            alert('Error: ' + (error.message || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Cotizar envío
async function cotizarEnvio() {
    const destinoCp = document.getElementById('destinoCp').value.trim();
    if (!destinoCp) {
        alert('Ingresá un código postal de destino');
        return;
    }
    
    try {
        const API_URL = getApiUrl();
        const response = await fetch(`${API_URL}/shipping/quote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.authUtils?.getToken() || ''}`
            },
            body: JSON.stringify({
                producto_id: getProductIdFromUrl(),
                cantidad: parseInt(document.getElementById('quantityInput').value) || 1,
                origen_cp: DEFAULT_ORIGIN_CP,
                destino_cp: destinoCp
            })
        });
        
        const data = await response.json();
        if (!response.ok) {
            alert(data.message || 'Error al cotizar envío');
            return;
        }
        
        currentShippingOptions = data.opciones || [];
        const select = document.getElementById('shippingOption');
        select.innerHTML = '<option value="">Seleccionar opción</option>';
        currentShippingOptions.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.carrier_id;
            option.textContent = `${opt.carrier_nombre} - $${opt.costo} (${opt.dias_estimados} días)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión al cotizar');
    }
}

// Tabs
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(`${tabId}Tab`).classList.add('active');
        });
    });
    
    // Cargar producto
    if (window.authUtils) {
        loadProduct();
    } else {
        setTimeout(loadProduct, 200);
    }
    
    // Event listeners
    document.getElementById('buyButton').addEventListener('click', mostrarModalCompra);
    document.getElementById('offerButton').addEventListener('click', () => {
        document.querySelector('[data-tab="offers"]').click();
    });
});

// Agregar al carrito
function agregarAlCarrito() {
    const cantidad = parseInt(document.getElementById('quantityInput').value) || 1;
    const productId = getProductIdFromUrl();
    
    if (!window.addToCart) {
        alert('Error: sistema de carrito no disponible');
        return;
    }
    
    addToCart(productId, cantidad);
    alert('Producto agregado al carrito');
    
    // Actualizar contador
    if (window.updateCartCount) {
        updateCartCount();
    }
}

// Exportar funciones globales
window.enviarPregunta = enviarPregunta;
window.enviarOferta = enviarOferta;
window.responderOferta = responderOferta;
window.mostrarModalCompra = mostrarModalCompra;
window.cerrarModalCompra = cerrarModalCompra;
window.confirmarCompra = confirmarCompra;
window.agregarAlCarrito = agregarAlCarrito;
window.cotizarEnvio = cotizarEnvio;
