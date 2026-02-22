const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
    nombre: {
        type: String,
        required: true,
        trim: true
    },
    email: {
        type: String,
        required: true,
        unique: true,
        lowercase: true,
        trim: true
    },
    password: {
        type: String,
        required: true,
        minlength: 6
    },
    telefono: {
        type: String,
        trim: true
    },
    direccion: {
        calle: String,
        ciudad: String,
        provincia: String,
        codigoPostal: String
    },
    billeteras: {
        mercadopago: {
            activa: { type: Boolean, default: false },
            cuenta: String
        },
        lemon: {
            activa: { type: Boolean, default: false },
            cuenta: String
        },
        brubank: {
            activa: { type: Boolean, default: false },
            cuenta: String
        }
    },
    productosPublicados: [{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Product'
    }],
    fechaCreacion: {
        type: Date,
        default: Date.now
    }
});

// Hash de contraseña antes de guardar
userSchema.pre('save', async function(next) {
    if (!this.isModified('password')) return next();
    this.password = await bcrypt.hash(this.password, 10);
    next();
});

// Método para comparar contraseñas
userSchema.methods.comparePassword = async function(candidatePassword) {
    return await bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', userSchema);

