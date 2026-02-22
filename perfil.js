const API_URL = window.authUtils?.API_URL || 'http://localhost:8000/api';

// Cargar datos del usuario
async function loadUserData() {
    const token = window.authUtils?.getToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const user = await response.json();
            displayUserData(user);
            loadUserProducts();
            loadWallets();
        } else {
            window.location.href = 'login.html';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Mostrar datos del usuario
function displayUserData(user) {
    const userDataEl = document.getElementById('userData');
    if (!userDataEl) return;

    userDataEl.innerHTML = `
        <div class="user-info-item">
            <span class="user-info-label">Nombre:</span>
            <span class="user-info-value">${user.nombre}</span>
        </div>
        <div class="user-info-item">
            <span class="user-info-label">Email:</span>
            <span class="user-info-value">${user.email}</span>
        </div>
        <div class="user-info-item">
            <span class="user-info-label">Teléfono:</span>
            <span class="user-info-value">${user.telefono || 'No especificado'}</span>
        </div>
        <div class="user-info-item">
            <span class="user-info-label">Fecha de registro:</span>
            <span class="user-info-value">${user.fecha_creacion ? new Date(user.fecha_creacion).toLocaleDateString('es-AR') : 'N/A'}</span>
        </div>
        <div class="user-info-item">
            <span class="user-info-label">Productos publicados:</span>
            <span class="user-info-value">${user.productosPublicados?.length || 0}</span>
        </div>
    `;
}

// Cargar productos del usuario
async function loadUserProducts() {
    const token = window.authUtils?.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/products/mis_productos/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const products = await response.json();
            displayUserProducts(products);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Mostrar productos del usuario
function displayUserProducts(products) {
    const productsEl = document.getElementById('myProducts');
    if (!productsEl) return;

    if (products.length === 0) {
        productsEl.innerHTML = '<p>No has publicado ningún producto aún. <a href="publicar-producto.html">Publicar uno ahora</a></p>';
        return;
    }

    productsEl.innerHTML = products.map(product => `
        <div class="product-item">
            <h3>${product.titulo}</h3>
            <div class="price">$${parseFloat(product.precio).toLocaleString('es-AR')}</div>
            <span class="status ${product.estado.toLowerCase()}">${product.estado}</span>
            <p style="font-size: 12px; color: var(--text-gray); margin: 10px 0;">${product.descripcion.substring(0, 100)}...</p>
            <div class="actions">
                <button class="btn-small btn-edit" onclick="editProduct('${product.id}')">Editar</button>
                <button class="btn-small btn-delete" onclick="deleteProduct('${product.id}')">Eliminar</button>
            </div>
        </div>
    `).join('');
}

// Eliminar producto
async function deleteProduct(productId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este producto?')) return;

    const token = window.authUtils?.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/products/${productId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            loadUserProducts();
            alert('Producto eliminado exitosamente');
        } else {
            alert('Error al eliminar el producto');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Editar producto (redirigir a página de edición)
function editProduct(productId) {
    // Por simplicidad, redirigimos a publicar-producto con el ID
    // En una implementación completa, crearías una página de edición
    alert('Funcionalidad de edición próximamente. Por ahora puedes eliminar y volver a publicar.');
}

// Cargar billeteras
async function loadWallets() {
    const token = window.authUtils?.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/payments/mis-billeteras`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const wallets = await response.json();
            displayWallets(wallets);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Mostrar billeteras
function displayWallets(wallets) {
    const container = document.getElementById('walletsContainer');
    if (!container) return;

    const walletTypes = [
        { id: 'mercadopago', nombre: 'Mercado Pago', icono: '💳' },
        { id: 'lemon', nombre: 'Lemon', icono: '🍋' },
        { id: 'brubank', nombre: 'Brubank', icono: '🏦' }
    ];

    container.innerHTML = walletTypes.map(walletType => {
        const wallet = wallets[walletType.id];
        const isConnected = wallet && wallet.activa;

        return `
            <div class="wallet-card ${isConnected ? 'connected' : ''}">
                <div class="wallet-header">
                    <div class="wallet-name">
                        <span>${walletType.icono}</span>
                        <span>${walletType.nombre}</span>
                    </div>
                    <span class="wallet-status ${isConnected ? 'connected' : 'disconnected'}">
                        ${isConnected ? 'Conectada' : 'Desconectada'}
                    </span>
                </div>
                ${isConnected ? `
                    <p>Cuenta: ${wallet.cuenta}</p>
                    <button class="btn-disconnect" onclick="disconnectWallet('${walletType.id}')">
                        Desconectar
                    </button>
                ` : `
                    <form class="wallet-form" onsubmit="connectWallet(event, '${walletType.id}')">
                        <input type="text" placeholder="Número de cuenta o email" required>
                        <button type="submit" class="btn-connect">Conectar</button>
                    </form>
                `}
            </div>
        `;
    }).join('');
}

// Conectar billetera
async function connectWallet(e, walletType) {
    e.preventDefault();
    const input = e.target.querySelector('input');
    const cuenta = input.value;

    if (!cuenta) return;

    const token = window.authUtils?.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/payments/conectar-billetera`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ tipo: walletType, cuenta })
        });

        if (response.ok) {
            loadWallets();
            alert(`${walletType} conectada exitosamente`);
        } else {
            const data = await response.json();
            alert(data.message || 'Error al conectar la billetera');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Desconectar billetera
async function disconnectWallet(walletType) {
    if (!confirm(`¿Estás seguro de que deseas desconectar ${walletType}?`)) return;

    const token = window.authUtils?.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/payments/desconectar-billetera`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ tipo: walletType })
        });

        if (response.ok) {
            loadWallets();
            alert(`${walletType} desconectada exitosamente`);
        } else {
            alert('Error al desconectar la billetera');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

// Manejo de tabs
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');

            // Remover active de todos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Agregar active al seleccionado
            button.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Cargar datos al iniciar
    loadUserData();
});

// Exportar funciones globales
window.deleteProduct = deleteProduct;
window.editProduct = editProduct;
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;

