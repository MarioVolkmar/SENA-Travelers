import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Avatar from '../../components/Avatar/Avatar';
import Icon from '../../components/Icon/Icon';
import { ACCEPTED_IMAGE_TYPES, cropToSquareJpeg } from '../../utils/image';
import { useAuth } from '../../context/AuthContext';
import {
  formatDate,
  getErrorMessage,
  ROLE_ADMIN,
  ROLE_CLIENT,
  ROLE_PROVIDER,
} from '../../utils/format';
import AdminPanel from './AdminPanel';
import FavoritesSection from './FavoritesSection';
import ReviewsSection from './ReviewsSection';
import TravelerCard from './TravelerCard';
import TravelStamps from './TravelStamps';

import './Profile.css';

import Select from '../../components/Select/Select';
import DatePicker from '../../components/DatePicker/DatePicker';
import { todayKey } from '../../components/DatePicker/calendarUtils';
import usePageTitle from '../../hooks/usePageTitle';
const ROLE_NAMES = {
  [ROLE_ADMIN]: 'Administrador',
  [ROLE_CLIENT]: 'Cliente',
  [ROLE_PROVIDER]: 'Proveedor',
};

const emptyStatus = { type: '', text: '' };

function GoogleLogo() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.5 12.2c0-.8-.1-1.5-.2-2.2H12v4.2h5.9a5 5 0 0 1-2.2 3.3v2.7h3.5c2.1-1.9 3.3-4.7 3.3-8z" />
      <path fill="#34A853" d="M12 23c3 0 5.4-1 7.2-2.7l-3.5-2.7c-1 .7-2.2 1-3.7 1-2.9 0-5.3-1.9-6.2-4.5H2.2v2.8A11 11 0 0 0 12 23z" />
      <path fill="#FBBC05" d="M5.8 14.1a6.6 6.6 0 0 1 0-4.2V7.1H2.2a11 11 0 0 0 0 9.8l3.6-2.8z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3 .6 4.2 1.6l3.1-3.1A11 11 0 0 0 2.2 7.1l3.6 2.8C6.7 7.3 9.1 5.4 12 5.4z" />
    </svg>
  );
}

function StatusMessage({ status }) {
  if (!status.text) return null;
  return <div className={`alert alert-${status.type}`}>{status.text}</div>;
}

function Profile() {
  usePageTitle('Mi perfil');
  const { user, getCurrentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const isClient = user.rol_id === ROLE_CLIENT;
  const isProvider = user.rol_id === ROLE_PROVIDER;
  const isAdmin = user.rol_id === ROLE_ADMIN;

  const [cities, setCities] = useState([]);
  const [clientProfile, setClientProfile] = useState(undefined);
  const [providerProfile, setProviderProfile] = useState(undefined);

  // ---- Carnet de viajero ----
  const [clientForm, setClientForm] = useState({ identificacion: '', fecha_nacimiento: '', ciudad_id: '' });
  const [clientStatus, setClientStatus] = useState(emptyStatus);

  // ---- Información personal ----
  const [editingName, setEditingName] = useState(false);
  const [name, setName] = useState(user.nombre);
  const [nameStatus, setNameStatus] = useState(emptyStatus);

  // ---- Seguridad ----
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwords, setPasswords] = useState({ actual_password: '', new_password: '', confirm: '' });
  const [passwordStatus, setPasswordStatus] = useState(emptyStatus);

  // ---- Foto de perfil ----
  const photoInputRef = useRef(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoStatus, setPhotoStatus] = useState(emptyStatus);

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/cities/').then((response) => setCities(response.data)).catch(() => setCities([]));

    if (isClient) {
      api.get('/clients/me')
        .then((response) => setClientProfile(response.data))
        .catch(() => setClientProfile(null));
    }

    // Los clientes también pueden tener una solicitud de proveedor (pendiente o rechazada)
    if (isProvider || isClient) {
      api.get('/providers/me')
        .then((response) => setProviderProfile(response.data))
        .catch(() => setProviderProfile(null));
    }
  }, [isClient, isProvider]);

  // ---- Solicitud de proveedor ----
  const [providerForm, setProviderForm] = useState({ nombre_empresa: '', rut: '', telefono: '', direccion: '', ciudad_id: '' });
  const [providerStatus, setProviderStatus] = useState(emptyStatus);

  // Si la solicitud fue rechazada, el formulario arranca con los datos enviados
  useEffect(() => {
    if (providerProfile?.estado_verificacion === 'rechazado') {
      setProviderForm({
        nombre_empresa: providerProfile.nombre_empresa,
        rut: providerProfile.rut,
        telefono: providerProfile.telefono,
        direccion: providerProfile.direccion,
        ciudad_id: String(providerProfile.ciudad_id),
      });
    }
  }, [providerProfile]);

  const handleProviderSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setProviderStatus(emptyStatus);

    try {
      const response = await api.post('/providers/me', {
        nombre_empresa: providerForm.nombre_empresa.trim(),
        rut: providerForm.rut.trim(),
        telefono: providerForm.telefono.trim(),
        direccion: providerForm.direccion.trim(),
        ciudad_id: Number(providerForm.ciudad_id),
      });
      setProviderProfile(response.data);
      setProviderStatus({ type: 'success', text: 'Solicitud enviada. Te avisaremos cuando el equipo la revise.' });
    } catch (error) {
      setProviderStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible enviar la solicitud.') });
    } finally {
      setSaving(false);
    }
  };

  const sections = [
    isAdmin && { key: 'admin', label: 'Administración', icon: 'grid' },
    isClient && { key: 'carnet', label: 'Carnet de viajero', icon: 'ticket', pending: clientProfile === null },
    isProvider && { key: 'proveedor', label: 'Mi empresa', icon: 'building' },
    { key: 'favoritos', label: 'Favoritos', icon: 'heart' },
    isClient && { key: 'resenas', label: 'Mis reseñas', icon: 'star' },
    isClient && { key: 'proveedor', label: 'Ser proveedor', icon: 'building' },
    { key: 'personal', label: 'Información personal', icon: 'user' },
    { key: 'seguridad', label: 'Seguridad y acceso', icon: 'check', pending: !user.tiene_contrasena },
  ].filter(Boolean);

  const requested = searchParams.get('seccion');
  const active = sections.some((section) => section.key === requested) ? requested : sections[0].key;

  const goTo = (key) => {
    setSearchParams(key === sections[0].key ? {} : { seccion: key }, { replace: true });
  };

  const cityName = (id) => cities.find((city) => city.id_ciudad === Number(id))?.nombre || '';

  // Valores que muestra el carnet: los guardados o, si aún no hay perfil, los que se están escribiendo
  const cardIdentificacion = clientProfile ? clientProfile.identificacion : clientForm.identificacion.trim();
  const cardCity = clientProfile ? cityName(clientProfile.ciudad_id) : cityName(clientForm.ciudad_id);

  const progressItems = clientProfile
    ? [true, true, true, true]
    : [
        user.verificacion_email === 'verificado',
        Boolean(clientForm.identificacion.trim()),
        Boolean(clientForm.fecha_nacimiento),
        Boolean(clientForm.ciudad_id),
      ];
  const progress = Math.round((progressItems.filter(Boolean).length / progressItems.length) * 100);

  // ---------- Acciones ----------

  const openPhotoPicker = () => {
    setPhotoStatus(emptyStatus);
    photoInputRef.current?.click();
  };

  const handlePhotoSelected = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = ''; // permite volver a elegir el mismo archivo

    if (!file) return;

    setUploadingPhoto(true);
    setPhotoStatus(emptyStatus);

    try {
      const blob = await cropToSquareJpeg(file);
      const formData = new FormData();
      formData.append('file', blob, 'avatar.jpg');

      await api.post('/users/me/avatar', formData);
      await getCurrentUser();
      setPhotoStatus({ type: 'success', text: 'Foto de perfil actualizada.' });
    } catch (error) {
      setPhotoStatus({
        type: 'error',
        text: error.response ? getErrorMessage(error, 'No fue posible subir la foto.') : error.message,
      });
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handlePhotoRemove = async () => {
    setUploadingPhoto(true);
    setPhotoStatus(emptyStatus);

    try {
      await api.delete('/users/me/avatar');
      await getCurrentUser();
      setPhotoStatus({ type: 'success', text: 'Foto de perfil eliminada.' });
    } catch (error) {
      setPhotoStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible quitar la foto.') });
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleClientSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setClientStatus(emptyStatus);

    try {
      const response = await api.post('/clients/me', {
        identificacion: clientForm.identificacion.trim(),
        fecha_nacimiento: clientForm.fecha_nacimiento,
        ciudad_id: Number(clientForm.ciudad_id),
      });
      setClientProfile(response.data);
      setClientStatus({ type: 'success', text: '¡Tu carnet está activo! Ya puedes reservar paquetes.' });
    } catch (error) {
      setClientStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible activar el carnet.') });
    } finally {
      setSaving(false);
    }
  };

  const handleCityChange = async (event) => {
    const ciudad_id = Number(event.target.value);
    setClientStatus(emptyStatus);

    try {
      const response = await api.patch(`/clients/${clientProfile.id_cliente}/city`, { ciudad_id });
      setClientProfile(response.data);
      setClientStatus({ type: 'success', text: 'Ciudad actualizada.' });
    } catch (error) {
      setClientStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible actualizar la ciudad.') });
    }
  };

  const handleNameSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNameStatus(emptyStatus);

    try {
      await api.patch(`/users/${user.id_usuario}/name`, { nombre: name.trim() });
      await getCurrentUser();
      setEditingName(false);
      setNameStatus({ type: 'success', text: 'Nombre actualizado.' });
    } catch (error) {
      setNameStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible actualizar el nombre.') });
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    setPasswordStatus(emptyStatus);

    if (passwords.new_password !== passwords.confirm) {
      setPasswordStatus({ type: 'error', text: 'Las contraseñas nuevas no coinciden.' });
      return;
    }

    setSaving(true);

    try {
      const body = { new_password: passwords.new_password };
      if (user.tiene_contrasena) body.actual_password = passwords.actual_password;

      await api.patch(`/users/${user.id_usuario}/password`, body);
      const created = !user.tiene_contrasena;

      await getCurrentUser();
      setPasswords({ actual_password: '', new_password: '', confirm: '' });
      setPasswordOpen(false);
      setPasswordStatus({
        type: 'success',
        text: created
          ? 'Contraseña creada. Ahora también puedes entrar con tu correo y contraseña.'
          : 'Contraseña actualizada.',
      });
    } catch (error) {
      setPasswordStatus({ type: 'error', text: getErrorMessage(error, 'No fue posible guardar la contraseña.') });
    } finally {
      setSaving(false);
    }
  };

  // ---------- Secciones ----------

  const renderCarnet = () => (
    <>
      <div className="carnet">
        <div className="carnet-visual">
          <TravelerCard
            user={user}
            identificacion={cardIdentificacion}
            ciudad={cardCity}
            complete={Boolean(clientProfile)}
          />
          <div className="carnet-progress">
            <div className="carnet-progress-bar" aria-hidden="true">
              <span style={{ width: `${progress}%` }} />
            </div>
            <span>{progress}% completo</span>
          </div>
        </div>

        <div className="account-panel carnet-panel">
          <StatusMessage status={clientStatus} />

          {clientProfile === undefined && <p className="account-muted">Cargando...</p>}

          {clientProfile === null && (
            <form onSubmit={handleClientSubmit}>
              <h2>Activa tu carnet</h2>
              <p className="account-muted">
                Lo necesitas para reservar. Mira cómo se completa tu carnet mientras escribes.
              </p>

              <div className="field">
                <label htmlFor="client-id">Número de identificación</label>
                <input
                  id="client-id"
                  value={clientForm.identificacion}
                  onChange={(event) => setClientForm({ ...clientForm, identificacion: event.target.value })}
                  placeholder="Cédula o pasaporte"
                  minLength={5}
                  maxLength={30}
                  required
                />
              </div>

              <div className="account-field-row">
                <div className="field">
                  <label htmlFor="client-birth">Fecha de nacimiento</label>
                  <DatePicker
                    id="client-birth"
                    startView="years"
                    max={todayKey()}
                    placeholder="Elige tu fecha"
                    value={clientForm.fecha_nacimiento}
                    onChange={(event) => setClientForm({ ...clientForm, fecha_nacimiento: event.target.value })}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="client-city">Ciudad</label>
                  <Select
                    id="client-city"
                    value={clientForm.ciudad_id}
                    onChange={(event) => setClientForm({ ...clientForm, ciudad_id: event.target.value })}
                    required
                  >
                    <option value="">Selecciona</option>
                    {cities.map((city) => (
                      <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
                    ))}
                  </Select>
                </div>
              </div>

              <button type="submit" className="btn btn-primary btn-block" disabled={saving}>
                {saving ? 'Activando...' : 'Activar mi carnet'}
              </button>
            </form>
          )}

          {clientProfile && (
            <>
              <h2>Datos del carnet</h2>
              <ul className="account-rows">
                <li className="account-row">
                  <div>
                    <p className="account-row-label">Identificación</p>
                    <p className="account-row-value">{clientProfile.identificacion}</p>
                  </div>
                </li>
                <li className="account-row">
                  <div>
                    <p className="account-row-label">Fecha de nacimiento</p>
                    <p className="account-row-value">{formatDate(clientProfile.fecha_nacimiento)}</p>
                  </div>
                </li>
                <li className="account-row">
                  <div>
                    <label className="account-row-label" htmlFor="client-city-edit">Ciudad</label>
                    <Select
                      id="client-city-edit"
                      className="account-inline-select"
                      value={clientProfile.ciudad_id}
                      onChange={handleCityChange}
                    >
                      {cities.map((city) => (
                        <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
                      ))}
                    </Select>
                  </div>
                </li>
              </ul>
              <p className="account-muted account-note">
                Para corregir tu identificación o fecha de nacimiento, escribe al administrador.
              </p>
            </>
          )}
        </div>
      </div>

      <TravelStamps hasClientProfile={Boolean(clientProfile)} />
    </>
  );

  const renderPersonal = () => (
    <div className="account-panel">
      <h2>Información personal</h2>
      <StatusMessage status={nameStatus} />
      <StatusMessage status={photoStatus} />

      <ul className="account-rows">
        <li className="account-row">
          <div className="account-row-with-icon">
            <Avatar user={user} size={56} />
            <div>
              <p className="account-row-label">Foto de perfil</p>
              <p className="account-row-value">
                {uploadingPhoto ? 'Subiendo...' : 'JPG, PNG o WEBP. Se recorta en cuadrado.'}
              </p>
            </div>
          </div>
          <div className="account-inline-actions">
            {user.foto_url && (
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={handlePhotoRemove}
                disabled={uploadingPhoto}
              >
                Quitar
              </button>
            )}
            <button
              type="button"
              className="btn btn-primary btn-small"
              onClick={openPhotoPicker}
              disabled={uploadingPhoto}
            >
              {user.foto_url ? 'Cambiar' : 'Subir foto'}
            </button>
          </div>
        </li>
        <li className="account-row">
          {editingName ? (
            <form className="account-inline-form" onSubmit={handleNameSubmit}>
              <div className="field">
                <label htmlFor="profile-name">Nombre</label>
                <input
                  id="profile-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  minLength={2}
                  maxLength={100}
                  required
                  autoFocus
                />
              </div>
              <div className="account-inline-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  onClick={() => { setEditingName(false); setName(user.nombre); }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-small"
                  disabled={saving || name.trim() === user.nombre}
                >
                  Guardar
                </button>
              </div>
            </form>
          ) : (
            <>
              <div>
                <p className="account-row-label">Nombre</p>
                <p className="account-row-value">{user.nombre}</p>
              </div>
              <button type="button" className="btn btn-secondary btn-small" onClick={() => setEditingName(true)}>
                Editar
              </button>
            </>
          )}
        </li>
        <li className="account-row">
          <div>
            <p className="account-row-label">Correo electrónico</p>
            <p className="account-row-value">{user.email}</p>
          </div>
          <span className={`badge badge-${user.verificacion_email}`}>{user.verificacion_email}</span>
        </li>
        <li className="account-row">
          <div>
            <p className="account-row-label">Tipo de cuenta</p>
            <p className="account-row-value">{ROLE_NAMES[user.rol_id] || 'Usuario'}</p>
          </div>
        </li>
        {user.fecha_creacion && (
          <li className="account-row">
            <div>
              <p className="account-row-label">Miembro desde</p>
              <p className="account-row-value">{formatDate(user.fecha_creacion)}</p>
            </div>
          </li>
        )}
      </ul>
    </div>
  );

  const renderSecurity = () => (
    <div className="account-panel">
      <h2>Seguridad y acceso</h2>
      <StatusMessage status={passwordStatus} />

      <ul className="account-rows">
        <li className="account-row">
          <div className="account-row-with-icon">
            <span className="account-row-icon"><GoogleLogo /></span>
            <div>
              <p className="account-row-label">Google</p>
              <p className="account-row-value">
                {user.google_conectado ? `Conectado como ${user.email}` : 'Sin conectar'}
              </p>
            </div>
          </div>
          {user.google_conectado ? (
            <span className="badge badge-activo">Conectado</span>
          ) : (
            <span className="account-muted account-hint">Entra una vez con Google para conectarla</span>
          )}
        </li>

        <li className="account-row account-row-column">
          <div className="account-row-header">
            <div>
              <p className="account-row-label">Contraseña</p>
              <p className="account-row-value">
                {user.tiene_contrasena
                  ? 'Puedes entrar con tu correo y contraseña'
                  : 'Aún no has creado una contraseña'}
              </p>
            </div>
            {!passwordOpen && (
              <button
                type="button"
                className={`btn btn-small ${user.tiene_contrasena ? 'btn-secondary' : 'btn-primary'}`}
                onClick={() => { setPasswordOpen(true); setPasswordStatus(emptyStatus); }}
              >
                {user.tiene_contrasena ? 'Cambiar' : 'Crear contraseña'}
              </button>
            )}
          </div>

          {passwordOpen && (
            <form className="account-password-form" onSubmit={handlePasswordSubmit}>
              {user.tiene_contrasena && (
                <div className="field">
                  <label htmlFor="pwd-current">Contraseña actual</label>
                  <input
                    id="pwd-current"
                    type="password"
                    autoComplete="current-password"
                    value={passwords.actual_password}
                    onChange={(event) => setPasswords({ ...passwords, actual_password: event.target.value })}
                    required
                  />
                </div>
              )}
              <div className="account-field-row">
                <div className="field">
                  <label htmlFor="pwd-new">Nueva contraseña</label>
                  <input
                    id="pwd-new"
                    type="password"
                    autoComplete="new-password"
                    value={passwords.new_password}
                    onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })}
                    minLength={6}
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="pwd-confirm">Confirmar</label>
                  <input
                    id="pwd-confirm"
                    type="password"
                    autoComplete="new-password"
                    value={passwords.confirm}
                    onChange={(event) => setPasswords({ ...passwords, confirm: event.target.value })}
                    minLength={6}
                    required
                  />
                </div>
              </div>
              <div className="account-inline-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  onClick={() => { setPasswordOpen(false); setPasswords({ actual_password: '', new_password: '', confirm: '' }); }}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary btn-small" disabled={saving}>
                  {user.tiene_contrasena ? 'Cambiar contraseña' : 'Crear contraseña'}
                </button>
              </div>
            </form>
          )}
        </li>
      </ul>
    </div>
  );

  const providerRequestForm = (resubmit) => (
    <form onSubmit={handleProviderSubmit}>
      <div className="field">
        <label htmlFor="prov-company">Nombre de la empresa</label>
        <input
          id="prov-company"
          value={providerForm.nombre_empresa}
          onChange={(event) => setProviderForm({ ...providerForm, nombre_empresa: event.target.value })}
          placeholder="Ej.: Hotel Casa del Mar"
          minLength={2}
          maxLength={100}
          required
        />
      </div>
      <div className="account-field-row">
        <div className="field">
          <label htmlFor="prov-rut">RUT</label>
          <input id="prov-rut" value={providerForm.rut} onChange={(event) => setProviderForm({ ...providerForm, rut: event.target.value })} minLength={5} maxLength={30} required />
        </div>
        <div className="field">
          <label htmlFor="prov-phone">Teléfono</label>
          <input id="prov-phone" type="tel" value={providerForm.telefono} onChange={(event) => setProviderForm({ ...providerForm, telefono: event.target.value })} minLength={7} maxLength={30} required />
        </div>
      </div>
      <div className="account-field-row">
        <div className="field">
          <label htmlFor="prov-address">Dirección</label>
          <input id="prov-address" value={providerForm.direccion} onChange={(event) => setProviderForm({ ...providerForm, direccion: event.target.value })} minLength={5} maxLength={45} required />
        </div>
        <div className="field">
          <label htmlFor="prov-city">Ciudad</label>
          <Select id="prov-city" value={providerForm.ciudad_id} onChange={(event) => setProviderForm({ ...providerForm, ciudad_id: event.target.value })} required>
            <option value="">Selecciona</option>
            {cities.map((city) => (
              <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
            ))}
          </Select>
        </div>
      </div>
      <button type="submit" className="btn btn-primary" disabled={saving}>
        {saving ? 'Enviando...' : resubmit ? 'Reenviar solicitud' : 'Enviar solicitud'}
      </button>
    </form>
  );

  const renderProvider = () => {
    const estado = providerProfile?.estado_verificacion;

    // Cliente sin solicitud, o con solicitud pendiente o rechazada
    if (isClient) {
      return (
        <div className="account-panel">
          <h2>Ser proveedor de Travelers</h2>
          <StatusMessage status={providerStatus} />

          {providerProfile === undefined && <p className="account-muted">Cargando...</p>}

          {providerProfile === null && (
            <>
              <p className="account-muted">
                ¿Tienes un hotel, restaurante, transporte o tours? Regístrate como proveedor para que tus servicios
                se incluyan en nuestros paquetes. El equipo revisará tu solicitud.
              </p>
              {providerRequestForm(false)}
            </>
          )}

          {estado === 'pendiente' && (
            <div className="provider-request is-pending">
              <Icon name="clock" size={24} />
              <div>
                <strong>Solicitud en revisión</strong>
                <p>
                  Enviaste la solicitud de <b>{providerProfile.nombre_empresa}</b> el {formatDate(providerProfile.fecha_solicitud)}.
                  Cuando sea aprobada, tu cuenta pasará a ser de proveedor y tendrás tu panel.
                </p>
              </div>
            </div>
          )}

          {estado === 'rechazado' && (
            <>
              <div className="provider-request is-rejected">
                <Icon name="close" size={24} />
                <div>
                  <strong>Tu solicitud no fue aprobada</strong>
                  <p>Revisa y corrige tus datos y vuelve a enviarla.</p>
                </div>
              </div>
              {providerRequestForm(true)}
            </>
          )}

          {estado === 'aprobado' && (
            <div className="provider-request">
              <Icon name="check" size={24} />
              <div>
                <strong>Solicitud aprobada</strong>
                <p>Recarga la página para ver tu panel de proveedor.</p>
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
    <div className="account-panel">
      <div className="account-row-header">
        <h2>Mi empresa</h2>
        <Link to="/proveedor" className="btn btn-primary btn-small">Abrir mi panel</Link>
      </div>
      {providerProfile === undefined && <p className="account-muted">Cargando...</p>}
      {providerProfile === null && <p className="account-muted">Aún no tienes un perfil de proveedor registrado.</p>}
      {providerProfile && (
        <ul className="account-rows">
          <li className="account-row"><div><p className="account-row-label">Empresa</p><p className="account-row-value">{providerProfile.nombre_empresa}</p></div></li>
          <li className="account-row"><div><p className="account-row-label">RUT</p><p className="account-row-value">{providerProfile.rut}</p></div></li>
          <li className="account-row"><div><p className="account-row-label">Teléfono</p><p className="account-row-value">{providerProfile.telefono}</p></div></li>
          <li className="account-row"><div><p className="account-row-label">Ciudad</p><p className="account-row-value">{cityName(providerProfile.ciudad_id)}</p></div></li>
          <li className="account-row">
            <div><p className="account-row-label">Verificación</p></div>
            <span className={`badge badge-${providerProfile.estado_verificacion}`}>{providerProfile.estado_verificacion}</span>
          </li>
        </ul>
      )}
    </div>
    );
  };

  return (
    <section className="page account-page">
      <div className="page-header">
        <h1>{['carnet', 'admin'].includes(active) ? `Hola, ${user.nombre.split(' ')[0]}` : 'Mi cuenta'}</h1>
        {active === 'carnet' && (
          <p>
            {clientProfile
              ? 'Tu carnet de viajero está activo: ya puedes reservar.'
              : 'Te falta poco para tener tu carnet de viajero completo.'}
          </p>
        )}
      </div>

      <div className="account-layout">
        <aside className="account-sidebar">
          <div className="account-identity">
            <div className="account-avatar-wrapper">
              <Avatar user={user} size={60} />
              <button
                type="button"
                className="account-avatar-button"
                onClick={openPhotoPicker}
                disabled={uploadingPhoto}
                aria-label="Cambiar foto de perfil"
                title="Cambiar foto de perfil"
              >
                <Icon name="image" size={15} strokeWidth={2.2} />
              </button>
            </div>
            <div>
              <p className="account-identity-name">{user.nombre}</p>
              <p className="account-identity-role">{ROLE_NAMES[user.rol_id] || 'Usuario'}</p>
            </div>
          </div>

          <nav className="account-menu" aria-label="Secciones de la cuenta">
            {sections.map((section) => (
              <button
                key={section.key}
                type="button"
                className={`account-menu-item ${active === section.key ? 'active' : ''}`}
                aria-current={active === section.key ? 'page' : undefined}
                onClick={() => goTo(section.key)}
              >
                <Icon name={section.icon} size={19} />
                <span>{section.label}</span>
                {section.pending && <span className="account-pending" title="Pendiente" aria-label="Pendiente" />}
              </button>
            ))}

            {isClient && (
              <Link to="/reservations" className="account-menu-item">
                <Icon name="calendar" size={19} />
                <span>Mis reservas</span>
                <Icon name="arrowRight" size={16} className="account-menu-arrow" />
              </Link>
            )}
            {user.rol_id === ROLE_ADMIN && (
              <Link to="/admin" className="account-menu-item">
                <Icon name="grid" size={19} />
                <span>Consola</span>
                <Icon name="arrowRight" size={16} className="account-menu-arrow" />
              </Link>
            )}
          </nav>
        </aside>

        <input
          ref={photoInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(',')}
          className="visually-hidden"
          tabIndex={-1}
          onChange={handlePhotoSelected}
        />

        <div className="account-content">
          {photoStatus.text && active !== 'personal' && <StatusMessage status={photoStatus} />}
          {active === 'admin' && <AdminPanel user={user} />}
          {active === 'carnet' && renderCarnet()}
          {active === 'proveedor' && renderProvider()}
          {active === 'favoritos' && <FavoritesSection />}
          {active === 'resenas' && <ReviewsSection />}
          {active === 'personal' && renderPersonal()}
          {active === 'seguridad' && renderSecurity()}
        </div>
      </div>
    </section>
  );
}

export default Profile;
