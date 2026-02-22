// Página del carrito
const API_URL = window.authUtils?.API_URL || 'http://localhost:8000/api';

async function loadCartPage() {
    const cartItems = document.getElementById('cartItems');
    const cartSummary = document.getElementById('cartSummary');
    
    const products = await loadCartProducts();
    
    if (products.length === 0) {
        cartItems.innerHTML = `
            <div style="text-align: center; padding: 60px;">
                <p style="font-size: 24px; margin-bottom: 20px;">Tu carrito está vacío</p>
                <a href="/" style="display: inline-block; padding: 12px 30px; background: var(--primary-color); color: white; text-decoration: none; border-radius: 8px;">Seguir comprando</a>
            </div>
        `;
        cartSummary.style.display = 'none';
        return;
    }
    
    // Mostrar items
    cartItems.innerHTML = products.map(product => {
        const imagenUrl = product.imagenes && product.imagenes.length > 0 
            ? (product.imagenes[0].imagen.startsWith('http') 
                ? product.imagenes[0].imagen 
                : `http://localhost:8000${product.imagenes[0].imagen}`)
            : '';
        
        return `
            <div class="cart-item" data-product-id="${product.id}">
                ${imagenUrl ? `<img src="${imagenUrl}" alt="${product.titulo}" class="cart-item-image">` : '<div class="cart-item-image" style="background: #f5f5f5; display: flex; align-items: center; justify-content: center;">📦</div>'}
                <div class="cart-item-info">
                    <div class="cart-item-title">${product.titulo}</div>
                    <div class="cart-item-price">$${parseFloat(product.precio).toLocaleString('es-AR')}</div>
                    <div style="margin-top: 10px; color: var(--text-gray);">Stock disponible: ${product.stock}</div>
                </div>
                <div class="cart-item-quantity">
                    <button class="quantity-btn" onclick="updateQuantity(${product.id}, ${product.cantidad - 1})">-</button>
                    <input type="number" class="quantity-input" value="${product.cantidad}" min="1" max="${product.stock}" onchange="updateQuantity(${product.id}, parseInt(this.value))">
                    <button class="quantity-btn" onclick="updateQuantity(${product.id}, ${product.cantidad + 1})">+</button>
                </div>
                <button class="remove-btn" onclick="removeItem(${product.id})">Eliminar</button>
            </div>
        `;
    }).join('');
    
    // Actualizar total
    const total = calculateCartTotal(products);
    document.getElementById('cartTotal').textContent = `Total: $${total.toLocaleString('es-AR')}`;
    cartSummary.style.display = 'block';
}

function updateQuantity(productId, newQuantity) {
    const product = document.querySelector(`[data-product-id="${productId}"]`);
    const maxStock = parseInt(product.querySelector('.cart-item-info').textContent.match(/Stock disponible: (\d+)/)[1]);
    
    if (newQuantity < 1) {
        removeItem(productId);
        return;
    }
    
    if (newQuantity > maxStock) {
        alert(`Solo hay ${maxStock} unidades disponibles`);
        return;
    }
    
    updateCartQuantity(productId, newQuantity);
    loadCartPage();
}

function removeItem(productId) {
    if (confirm('¿Estás seguro de que deseas eliminar este producto del carrito?')) {
        removeFromCart(productId);
        loadCartPage();
    }
}

async function procederCheckout() {
    const token = window.authUtils?.getToken();
    if (!token) {
        alert('Debes iniciar sesión para continuar');
        window.location.href = 'login.html';
        return;
    }
    
    const products = await loadCartProducts();
    
    if (products.length === 0) {
        alert('Tu carrito está vacío');
        return;
    }
    
    // Por ahora, redirigir a una página de checkout simple
    // En una implementación completa, crearías una página de checkout
    let direccion = prompt('Ingresa tu dirección de entrega:');
    if (!direccion) return;
    
    let metodoPago = prompt('Selecciona método de pago (mercadopago/lemon/brubank):');
    if (!metodoPago) return;
    
    // Crear órdenes para cada producto
    let successCount = 0;
    let errorCount = 0;
    
    for (const product of products) {
        try {
            const response = await fetch(`${API_URL}/orders/crear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    producto_id: product.id,
                    cantidad: product.cantidad,
                    metodo_pago: metodoPago,
                    direccion_entrega: direccion
                })
            });
            
            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
            }
        } catch (error) {
            console.error('Error:', error);
            errorCount++;
        }
    }
    
    if (successCount > 0) {
        clearCart();
        alert(`¡${successCount} compra(s) realizada(s) exitosamente!`);
        window.location.href = 'perfil.html';
    } else {
        alert('Error al procesar las compras. Por favor intenta nuevamente.');
    }
}

// Cargar página al iniciar
document.addEventListener('DOMContentLoaded', () => {
    if (window.authUtils) {
        loadCartPage();
    } else {
        setTimeout(loadCartPage, 200);
    }
});

// Exportar funciones
window.updateQuantity = updateQuantity;
window.removeItem = removeItem;
window.procederCheckout = procederCheckout;
window.loadCartPage = loadCartPage;
