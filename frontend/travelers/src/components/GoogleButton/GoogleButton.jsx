import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../../api/axiosConfig';
import { useAuth } from '../../context/AuthContext';
import { getErrorMessage } from '../../utils/format';

import './GoogleButton.css';

const GOOGLE_SCRIPT_URL = 'https://accounts.google.com/gsi/client';

let scriptPromise = null;

// Carga una sola vez el script de Google Identity Services
function loadGoogleScript() {
  if (window.google?.accounts?.id) return Promise.resolve();

  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = GOOGLE_SCRIPT_URL;
      script.async = true;
      script.defer = true;
      script.onload = resolve;
      script.onerror = () => {
        scriptPromise = null;
        reject(new Error('No se pudo cargar Google'));
      };
      document.head.appendChild(script);
    });
  }

  return scriptPromise;
}

/**
 * Botón "Continuar con Google". Sirve tanto para iniciar sesión como para
 * registrarse: si el correo no existe, el backend crea la cuenta.
 */
function GoogleButton({ text = 'continue_with', redirectTo = '/', dividerLabel = 'o con tu correo' }) {
  const navigate = useNavigate();
  const { login } = useAuth();
  const containerRef = useRef(null);

  const [clientId, setClientId] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ¿Está configurado Google en el backend?
  useEffect(() => {
    api.get('/users/google/config')
      .then((response) => {
        if (response.data.enabled) setClientId(response.data.client_id);
      })
      .catch(() => setClientId(null));
  }, []);

  // El callback siempre usa los valores actuales sin reinicializar Google
  const handleCredentialRef = useRef(null);

  useEffect(() => {
    handleCredentialRef.current = async ({ credential }) => {
      setError('');
      setLoading(true);

      try {
        const response = await api.post('/users/google', { credential });
        await login(response.data.access_token);
        navigate(redirectTo, { replace: true });
      } catch (requestError) {
        setError(getErrorMessage(requestError, 'No fue posible continuar con Google.'));
      } finally {
        setLoading(false);
      }
    };
  });

  useEffect(() => {
    if (!clientId) return undefined;

    let cancelled = false;

    const handleCredential = (response) => handleCredentialRef.current(response);

    loadGoogleScript()
      .then(() => {
        if (cancelled || !containerRef.current) return;

        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredential,
          ux_mode: 'popup',
        });

        const width = Math.min(Math.max(containerRef.current.offsetWidth, 200), 400);

        window.google.accounts.id.renderButton(containerRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          shape: 'pill',
          text,
          locale: 'es',
          width,
        });
      })
      .catch(() => {
        if (!cancelled) setError('No se pudo cargar el inicio de sesión con Google.');
      });

    return () => {
      cancelled = true;
    };
  }, [clientId, text]);

  if (!clientId) return null;

  return (
    <div className="google-auth">
      {error && <div className="alert alert-error">{error}</div>}

      <div className={`google-button ${loading ? 'is-loading' : ''}`} ref={containerRef} />

      {loading && <p className="google-loading">Conectando con Google...</p>}

      <div className="google-divider" role="separator">
        <span>{dividerLabel}</span>
      </div>
    </div>
  );
}

export default GoogleButton;
