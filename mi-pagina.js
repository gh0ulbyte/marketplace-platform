// Función para obtener API_URL sin conflictos
function getApiUrl() {
    if (window.authUtils && window.authUtils.API_URL) {
        return window.authUtils.API_URL;
    }
    return 'http://localhost:8000/api';
}

// Cargar información del vendedor y sus productos
async function loadMyPage() {
    console.log('🔍 Cargando mi página...');
    
    // Verificar que authUtils esté disponible
    if (!window.authUtils) {
        console.error('❌ authUtils no está disponible');
        setTimeout(() => {
            if (window.authUtils) {
                loadMyPage();
            } else {
                const sellerName = document.getElementById('sellerName');
                const sellerEmail = document.getElementById('sellerEmail');
                const grid = document.getElementById('myProductsGrid');
                
                if (sellerName) sellerName.textContent = 'Error al cargar';
                if (sellerEmail) sellerEmail.textContent = 'Por favor, recarga la página';
                if (grid) {
                    grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 40px;"><p>Error: No se pudo inicializar. Recarga la página.</p></div>';
                }
            }
        }, 200);
        return;
    }
    
    const token = window.authUtils.getToken();
    const API_URL = getApiUrl();
    
    if (!token) {
        console.error('❌ No hay token de autenticación');
        const sellerName = document.getElementById('sellerName');
        const sellerEmail = document.getElementById('sellerEmail');
        const grid = document.getElementById('myProductsGrid');
        
        if (sellerName) sellerName.textContent = 'No autenticado';
        if (sellerEmail) sellerEmail.textContent = 'Redirigiendo al login...';
        if (grid) {
            grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 40px;"><p>Debes iniciar sesión para ver tu página.</p></div>';
        }
        
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return;
    }

    try {
        // Cargar información del usuario
        const apiUrl = getApiUrl();
        const userResponse = await fetch(`${apiUrl}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (userResponse.ok) {
            const user = await userResponse.json();
            console.log('✅ Usuario cargado:', user);
            
            // Mostrar información del vendedor
            // Usar nombre_tienda si existe, sino nombre de usuario, sino nombre
            const nombreMostrar = user.nombre_tienda || user.username || user.nombre || 'Mi tienda';
            const sellerNameEl = document.getElementById('sellerName');
            const sellerEmailEl = document.getElementById('sellerEmail');
            const sellerBannerImg = document.getElementById('sellerBannerImage');
            
            if (sellerNameEl) sellerNameEl.textContent = nombreMostrar;
            if (sellerEmailEl) sellerEmailEl.textContent = user.email || '';

            // Mostrar banner si el usuario tiene uno configurado
            if (sellerBannerImg) {
                if (user.banner_imagen) {
                    let bannerUrl = user.banner_imagen;
                    if (bannerUrl && !bannerUrl.startsWith('http')) {
                        bannerUrl = `http://localhost:8000${bannerUrl}`;
                    }
                    sellerBannerImg.src = bannerUrl;
                    sellerBannerImg.style.display = 'block';
                } else {
                    sellerBannerImg.style.display = 'none';
                }
            }
        } else {
            const errorData = await userResponse.json().catch(() => ({}));
            console.error('❌ Error al cargar usuario:', errorData);
            
            const sellerNameEl = document.getElementById('sellerName');
            const sellerEmailEl = document.getElementById('sellerEmail');
            
            if (sellerNameEl) sellerNameEl.textContent = 'Error al cargar';
            if (sellerEmailEl) sellerEmailEl.textContent = errorData.message || 'Error desconocido';
        }

        // Cargar productos del usuario
        console.log('🛍️ Cargando productos del usuario...');
        console.log('   URL:', `${apiUrl}/products/mis_productos/`);
        console.log('   Token:', token ? 'Presente (' + token.substring(0, 20) + '...)' : 'Ausente');
        
        // Agregar timeout a la petición
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos timeout
        
        const productsResponse = await fetch(`${apiUrl}/products/mis_productos/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        console.log('📦 Respuesta de productos:', productsResponse.status, productsResponse.statusText);

        if (productsResponse.ok) {
            const products = await productsResponse.json();
            console.log('✅ Productos cargados:', products);
            renderMyProducts(products);
        } else {
            const errorData = await productsResponse.json().catch(() => ({}));
            console.error('❌ Error al cargar productos:', errorData);
            console.error('   Status:', productsResponse.status);
            console.error('   StatusText:', productsResponse.statusText);
            
            const grid = document.getElementById('myProductsGrid');
            if (grid) {
                let errorMsg = 'Error al cargar productos';
                if (errorData.detail) {
                    errorMsg = errorData.detail;
                } else if (errorData.message) {
                    errorMsg = errorData.message;
                } else if (productsResponse.status === 401) {
                    errorMsg = 'No estás autenticado. Por favor, inicia sesión nuevamente.';
                } else if (productsResponse.status === 403) {
                    errorMsg = 'No tienes permiso para ver estos productos.';
                }
                
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                        <p style="font-size: 18px; color: var(--text-gray); margin-bottom: 10px;">
                            ${errorMsg}
                        </p>
                        <p style="font-size: 14px; color: var(--text-gray);">
                            Código de error: ${productsResponse.status}
                        </p>
                        ${productsResponse.status === 401 ? '<p><a href="login.html" style="color: var(--primary-color);">Iniciar sesión</a></p>' : ''}
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('❌ Error de conexión:', error);
        console.error('   Error completo:', error);
        console.error('   Tipo de error:', error.name);
        
        const sellerName = document.getElementById('sellerName');
        const sellerEmail = document.getElementById('sellerEmail');
        const grid = document.getElementById('myProductsGrid');
        
        let errorMessage = 'Error de conexión';
        if (error.name === 'AbortError') {
            errorMessage = 'La petición tardó demasiado. El servidor puede estar lento o no estar respondiendo.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        if (sellerName) sellerName.textContent = 'Error de conexión';
        if (sellerEmail) sellerEmail.textContent = 'Asegúrate de que el servidor esté corriendo';
        
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                    <p style="font-size: 18px; color: var(--text-gray); margin-bottom: 10px;">
                        ${errorMessage}
                    </p>
                    <p style="font-size: 14px; color: var(--text-gray); margin-top: 10px;">
                        Asegúrate de que el servidor esté corriendo en http://localhost:8000
                    </p>
                    <p style="font-size: 12px; color: var(--text-gray); margin-top: 5px;">
                        ${error.name === 'AbortError' ? 'Timeout: La petición tardó más de 10 segundos' : `Error: ${error.toString()}`}
                    </p>
                    <button onclick="location.reload()" style="margin-top: 15px; padding: 10px 20px; background: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                        Reintentar
                    </button>
                </div>
            `;
        }
    }
}

// Renderizar productos
function renderMyProducts(products) {
    console.log('🎨 Renderizando productos:', products);
    const grid = document.getElementById('myProductsGrid');
    if (!grid) {
        console.error('❌ No se encontró el elemento myProductsGrid');
        return;
    }

    // Verificar que products sea un array
    if (!Array.isArray(products)) {
        console.error('❌ products no es un array:', products);
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                <p style="font-size: 18px; color: var(--text-gray);">
                    Error: Formato de datos inválido
                </p>
            </div>
        `;
        return;
    }

    if (products.length === 0) {
        console.log('📭 No hay productos para mostrar');
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
                <p style="font-size: 18px; color: var(--text-gray); margin-bottom: 20px;">
                    Aún no has publicado ningún producto
                </p>
                <a href="publicar-producto.html" style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">
                    Publicar mi primer producto
                </a>
            </div>
        `;
        return;
    }

    console.log(`✅ Renderizando ${products.length} productos`);

    // Usar la función crearProductoCard de script.js si está disponible
    if (window.crearProductoCard) {
        console.log('✅ Usando crearProductoCard de script.js');
        grid.innerHTML = products.map(producto => 
            window.crearProductoCard(producto)
        ).join('');
    } else {
        console.log('⚠️ crearProductoCard no disponible, usando fallback');
        // Fallback si la función no está disponible
        grid.innerHTML = products.map(producto => {
            const precio = parseFloat(producto.precio).toLocaleString('es-AR', {
                style: 'currency',
                currency: 'ARS',
                minimumFractionDigits: 0
            });
            
            let imagenUrl = '';
            if (producto.imagenes && producto.imagenes.length > 0) {
                imagenUrl = producto.imagenes[0].imagen;
                if (imagenUrl && !imagenUrl.startsWith('http')) {
                    imagenUrl = `http://localhost:8000${imagenUrl}`;
                }
            }
            
            return `
                <a href="#" class="product-card" data-id="${producto.id}">
                    <div class="product-image">
                        ${imagenUrl ? 
                            `<img src="${imagenUrl}" alt="${producto.titulo}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div class="product-image-placeholder" style="display: none;">
                                <span>📦</span>
                             </div>` 
                            : `<div class="product-image-placeholder">
                                <span>📦</span>
                               </div>`
                        }
                        ${producto.envio_gratis ? '<span class="free-shipping-badge">🚚 Envío gratis</span>' : ''}
                    </div>
                    <div class="product-info">
                        <div class="product-title">${producto.titulo}</div>
                        ${producto.condicion ? `<span class="product-condition">${producto.condicion}</span>` : ''}
                        <div class="product-price">$${precio.replace('ARS', '').trim()}</div>
                        <div class="product-shipping">${producto.envio_gratis ? 'Envío gratis' : 'Con costo de envío'}</div>
                    </div>
                </a>
            `;
        }).join('');
    }
    
    console.log('✅ Productos renderizados correctamente');
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Página "Mi página" cargada');
    
    const initMyPage = () => {
        if (!window.authUtils) {
            console.warn('⚠️ authUtils no está disponible, esperando...');
            setTimeout(initMyPage, 100);
            return;
        }

        console.log('✅ authUtils disponible, cargando mi página...');
        loadMyPage();
    };

    setTimeout(initMyPage, 200);
});
