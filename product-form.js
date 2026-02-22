// Esperar a que auth.js cargue
// Usar función para evitar conflictos de declaración
function getApiUrl() {
    if (window.authUtils && window.authUtils.API_URL) {
        return window.authUtils.API_URL;
    }
    return 'http://localhost:8000/api';
}

document.addEventListener('DOMContentLoaded', () => {
    // Esperar a que auth.js esté disponible
    const initForm = () => {
        const form = document.getElementById('productForm');
        
        if (!form) {
            console.error('Formulario no encontrado');
            return;
        }

        if (!window.authUtils) {
            console.warn('⚠️ authUtils no está disponible, esperando...');
            setTimeout(initForm, 100);
            return;
        }

        console.log('✅ Formulario inicializado');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const errorEl = document.getElementById('errorMessage');
            const successEl = document.getElementById('successMessage');
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (errorEl) errorEl.style.display = 'none';
            if (successEl) successEl.style.display = 'none';

            // Validación básica del formulario
            const titulo = document.getElementById('titulo').value.trim();
            const descripcion = document.getElementById('descripcion').value.trim();
            const precio = parseFloat(document.getElementById('precio').value);
            const categoria = document.getElementById('categoria').value;
            const stock = parseInt(document.getElementById('stock').value);

            if (!titulo || !descripcion || !precio || !categoria) {
                if (errorEl) {
                    errorEl.textContent = 'Por favor completa todos los campos requeridos';
                    errorEl.style.display = 'block';
                }
                return;
            }

            if (precio <= 0) {
                if (errorEl) {
                    errorEl.textContent = 'El precio debe ser mayor a 0';
                    errorEl.style.display = 'block';
                }
                return;
            }

            if (stock < 1) {
                if (errorEl) {
                    errorEl.textContent = 'El stock debe ser al menos 1';
                    errorEl.style.display = 'block';
                }
                return;
            }

            const token = window.authUtils?.getToken();
            
            if (!token) {
                if (errorEl) {
                    errorEl.textContent = 'Debes iniciar sesión para publicar productos';
                    errorEl.style.display = 'block';
                }
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
                return;
            }

            // Deshabilitar botón y mostrar estado de carga
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Publicando...';
            }

            try {
                // Crear FormData para enviar datos (aunque no haya imágenes)
                const formData = new FormData();
                formData.append('titulo', titulo);
                formData.append('descripcion', descripcion);
                formData.append('precio', precio);
                formData.append('categoria', categoria);
                formData.append('condicion', document.getElementById('condicion').value);
                formData.append('stock', stock);
                formData.append('envio_gratis', document.getElementById('envioGratis').checked);
                
                // Datos de envío (opcionales)
                const pesoKg = document.getElementById('pesoKg')?.value;
                const altoCm = document.getElementById('altoCm')?.value;
                const anchoCm = document.getElementById('anchoCm')?.value;
                const largoCm = document.getElementById('largoCm')?.value;
                if (pesoKg) formData.append('peso_kg', pesoKg);
                if (altoCm) formData.append('alto_cm', altoCm);
                if (anchoCm) formData.append('ancho_cm', anchoCm);
                if (largoCm) formData.append('largo_cm', largoCm);

                const API_URL = getApiUrl();
                console.log('📤 Enviando producto a:', `${API_URL}/products/`);
                console.log('📋 Datos del formulario:', {
                    titulo,
                    descripcion: descripcion.substring(0, 50) + '...',
                    precio,
                    categoria,
                    stock,
                    envio_gratis: document.getElementById('envioGratis').checked
                });

                const response = await fetch(`${API_URL}/products/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                        // NO incluir Content-Type, el navegador lo hará automáticamente con FormData
                    },
                    body: formData
                });

                console.log('📥 Respuesta del servidor:', response.status, response.statusText);

                const data = await response.json();
                console.log('📦 Datos recibidos:', data);

                if (response.ok) {
                    console.log('✅ Producto publicado exitosamente');
                    if (successEl) {
                        successEl.textContent = '¡Producto publicado exitosamente! Redirigiendo...';
                        successEl.style.display = 'block';
                    }
                    form.reset();
                    // Esperar un poco antes de redirigir para asegurar que el producto se guardó
                    setTimeout(() => {
                        console.log('🔄 Redirigiendo a mi-pagina.html');
                        window.location.href = 'mi-pagina.html';
                    }, 1500);
                } else {
                    // Mostrar errores más detallados
                    let errorMsg = 'Error al publicar el producto';
                    if (data.detail) {
                        errorMsg = data.detail;
                    } else if (data.message) {
                        errorMsg = data.message;
                    } else if (typeof data === 'object') {
                        // Si hay errores de validación por campo
                        const errors = Object.values(data).flat();
                        if (errors.length > 0) {
                            errorMsg = Array.isArray(errors[0]) ? errors[0][0] : errors[0];
                        }
                    }
                    
                    if (errorEl) {
                        errorEl.textContent = errorMsg;
                        errorEl.style.display = 'block';
                    }
                    
                    // Rehabilitar botón
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Publicar producto';
                    }
                }
            } catch (error) {
                console.error('❌ Error:', error);
                if (errorEl) {
                    errorEl.textContent = `Error de conexión: ${error.message}. Asegúrate de que el servidor Django esté corriendo en el puerto 8000.`;
                    errorEl.style.display = 'block';
                }
                
                // Rehabilitar botón
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Publicar producto';
                }
            }
        });
    };

    // Iniciar después de un pequeño delay para asegurar que auth.js cargó
    setTimeout(initForm, 50);
});

