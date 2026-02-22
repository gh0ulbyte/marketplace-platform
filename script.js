// API URL
const API_URL = window.authUtils?.API_URL || 'http://localhost:3000/api';

// Función para formatear precio
function formatearPrecio(precio) {
    return precio.toLocaleString('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

// Función para crear tarjeta de producto
function crearProductoCard(producto) {
    const precioFormateado = formatearPrecio(producto.precio);
    const simbolo = precioFormateado.charAt(0);
    const precio = precioFormateado.slice(1);
    const envio = producto.envioGratis ? "Envío gratis" : "Con costo de envío";
    
    return `
        <div class="product-card" data-id="${producto._id}">
            <div class="product-image">
                <span>📦</span>
            </div>
            <div class="product-info">
                <div class="product-price">
                    <span class="product-price-symbol">${simbolo}</span>${precio}
                </div>
                <div class="product-title">${producto.titulo}</div>
                <div class="product-shipping">${envio}</div>
            </div>
        </div>
    `;
}

// Función para renderizar productos
function renderizarProductos(productosArray = []) {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    if (productosArray.length === 0) {
        productsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                <p style="font-size: 18px; color: var(--text-gray);">
                    No hay productos disponibles
                </p>
            </div>
        `;
        return;
    }
    
    productsGrid.innerHTML = productosArray.map(producto => 
        crearProductoCard(producto)
    ).join('');
    
    // Agregar event listeners a las tarjetas
    const productCards = productsGrid.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.addEventListener('click', () => {
            const productId = card.getAttribute('data-id');
            console.log('Producto seleccionado:', productId);
            // Aquí podrías redirigir a una página de detalle del producto
        });
    });
}

// Cargar productos desde la API
async function cargarProductos(busqueda = '') {
    try {
        const url = busqueda 
            ? `${API_URL}/products?busqueda=${encodeURIComponent(busqueda)}`
            : `${API_URL}/products`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            renderizarProductos(data.products || []);
        } else {
            console.error('Error cargando productos:', data.message);
            renderizarProductos([]);
        }
    } catch (error) {
        console.error('Error de conexión:', error);
        renderizarProductos([]);
    }
}

// Función de búsqueda
function buscarProductos(termino) {
    cargarProductos(termino);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Cargar productos iniciales desde la API
    cargarProductos();
    
    // Actualizar UI de autenticación
    if (window.authUtils) {
        const token = window.authUtils.getToken();
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        
        const loginLink = document.getElementById('loginLink');
        const venderLink = document.getElementById('venderLink');
        const venderNavLink = document.getElementById('venderNavLink');
        const perfilLink = document.getElementById('perfilLink');
        
        if (token && user) {
            if (loginLink) {
                loginLink.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z" fill="currentColor"/>
                        <path d="M10 12C5.58172 12 2 13.7909 2 16V20H18V16C18 13.7909 14.4183 12 10 12Z" fill="currentColor"/>
                    </svg>
                    <span>${user.nombre || 'Mi cuenta'}</span>
                `;
                loginLink.href = 'perfil.html';
            }
            if (venderLink) venderLink.style.display = 'flex';
            if (venderNavLink) venderNavLink.style.display = 'block';
            if (perfilLink) perfilLink.style.display = 'flex';
        } else {
            if (venderLink) venderLink.style.display = 'none';
            if (venderNavLink) venderNavLink.style.display = 'none';
            if (perfilLink) perfilLink.style.display = 'none';
        }
    }
    
    // Búsqueda
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const termino = searchInput.value;
            buscarProductos(termino);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const termino = e.target.value;
            if (termino.length > 2 || termino.length === 0) {
                buscarProductos(termino);
            }
        });
    }
    
    // Agregar funcionalidad a los botones de ofertas
    const offerButtons = document.querySelectorAll('.btn-secondary');
    offerButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const offerCard = button.closest('.offer-card');
            if (offerCard) {
                const categoria = offerCard.querySelector('h3').textContent;
                console.log('Ver ofertas de:', categoria);
                // Aquí podrías filtrar productos por categoría
            }
        });
    });
    
    // Agregar funcionalidad a las categorías
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            const categoria = card.querySelector('span').textContent;
            console.log('Categoría seleccionada:', categoria);
            // Aquí podrías filtrar productos por categoría
        });
    });
    
    // Simular carrito (contador)
    let cartCount = 0;
    const cartCountElement = document.querySelector('.cart-count');
    
    // Agregar productos al carrito al hacer clic
    document.addEventListener('click', (e) => {
        const productCard = e.target.closest('.product-card');
        if (productCard && e.ctrlKey) { // Ctrl + click para agregar al carrito
            cartCount++;
            if (cartCountElement) {
                cartCountElement.textContent = cartCount;
            }
            // Mostrar notificación
            mostrarNotificacion('Producto agregado al carrito');
        }
    });
    
    // Función para mostrar notificaciones
    function mostrarNotificacion(mensaje) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background-color: var(--secondary-color);
            color: white;
            padding: 15px 20px;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = mensaje;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 2000);
    }
    
    // Agregar animaciones CSS dinámicamente
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});

// Función para filtrar por categoría
function filtrarPorCategoria(categoria) {
    const resultados = productos.filter(producto => 
        producto.categoria.toLowerCase() === categoria.toLowerCase()
    );
    renderizarProductos(resultados);
    
    // Scroll suave a la sección de productos
    const productsSection = document.querySelector('.featured-products');
    if (productsSection) {
        productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Exportar funciones para uso global
window.buscarProductos = buscarProductos;
window.filtrarPorCategoria = filtrarPorCategoria;

