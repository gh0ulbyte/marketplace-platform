// Sistema de carrito de compras usando localStorage
const CART_KEY = 'mandale_cart';

// Obtener carrito
function getCart() {
    const cart = localStorage.getItem(CART_KEY);
    return cart ? JSON.parse(cart) : [];
}

// Guardar carrito
function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

// Agregar producto al carrito
function addToCart(productId, cantidad = 1) {
    const cart = getCart();
    const existingItem = cart.find(item => item.productId === productId);
    
    if (existingItem) {
        existingItem.cantidad += cantidad;
    } else {
        cart.push({ productId, cantidad });
    }
    
    saveCart(cart);
    updateCartCount();
    return cart;
}

// Remover producto del carrito
function removeFromCart(productId) {
    const cart = getCart().filter(item => item.productId !== productId);
    saveCart(cart);
    updateCartCount();
    return cart;
}

// Actualizar cantidad en carrito
function updateCartQuantity(productId, cantidad) {
    const cart = getCart();
    const item = cart.find(item => item.productId === productId);
    
    if (item) {
        if (cantidad <= 0) {
            return removeFromCart(productId);
        }
        item.cantidad = cantidad;
    }
    
    saveCart(cart);
    updateCartCount();
    return cart;
}

// Limpiar carrito
function clearCart() {
    localStorage.removeItem(CART_KEY);
    updateCartCount();
}

// Obtener cantidad total de items
function getCartItemCount() {
    const cart = getCart();
    return cart.reduce((total, item) => total + item.cantidad, 0);
}

// Actualizar contador en el header
function updateCartCount() {
    const count = getCartItemCount();
    const countElements = document.querySelectorAll('.cart-count');
    countElements.forEach(el => {
        el.textContent = count;
        el.style.display = count > 0 ? 'block' : 'none';
    });
}

// Cargar productos del carrito desde la API
async function loadCartProducts() {
    const cart = getCart();
    if (cart.length === 0) return [];
    
    const API_URL = window.authUtils?.API_URL || 'http://localhost:8000/api';
    const products = [];
    
    for (const item of cart) {
        try {
            const response = await fetch(`${API_URL}/products/${item.productId}/`);
            if (response.ok) {
                const product = await response.json();
                products.push({
                    ...product,
                    cantidad: item.cantidad
                });
            }
        } catch (error) {
            console.error(`Error cargando producto ${item.productId}:`, error);
        }
    }
    
    return products;
}

// Calcular total del carrito
function calculateCartTotal(products) {
    return products.reduce((total, item) => {
        return total + (parseFloat(item.precio) * item.cantidad);
    }, 0);
}

// Exportar funciones globales
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.clearCart = clearCart;
window.getCart = getCart;
window.getCartItemCount = getCartItemCount;
window.loadCartProducts = loadCartProducts;
window.calculateCartTotal = calculateCartTotal;

// Actualizar contador al cargar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateCartCount);
} else {
    updateCartCount();
}
