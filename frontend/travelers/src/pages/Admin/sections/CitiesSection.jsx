import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import IconButton from '../../../components/IconButton/IconButton';
import Icon from '../../../components/Icon/Icon';
import Toast from '../../../components/Toast/Toast';
import { useAdminAction } from '../adminShared';
import NumberField, { numberError } from '../../../components/NumberField/NumberField';

const LATITUDE = { min: -90, max: 90 };
const LONGITUDE = { min: -180, max: 180 };

const EMPTY_FORM = { nombre: '', departamento: '', pais: 'Colombia', latitud: '', longitud: '' };

function toForm(city) {
  return {
    nombre: city.nombre,
    departamento: city.departamento,
    pais: city.pais,
    latitud: city.latitud ?? '',
    longitud: city.longitud ?? '',
  };
}

function CitiesSection() {
  const [cities, setCities] = useState(null);
  const [packages, setPackages] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState(null);
  const [manualCoords, setManualCoords] = useState(false);
  const { busy, message, error, run } = useAdminAction();

  const load = useCallback(async () => {
    const [citiesResponse, packagesResponse] = await Promise.all([api.get('/cities/'), api.get('/packages/admin')]);
    setCities(citiesResponse.data);
    setPackages(packagesResponse.data);
  }, []);

  useEffect(() => {
    load().catch(() => setCities([]));
  }, [load]);

  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const cancelEdit = () => {
    setEditing(null);
    setManualCoords(false);
    setForm(EMPTY_FORM);
  };

  const locate = async () => {
    const { ok, result } = await run(
      () => api.patch(`/cities/${editing.id_ciudad}`, {
        nombre: form.nombre.trim(),
        departamento: form.departamento.trim(),
        recalcular_ubicacion: true,
      }),
      null,
      'No se encontró la ubicación.'
    );
    if (ok) {
      setForm(toForm(result.data));
      setEditing(result.data);
      await load();
      await run(async () => {}, `Ubicación de ${result.data.nombre}: ${Number(result.data.latitud).toFixed(4)}, ${Number(result.data.longitud).toFixed(4)}.`);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const coords = {
      latitud: form.latitud === '' ? null : Number(form.latitud),
      longitud: form.longitud === '' ? null : Number(form.longitud),
    };
    const name = form.nombre.trim();
    // Al crear sin coordenadas manuales, el servidor busca la ubicación solo
    const sendCoords = editing || manualCoords;

    const { ok, result } = await run(
      () => (editing
        ? api.patch(`/cities/${editing.id_ciudad}`, { nombre: name, departamento: form.departamento.trim(), ...coords })
        : api.post('/cities/', {
          nombre: name,
          departamento: form.departamento.trim(),
          pais: form.pais.trim(),
          ...(sendCoords ? coords : {}),
        })),
      null,
      'No fue posible guardar la ciudad.'
    );

    if (ok) {
      const saved = result.data;
      const located = saved.latitud !== null && saved.longitud !== null;
      cancelEdit();
      await load();
      await run(async () => {}, editing
        ? `${name} actualizada.`
        : located
          ? `${name} agregada y ubicada en el mapa (${Number(saved.latitud).toFixed(4)}, ${Number(saved.longitud).toFixed(4)}).`
          : `${name} agregada, pero no se encontró su ubicación: edítala para ponerla a mano.`);
    }
  };

  if (!cities) return <p className="page-status">Cargando ciudades...</p>;

  const packageCount = (id) => packages.filter((item) => item.ciudad_id === id).length;
  const withoutCoords = cities.filter((city) => city.latitud === null || city.longitud === null).length;

  const coordsInvalid = Boolean(
    numberError(form.latitud ?? '', LATITUDE, { optional: true, decimals: true })
    || numberError(form.longitud ?? '', LONGITUDE, { optional: true, decimals: true })
  );

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Ciudades</h1>
          <p>Destinos para paquetes, productos y clientes. Con su ubicación aparecen en el mapa de la portada.</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="admin-two-columns">
        <form className="surface" onSubmit={handleSubmit}>
          <div className="admin-panel-header">
            <h2>{editing ? `Editar ${editing.nombre}` : 'Agregar ciudad'}</h2>
          </div>
          <div className="field">
            <label htmlFor="city-name">Nombre</label>
            <input id="city-name" value={form.nombre} onChange={update('nombre')} minLength={2} maxLength={45} required />
          </div>
          <div className="field">
            <label htmlFor="city-department">Departamento</label>
            <input id="city-department" value={form.departamento} onChange={update('departamento')} minLength={2} maxLength={45} required />
          </div>
          {!editing && (
            <div className="field">
              <label htmlFor="city-country">País</label>
              <input id="city-country" value={form.pais} onChange={update('pais')} minLength={2} maxLength={45} required />
            </div>
          )}
          {!editing && !manualCoords ? (
            <p className="admin-auto-location">
              <Icon name="pin" size={16} />
              <span>
                La ubicación en el mapa se busca sola con el nombre y el departamento.{' '}
                <button type="button" className="link-button" onClick={() => setManualCoords(true)}>
                  Escribir coordenadas a mano
                </button>
              </span>
            </p>
          ) : (
            <>
              <div className="admin-coords">
                <NumberField
                  id="city-lat"
                  label="Latitud"
                  placeholder="6.244203"
                  value={form.latitud ?? ''}
                  onChange={update('latitud')}
                  range={LATITUDE}
                  optional
                  decimals
                />
                <NumberField
                  id="city-lng"
                  label="Longitud"
                  placeholder="-75.581212"
                  value={form.longitud ?? ''}
                  onChange={update('longitud')}
                  range={LONGITUDE}
                  optional
                  decimals
                />
              </div>
              <p className="field-hint">
                {editing
                  ? 'Usa «Buscar ubicación» para calcularla de nuevo, o escríbela a mano (en Google Maps: clic derecho sobre la ciudad).'
                  : 'Déjalas vacías para que se busquen solas.'}
              </p>
              {editing && (
                <button type="button" className="btn btn-secondary btn-small admin-locate" onClick={locate} disabled={busy}>
                  <Icon name="pin" size={16} /> Buscar ubicación
                </button>
              )}
            </>
          )}
          <div className="admin-form-actions">
            {editing && (
              <button type="button" className="btn btn-secondary" onClick={cancelEdit} disabled={busy}>Cancelar</button>
            )}
            <button type="submit" className="btn btn-primary" disabled={busy || coordsInvalid}>
              {busy ? (editing ? 'Guardando...' : 'Agregando y ubicando...') : editing ? 'Guardar cambios' : 'Agregar ciudad'}
            </button>
          </div>
        </form>

        <div className="surface">
          <div className="admin-panel-header">
            <h2>{cities.length} ciudades</h2>
            {withoutCoords > 0 && <span className="badge badge-pendiente">{withoutCoords} sin ubicación</span>}
          </div>
          <ul className="admin-list">
            {cities.map((city) => {
              const hasCoords = city.latitud !== null && city.longitud !== null;
              return (
                <li key={city.id_ciudad}>
                  <span>
                    <span className="admin-strong">{city.nombre}</span>
                    <span className="admin-muted"> · {city.departamento}, {city.pais}</span>
                    <br />
                    <span className={`admin-city-coords ${hasCoords ? '' : 'is-missing'}`}>
                      <Icon name="pin" size={13} />
                      {hasCoords ? `${Number(city.latitud).toFixed(3)}, ${Number(city.longitud).toFixed(3)}` : 'Sin ubicación en el mapa'}
                    </span>
                  </span>
                  <span className="admin-city-side">
                    <span className="admin-muted">
                      {packageCount(city.id_ciudad)} {packageCount(city.id_ciudad) === 1 ? 'paquete' : 'paquetes'}
                    </span>
                    <IconButton icon="edit" label="Editar" onClick={() => { setEditing(city); setForm(toForm(city)); }} />
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </>
  );
}

export default CitiesSection;
