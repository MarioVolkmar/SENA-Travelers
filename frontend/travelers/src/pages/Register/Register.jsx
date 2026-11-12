import { useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import GoogleButton from '../../components/GoogleButton/GoogleButton';
import Icon from '../../components/Icon/Icon';
import { getErrorMessage } from '../../utils/format';

import './Register.css';

import Select from '../../components/Select/Select';
import usePageTitle from '../../hooks/usePageTitle';
const EMPTY_ACCOUNT = { nombre: '', email: '', password: '', confirmPassword: '' };
const EMPTY_COMPANY = { nombre_empresa: '', rut: '', telefono: '', direccion: '', ciudad_id: '' };

const ACCOUNT_TYPES = [
  {
    key: 'viajero',
    icon: 'compass',
    title: 'Viajero',
    text: 'Reserva paquetes y viaja',
  },
  {
    key: 'proveedor',
    icon: 'building',
    title: 'Proveedor',
    text: 'Ofrece hotel, comida, transporte o tours',
  },
];

function Register() {
  usePageTitle('Crear cuenta');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [accountType, setAccountType] = useState(searchParams.get('tipo') === 'proveedor' ? 'proveedor' : 'viajero');
  const [step, setStep] = useState(1);
  const [account, setAccount] = useState(EMPTY_ACCOUNT);
  const [company, setCompany] = useState(EMPTY_COMPANY);
  const [cities, setCities] = useState([]);

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  const isProvider = accountType === 'proveedor';

  useEffect(() => {
    if (isProvider && cities.length === 0) {
      api.get('/cities/').then((response) => setCities(response.data)).catch(() => setCities([]));
    }
  }, [isProvider, cities.length]);

  const updateAccount = (event) => setAccount({ ...account, [event.target.name]: event.target.value });
  const updateCompany = (event) => setCompany({ ...company, [event.target.name]: event.target.value });

  const chooseType = (key) => {
    setAccountType(key);
    setStep(1);
    setError('');
  };

  const validateAccount = () => {
    if (account.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return false;
    }

    if (account.password !== account.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return false;
    }

    return true;
  };

  const createAccount = async () => {
    setLoading(true);
    setError('');

    try {
      const payload = {
        nombre: account.nombre.trim(),
        email: account.email.replace(/\s+/g, ''),
        password: account.password.trim(),
      };

      if (isProvider) {
        payload.proveedor = {
          nombre_empresa: company.nombre_empresa.trim(),
          rut: company.rut.trim(),
          telefono: company.telefono.trim(),
          direccion: company.direccion.trim(),
          ciudad_id: Number(company.ciudad_id),
        };
      }

      await api.post('/users/', payload);

      setMessage(
        isProvider
          ? 'Cuenta creada y solicitud de proveedor enviada. Verifica tu correo; cuando el equipo apruebe tu empresa tendrás tu panel de proveedor.'
          : 'Cuenta creada. Verifica tu correo para poder iniciar sesión.'
      );
      setAccount(EMPTY_ACCOUNT);
      setCompany(EMPTY_COMPANY);

      setTimeout(() => navigate('/login'), isProvider ? 4000 : 2200);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Error al crear la cuenta'));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');

    if (step === 1) {
      if (!validateAccount()) return;

      if (isProvider) {
        setStep(2);
        return;
      }
    }

    await createAccount();
  };

  return (
    <section className="register-page">
      <form className="register-card register-card-wide" onSubmit={handleSubmit}>
        <h1>Crear cuenta</h1>
        <p>
          {isProvider
            ? 'Registra tu empresa para que tus servicios se incluyan en los paquetes de Travelers.'
            : 'Regístrate para reservar paquetes y gestionar tus pagos en Travelers.'}
        </p>

        <div className="register-types" role="radiogroup" aria-label="Tipo de cuenta">
          {ACCOUNT_TYPES.map((type) => (
            <label key={type.key} className={`register-type ${accountType === type.key ? 'selected' : ''}`}>
              <input
                type="radio"
                name="account-type"
                value={type.key}
                checked={accountType === type.key}
                onChange={() => chooseType(type.key)}
              />
              <span className="register-type-icon"><Icon name={type.icon} size={22} /></span>
              <span>
                <strong>{type.title}</strong>
                <small>{type.text}</small>
              </span>
            </label>
          ))}
        </div>

        {isProvider && (
          <ol className="register-steps" aria-label="Pasos del registro">
            <li className={step === 1 ? 'current' : 'done'}>
              <span>{step > 1 ? <Icon name="check" size={14} strokeWidth={2.6} /> : '1'}</span>
              Tu cuenta
            </li>
            <li className={step === 2 ? 'current' : ''}>
              <span>2</span>
              Datos de tu empresa
            </li>
          </ol>
        )}

        {error && <div className="register-error">{error}</div>}
        {message && <div className="register-success">{message}</div>}

        {step === 1 && (
          <>
            <GoogleButton
              text="signup_with"
              redirectTo={isProvider ? '/profile?seccion=proveedor' : '/profile'}
              dividerLabel="o regístrate con tu correo"
            />

            <div className="form-group">
              <label htmlFor="nombre">{isProvider ? 'Tu nombre (responsable)' : 'Nombre'}</label>
              <input id="nombre" type="text" name="nombre" value={account.nombre} onChange={updateAccount} placeholder="Tu nombre" minLength={2} required />
            </div>

            <div className="form-group">
              <label htmlFor="email">Correo electrónico</label>
              <input id="email" type="email" name="email" value={account.email} onChange={updateAccount} placeholder="correo@ejemplo.com" required />
            </div>

            <div className="register-row">
              <div className="form-group">
                <label htmlFor="password">Contraseña</label>
                <input id="password" type="password" name="password" autoComplete="new-password" value={account.password} onChange={updateAccount} placeholder="Mínimo 6 caracteres" required />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirmar</label>
                <input id="confirmPassword" type="password" name="confirmPassword" autoComplete="new-password" value={account.confirmPassword} onChange={updateAccount} placeholder="Repite tu contraseña" required />
              </div>
            </div>

            <label className="register-legal">
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(event) => setAcceptedTerms(event.target.checked)}
                required
              />
              <span>
                Acepto los <Link to="/terminos" target="_blank">términos y condiciones</Link> y
                la <Link to="/privacidad" target="_blank">política de privacidad</Link>.
              </span>
            </label>

            <button type="submit" className="register-submit" disabled={loading || !acceptedTerms}>
              {isProvider ? 'Continuar con los datos de la empresa' : loading ? 'Creando cuenta...' : 'Registrarme'}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div className="form-group">
              <label htmlFor="nombre_empresa">Nombre de la empresa</label>
              <input id="nombre_empresa" name="nombre_empresa" value={company.nombre_empresa} onChange={updateCompany} placeholder="Ej.: Hotel Casa del Mar" minLength={2} maxLength={100} required autoFocus />
            </div>

            <div className="register-row">
              <div className="form-group">
                <label htmlFor="rut">RUT</label>
                <input id="rut" name="rut" value={company.rut} onChange={updateCompany} minLength={5} maxLength={30} required />
              </div>
              <div className="form-group">
                <label htmlFor="telefono">Teléfono</label>
                <input id="telefono" type="tel" name="telefono" value={company.telefono} onChange={updateCompany} minLength={7} maxLength={30} required />
              </div>
            </div>

            <div className="register-row">
              <div className="form-group">
                <label htmlFor="direccion">Dirección</label>
                <input id="direccion" name="direccion" value={company.direccion} onChange={updateCompany} minLength={5} maxLength={45} required />
              </div>
              <div className="form-group">
                <label htmlFor="ciudad_id">Ciudad</label>
                <Select id="ciudad_id" name="ciudad_id" value={company.ciudad_id} onChange={updateCompany} required>
                  <option value="">Selecciona</option>
                  {cities.map((city) => (
                    <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
                  ))}
                </Select>
              </div>
            </div>

            <p className="register-note">
              Tu solicitud quedará en revisión. Mientras tanto podrás usar tu cuenta como viajero.
            </p>

            <div className="register-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setStep(1)} disabled={loading}>
                Atrás
              </button>
              <button type="submit" className="register-submit" disabled={loading}>
                {loading ? 'Enviando...' : 'Crear cuenta y enviar solicitud'}
              </button>
            </div>
          </>
        )}

        <p className="register-login-text">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </form>
    </section>
  );
}

export default Register;
