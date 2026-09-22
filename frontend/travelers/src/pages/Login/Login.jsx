import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';


import api from '../../api/axiosConfig';
import { useAuth } from '../../context/AuthContext';

import './Login.css';

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData({
      ...formData,
      [name]: value
    });
  };

const handleSubmit = async (event) => {
  event.preventDefault();

  setError('');
  setLoading(true);

  try {
    const loginData = {
      email: formData.email.replace(/\s+/g, ''),
      password: formData.password.trim()
    };

    const response = await api.post('/users/login', loginData);

    await login(response.data.access_token);

    navigate('/');
  } catch (error) {
    const errorMessage =
      error.response?.data?.detail || 'Error al iniciar sesión';

    setError(errorMessage);
  } finally {
    setLoading(false);
  }
};

  return (
    <section className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Iniciar sesión</h1>

        <p>
          Ingresa con tu cuenta para gestionar tus reservas y pagos.
        </p>

        {error && (
          <div className="login-error">
            {error}
          </div>
        )}

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
            placeholder="Tu contraseña"
            required
          />
        </div>

        <button
          type="submit"
          className="login-submit"
          disabled={loading}
        >
          {loading ? 'Ingresando...' : 'Iniciar sesión'}
        </button>
        <p className="login-forgot-text">
          <Link to="/forgot-password">
            ¿Olvidaste tu contraseña?
          </Link>
        </p>
      </form>
    </section>
  );
}

export default Login;