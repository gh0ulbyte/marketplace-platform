const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    titulo: {
        type: String,
        required: true,
        trim: true
    },
    descripcion: {
        type: String,
        required: true
    },
    precio: {
        type: Number,
        required: true,
        min: 0
    },
    categoria: {
        type: String,
        required: true
    },
    condicion: {
        type: String,
        enum: ['Nuevo', 'Usado', 'Reacondicionado'],
        default: 'Nuevo'
    },
    stock: {
        type: Number,
        required: true,
        min: 0,
        default: 1
    },
    imagenes: [{
        type: String
    }],
    envioGratis: {
        type: Boolean,
        default: false
    },
    vendedor: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    estado: {
        type: String,
        enum: ['Activo', 'Pausado', 'Vendido', 'Eliminado'],
        default: 'Activo'
    },
    fechaPublicacion: {
        type: Date,
        default: Date.now
    },
    visitas: {
        type: Number,
        default: 0
    }
});

module.exports = mongoose.model('Product', productSchema);

