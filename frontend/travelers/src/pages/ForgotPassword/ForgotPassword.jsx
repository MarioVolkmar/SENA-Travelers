import { useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';

import './ForgotPassword.css';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setMessage('');
    setError('');
    setLoading(true);

    try {
      await api.post('/users/forgot-password', {
        email: email.replace(/\s+/g, '')
      });

      setMessage(
        'Si el correo existe, recibirás instrucciones para restablecer tu contraseña.'
      );

      setEmail('');
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'No se pudo procesar la solicitud.';

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="forgot-password-page">
      <form className="forgot-password-card" onSubmit={handleSubmit}>
        <h1>Recuperar contraseña</h1>

        <p>
          Ingresa el correo asociado a tu cuenta y te enviaremos un enlace para
          restablecer tu contraseña.
        </p>

        {message && (
          <div className="forgot-password-success">
            {message}
          </div>
        )}

        {error && (
          <div className="forgot-password-error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="email">Correo electrónico</label>

          <input
            id="email"
            type="email"
            name="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="correo@ejemplo.com"
            required
          />
        </div>

        <button
          type="submit"
          className="forgot-password-submit"
          disabled={loading}
        >
          {loading ? 'Enviando...' : 'Enviar enlace'}
        </button>

        <p className="forgot-password-login-text">
          ¿Recordaste tu contraseña?{' '}
          <Link to="/login">
            Inicia sesión
          </Link>
        </p>
      </form>
    </section>
  );
}

export default ForgotPassword;