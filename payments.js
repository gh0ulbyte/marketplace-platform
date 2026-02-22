const express = require('express');
const router = express.Router();
const { authMiddleware } = require('../middleware/auth');
const User = require('../models/User');
const axios = require('axios');

// Conectar billetera virtual
router.post('/conectar-billetera', authMiddleware, async (req, res) => {
    try {
        const { tipo, cuenta } = req.body;
        const tiposPermitidos = ['mercadopago', 'lemon', 'brubank'];

        if (!tiposPermitidos.includes(tipo)) {
            return res.status(400).json({ message: 'Tipo de billetera no válido' });
        }

        if (!cuenta) {
            return res.status(400).json({ message: 'Debes proporcionar el número de cuenta' });
        }

        const user = await User.findById(req.user._id);
        user.billeteras[tipo] = {
            activa: true,
            cuenta: cuenta
        };

        await user.save();

        res.json({
            message: `Billetera ${tipo} conectada exitosamente`,
            billeteras: user.billeteras
        });
    } catch (error) {
        console.error('Error conectando billetera:', error);
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Desconectar billetera
router.post('/desconectar-billetera', authMiddleware, async (req, res) => {
    try {
        const { tipo } = req.body;
        const user = await User.findById(req.user._id);

        if (user.billeteras[tipo]) {
            user.billeteras[tipo] = {
                activa: false,
                cuenta: ''
            };
            await user.save();
        }

        res.json({
            message: `Billetera ${tipo} desconectada`,
            billeteras: user.billeteras
        });
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Obtener billeteras del usuario
router.get('/mis-billeteras', authMiddleware, async (req, res) => {
    try {
        const user = await User.findById(req.user._id).select('billeteras');
        res.json(user.billeteras);
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Procesar pago (simulado - en producción usarías las APIs reales)
router.post('/procesar-pago', authMiddleware, async (req, res) => {
    try {
        const { tipo, monto, productoId, descripcion } = req.body;
        const user = await User.findById(req.user._id);

        // Verificar que la billetera esté conectada
        if (!user.billeteras[tipo] || !user.billeteras[tipo].activa) {
            return res.status(400).json({ message: `La billetera ${tipo} no está conectada` });
        }

        // Simular procesamiento de pago
        // En producción, aquí harías la llamada real a la API del proveedor
        const paymentResult = await simularPago(tipo, monto, user.billeteras[tipo].cuenta, descripcion);

        res.json({
            message: 'Pago procesado exitosamente',
            transaccion: {
                id: paymentResult.id,
                tipo: tipo,
                monto: monto,
                estado: 'Completado',
                fecha: new Date()
            }
        });
    } catch (error) {
        console.error('Error procesando pago:', error);
        res.status(500).json({ message: 'Error procesando el pago', error: error.message });
    }
});

// Función para simular pagos (en producción usarías las APIs reales)
async function simularPago(tipo, monto, cuenta, descripcion) {
    // Simulación de delay de red
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simular diferentes comportamientos según el tipo
    switch (tipo) {
        case 'mercadopago':
            // En producción: usar SDK de MercadoPago
            // const mercadopago = require('mercadopago');
            return {
                id: `MP-${Date.now()}`,
                estado: 'approved',
                mensaje: 'Pago aprobado con MercadoPago'
            };

        case 'lemon':
            // En producción: usar API de Lemon
            return {
                id: `LEMON-${Date.now()}`,
                estado: 'completed',
                mensaje: 'Pago completado con Lemon'
            };

        case 'brubank':
            // En producción: usar API de Brubank
            return {
                id: `BRU-${Date.now()}`,
                estado: 'success',
                mensaje: 'Pago exitoso con Brubank'
            };

        default:
            throw new Error('Tipo de billetera no soportado');
    }
}

// Obtener métodos de pago disponibles
router.get('/metodos-disponibles', (req, res) => {
    res.json({
        metodos: [
            {
                id: 'mercadopago',
                nombre: 'Mercado Pago',
                descripcion: 'Paga con tu cuenta de Mercado Pago',
                icono: '💳'
            },
            {
                id: 'lemon',
                nombre: 'Lemon',
                descripcion: 'Paga con tu billetera Lemon',
                icono: '🍋'
            },
            {
                id: 'brubank',
                nombre: 'Brubank',
                descripcion: 'Paga con tu cuenta Brubank',
                icono: '🏦'
            }
        ]
    });
});

module.exports = router;

