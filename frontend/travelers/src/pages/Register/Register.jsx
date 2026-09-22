import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

import api from '../../api/axiosConfig';

import './Register.css';

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData({
      ...formData,
      [name]: value
    });
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return false;
    }

    if (formData.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return false;
    }

    return true;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError('');
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const registerData = {
        nombre: formData.nombre.trim(),
        email: formData.email.replace(/\s+/g, ''),
        password: formData.password.trim()
      };

      await api.post('/users/', registerData);

      setMessage(
        'Usuario creado correctamente. Ahora puedes iniciar sesión cuando verifiques tu correo.'
      );

      setFormData({
        nombre: '',
        email: '',
        password: '',
        confirmPassword: ''
      });

      setTimeout(() => {
        navigate('/login');
      }, 1800);

    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'Error al crear el usuario';

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="register-page">
      <form className="register-card" onSubmit={handleSubmit}>
        <h1>Crear cuenta</h1>

        <p>
          Regístrate para crear reservas y gestionar tus pagos en Travelers.
        </p>

        {error && (
          <div className="register-error">
            {error}
          </div>
        )}

        {message && (
          <div className="register-success">
            {message}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="nombre">Nombre</label>
          <input
            id="nombre"
            type="text"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            placeholder="Tu nombre"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Correo electrónico</label>
          <input
            id="email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="correo@ejemplo.com"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Mínimo 6 caracteres"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Confirmar contraseña</label>
          <input
            id="confirmPassword"
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Repite tu contraseña"
            required
          />
        </div>

        <button
          type="submit"
          className="register-submit"
          disabled={loading}
        >
          {loading ? 'Creando cuenta...' : 'Registrarme'}
        </button>

        <p className="register-login-text">
          ¿Ya tienes cuenta?{' '}
          <Link to="/login">
            Inicia sesión
          </Link>
        </p>
      </form>
    </section>
  );
}

export default Register;