import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';

import './VerifyEmail.css';

function VerifyEmail() {
  const [searchParams] = useSearchParams();

  const hasVerified = useRef(false);

  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('Verificando tu correo...');

  useEffect(() => {
    const verifyEmail = async () => {
      if (hasVerified.current) {
        return;
      }

      hasVerified.current = true;

      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setMessage('Token de verificación no encontrado.');
        return;
      }

      try {
        await api.get(`/users/verify-email?token=${token}`);

        setStatus('success');
        setMessage('Tu correo fue verificado correctamente. Ya puedes iniciar sesión.');
      } catch (error) {
        const errorMessage =
          error.response?.data?.detail || 'No se pudo verificar el correo.';

        setStatus('error');
        setMessage(errorMessage);
      }
    };

    verifyEmail();
  }, [searchParams]);

  return (
    <section className="verify-email-page">
      <div className={`verify-email-card ${status}`}>
        <h1>
          {status === 'loading' && 'Verificando correo'}
          {status === 'success' && 'Correo verificado'}
          {status === 'error' && 'Error de verificación'}
        </h1>

        <p>{message}</p>

        {status === 'success' && (
          <Link to="/login" className="verify-email-button">
            Ir a iniciar sesión
          </Link>
        )}

        {status === 'error' && (
          <Link to="/" className="verify-email-button secondary">
            Volver al inicio
          </Link>
        )}
      </div>
    </section>
  );
}

export default VerifyEmail;