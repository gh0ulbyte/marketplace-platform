const API_URL = 'http://localhost:8000/api';

// Funciones de utilidad
function mostrarError(elementId, mensaje) {
    const errorEl = document.getElementById('errorMessage');
    const successEl = document.getElementById('successMessage');
    if (errorEl) {
        errorEl.textContent = mensaje;
        errorEl.style.display = 'block';
    }
    if (successEl) {
        successEl.style.display = 'none';
    }
}

function mostrarExito(elementId, mensaje) {
    const errorEl = document.getElementById('errorMessage');
    const successEl = document.getElementById('successMessage');
    if (successEl) {
        successEl.textContent = mensaje;
        successEl.style.display = 'block';
    }
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

function ocultarMensajes() {
    const errorEl = document.getElementById('errorMessage');
    const successEl = document.getElementById('successMessage');
    if (errorEl) errorEl.style.display = 'none';
    if (successEl) successEl.style.display = 'none';
}

// Obtener token del localStorage
function getToken() {
    return localStorage.getItem('token');
}

// Guardar token en localStorage
function saveToken(token) {
    localStorage.setItem('token', token);
}

// Eliminar token
function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// Verificar si el usuario está autenticado
function isAuthenticated() {
    return !!getToken();
}

// Obtener headers con autenticación
function getAuthHeaders() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

// Manejo de registro
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        ocultarMensajes();

        const formData = {
            nombre: document.getElementById('nombre').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            telefono: document.getElementById('telefono').value || undefined
        };

        const confirmPassword = document.getElementById('confirmPassword').value;

        if (formData.password !== confirmPassword) {
            mostrarError('errorMessage', 'Las contraseñas no coinciden');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                saveToken(data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                mostrarExito('successMessage', '¡Cuenta creada exitosamente!');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            } else {
                mostrarError('errorMessage', data.message || 'Error al crear la cuenta');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarError('errorMessage', 'Error de conexión. Asegúrate de que el servidor esté corriendo.');
        }
    });
}

// Manejo de login
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        ocultarMensajes();

        const formData = {
            email: document.getElementById('email').value,
            password: document.getElementById('password').value
        };

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                saveToken(data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                mostrarExito('successMessage', '¡Login exitoso!');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            } else {
                mostrarError('errorMessage', data.message || 'Credenciales inválidas');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarError('errorMessage', 'Error de conexión. Asegúrate de que el servidor esté corriendo.');
        }
    });
}

// Manejo de logout
if (document.getElementById('logoutBtn')) {
    document.getElementById('logoutBtn').addEventListener('click', () => {
        removeToken();
        window.location.href = 'index.html';
    });
}

// Actualizar UI según autenticación
function updateAuthUI() {
    const token = getToken();
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    const loginLinks = document.querySelectorAll('.user-link[href*="login"], .user-link[href*="Ingresá"]');
    const logoutBtn = document.getElementById('logoutBtn');
    const perfilLink = document.getElementById('perfilLink');
    
    if (token && user) {
        // Usuario autenticado
        loginLinks.forEach(link => {
            link.textContent = user.nombre || 'Mi cuenta';
            link.href = 'perfil.html';
        });
        
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (perfilLink) perfilLink.style.display = 'block';
    } else {
        // Usuario no autenticado
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (perfilLink) perfilLink.style.display = 'none';
    }
}

// Ejecutar al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    
    // Proteger rutas que requieren autenticación
    const protectedPages = ['publicar-producto.html', 'perfil.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage) && !isAuthenticated()) {
        alert('Debes iniciar sesión para acceder a esta página');
        window.location.href = 'login.html';
    }
});

// Exportar funciones para uso en otros archivos
window.authUtils = {
    getToken,
    saveToken,
    removeToken,
    isAuthenticated,
    getAuthHeaders,
    API_URL
};

