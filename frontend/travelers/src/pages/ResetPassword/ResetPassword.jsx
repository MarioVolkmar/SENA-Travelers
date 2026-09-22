import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';

import './ResetPassword.css';

function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const token = searchParams.get('token');

  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: ''
  });

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData({
      ...formData,
      [name]: value
    });
  };

  const validateForm = () => {
    if (!token) {
      setError('Token de recuperación no encontrado.');
      return false;
    }

    if (formData.newPassword.length < 6) {
      setError('La nueva contraseña debe tener al menos 6 caracteres.');
      return false;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return false;
    }

    return true;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setMessage('');
    setError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await api.post('/users/reset-password', {
        token,
        new_password: formData.newPassword.trim()
      });

      setMessage('Contraseña actualizada correctamente. Ya puedes iniciar sesión.');

      setFormData({
        newPassword: '',
        confirmPassword: ''
      });

      setTimeout(() => {
        navigate('/login');
      }, 1800);
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || 'No se pudo actualizar la contraseña.';

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="reset-password-page">
      <form className="reset-password-card" onSubmit={handleSubmit}>
        <h1>Restablecer contraseña</h1>

        <p>
          Crea una nueva contraseña para recuperar el acceso a tu cuenta.
        </p>

        {!token && (
          <div className="reset-password-error">
            Token de recuperación no encontrado.
          </div>
        )}

        {message && (
          <div className="reset-password-success">
            {message}
          </div>
        )}

        {error && (
          <div className="reset-password-error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="newPassword">Nueva contraseña</label>

          <input
            id="newPassword"
            type="password"
            name="newPassword"
            value={formData.newPassword}
            onChange={handleChange}
            placeholder="Mínimo 6 caracteres"
            required
            disabled={!token}
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
            placeholder="Repite tu nueva contraseña"
            required
            disabled={!token}
          />
        </div>

        <button
          type="submit"
          className="reset-password-submit"
          disabled={loading || !token}
        >
          {loading ? 'Actualizando...' : 'Actualizar contraseña'}
        </button>

        <p className="reset-password-login-text">
          <Link to="/login">
            Volver a iniciar sesión
          </Link>
        </p>
      </form>
    </section>
  );
}

export default ResetPassword;