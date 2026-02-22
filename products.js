const express = require('express');
const router = express.Router();
const Product = require('../models/Product');
const { authMiddleware } = require('../middleware/auth');

// Obtener todos los productos (público)
router.get('/', async (req, res) => {
    try {
        const { categoria, busqueda, limit = 20, page = 1 } = req.query;
        const query = { estado: 'Activo' };

        if (categoria) {
            query.categoria = categoria;
        }

        if (busqueda) {
            query.$or = [
                { titulo: { $regex: busqueda, $options: 'i' } },
                { descripcion: { $regex: busqueda, $options: 'i' } }
            ];
        }

        const skip = (parseInt(page) - 1) * parseInt(limit);
        const products = await Product.find(query)
            .populate('vendedor', 'nombre email')
            .sort({ fechaPublicacion: -1 })
            .limit(parseInt(limit))
            .skip(skip);

        const total = await Product.countDocuments(query);

        res.json({
            products,
            total,
            page: parseInt(page),
            totalPages: Math.ceil(total / parseInt(limit))
        });
    } catch (error) {
        console.error('Error obteniendo productos:', error);
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Obtener un producto por ID
router.get('/:id', async (req, res) => {
    try {
        const product = await Product.findById(req.params.id)
            .populate('vendedor', 'nombre email telefono');

        if (!product || product.estado === 'Eliminado') {
            return res.status(404).json({ message: 'Producto no encontrado' });
        }

        // Incrementar visitas
        product.visitas += 1;
        await product.save();

        res.json(product);
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Publicar un nuevo producto (requiere autenticación)
router.post('/', authMiddleware, async (req, res) => {
    try {
        const { titulo, descripcion, precio, categoria, condicion, stock, imagenes, envioGratis } = req.body;

        if (!titulo || !descripcion || !precio || !categoria) {
            return res.status(400).json({ message: 'Por favor completa todos los campos requeridos' });
        }

        const product = new Product({
            titulo,
            descripcion,
            precio: parseFloat(precio),
            categoria,
            condicion: condicion || 'Nuevo',
            stock: parseInt(stock) || 1,
            imagenes: imagenes || [],
            envioGratis: envioGratis || false,
            vendedor: req.user._id
        });

        await product.save();

        // Agregar producto al array del usuario
        req.user.productosPublicados.push(product._id);
        await req.user.save();

        res.status(201).json({
            message: 'Producto publicado exitosamente',
            product
        });
    } catch (error) {
        console.error('Error publicando producto:', error);
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Obtener productos del usuario autenticado
router.get('/mis-productos/list', authMiddleware, async (req, res) => {
    try {
        const products = await Product.find({ vendedor: req.user._id })
            .sort({ fechaPublicacion: -1 });

        res.json(products);
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Actualizar producto (solo el vendedor)
router.put('/:id', authMiddleware, async (req, res) => {
    try {
        const product = await Product.findById(req.params.id);

        if (!product) {
            return res.status(404).json({ message: 'Producto no encontrado' });
        }

        if (product.vendedor.toString() !== req.user._id.toString()) {
            return res.status(403).json({ message: 'No tienes permiso para editar este producto' });
        }

        Object.assign(product, req.body);
        await product.save();

        res.json({ message: 'Producto actualizado exitosamente', product });
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

// Eliminar producto (solo el vendedor)
router.delete('/:id', authMiddleware, async (req, res) => {
    try {
        const product = await Product.findById(req.params.id);

        if (!product) {
            return res.status(404).json({ message: 'Producto no encontrado' });
        }

        if (product.vendedor.toString() !== req.user._id.toString()) {
            return res.status(403).json({ message: 'No tienes permiso para eliminar este producto' });
        }

        product.estado = 'Eliminado';
        await product.save();

        res.json({ message: 'Producto eliminado exitosamente' });
    } catch (error) {
        res.status(500).json({ message: 'Error del servidor', error: error.message });
    }
});

module.exports = router;

