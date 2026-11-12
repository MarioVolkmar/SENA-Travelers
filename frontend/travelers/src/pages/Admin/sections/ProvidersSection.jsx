import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import { formatDate } from '../../../utils/format';
import { matches, useAdminAction } from '../adminShared';
import ConfirmDeleteModal from './ConfirmDeleteModal';
import UserProfileView from './UserProfileView';
import Avatar from '../../../components/Avatar/Avatar';

const FILTERS = [
  { key: '', label: 'Todos' },
  { key: 'pendiente', label: 'Pendientes' },
  { key: 'aprobado', label: 'Aprobados' },
  { key: 'rechazado', label: 'Rechazados' },
];

function ProvidersSection({ onDataChanged, goTo, searchParams, user: currentUser }) {
  // Ficha del proveedor dentro de la consola: ?seccion=proveedores&ficha=<id usuario>&pestana=productos|ordenes
  const fileUserId = Number(searchParams?.get('ficha')) || null;
  const fileTab = searchParams?.get('pestana') || 'resumen';
  const [providers, setProviders] = useState(null);
  const [users, setUsers] = useState({});
  const [cities, setCities] = useState([]);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [deleting, setDeleting] = useState(null);
  const { busy, message, error, run } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const [providersResponse, citiesResponse, usersResponse] = await Promise.all([
      api.get('/providers/'),
      api.get('/cities/'),
      api.get('/users/').catch(() => ({ data: [] })),
    ]);
    // Nombre y foto de la cuenta de cada proveedor, para el avatar
    setUsers(Object.fromEntries(usersResponse.data.map((item) => [item.id_usuario, item])));

    // Los pendientes primero
    const order = { pendiente: 0, aprobado: 1, rechazado: 2 };
    setProviders([...providersResponse.data].sort(
      (a, b) => (order[a.estado_verificacion] ?? 3) - (order[b.estado_verificacion] ?? 3)
    ));
    setCities(citiesResponse.data);
  }, []);

  useEffect(() => {
    load().catch(() => setProviders([]));
  }, [load]);

  const setVerification = async (provider, estado) => {
    const approving = estado === 'aprobado';
    const accepted = await confirm({
      title: approving ? 'Aprobar proveedor' : 'Rechazar proveedor',
      subtitle: `${provider.nombre_empresa} · RUT ${provider.rut}`,
      message: approving
        ? 'La cuenta pasará a rol proveedor y podrá crear productos y recibir órdenes de pago.'
        : 'La solicitud quedará rechazada. El usuario podrá corregirla y volver a enviarla.',
      confirmLabel: approving ? 'Aprobar' : 'Rechazar',
      tone: approving ? 'primary' : 'danger',
    });
    if (!accepted) return;

    const { ok } = await run(
      () => api.patch(`/providers/${provider.id_proveedor}/verification-status`, { estado_verificacion: estado }),
      `${provider.nombre_empresa}: ${estado}.`
    );

    if (ok) {
      await load();
      onDataChanged();
    }
  };

  const openFile = (provider, tab) => goTo('proveedores', {
    ficha: provider.usuario_id,
    ...(tab ? { pestana: tab } : {}),
  });

  if (fileUserId) {
    return (
      <UserProfileView
        key={`${fileUserId}-${fileTab}`}
        userId={fileUserId}
        currentUser={currentUser}
        goTo={goTo}
        backLabel="Volver a proveedores"
        initialTab={fileTab}
        onBack={() => goTo('proveedores')}
      />
    );
  }

  if (!providers) return <p className="page-status">Cargando proveedores...</p>;

  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || '';
  const visible = providers
    .filter((item) => !filter || item.estado_verificacion === filter)
    .filter((item) => !query || matches(item.nombre_empresa, query) || matches(item.rut, query));

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Proveedores</h1>
          <p>Solo los proveedores aprobados pueden ofrecer productos en los paquetes.</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por empresa o RUT"
              aria-label="Buscar proveedores"
            />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar por verificación">
            {FILTERS.map((option) => (
              <button
                key={option.key}
                type="button"
                className="chip"
                aria-pressed={filter === option.key}
                onClick={() => setFilter(option.key)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="proveedores">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Empresa</th>
                <th>RUT</th>
                <th>Contacto</th>
                <th>Solicitud</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((provider) => (
                <tr key={provider.id_proveedor}>
                  <td>
                    {/* Avatar y nombre abren la ficha del proveedor */}
                    <button
                      type="button"
                      className="admin-thumb-cell admin-thumb-link"
                      onClick={() => openFile(provider)}
                      aria-label={`Ver la ficha de ${provider.nombre_empresa}`}
                    >
                      <Avatar user={users[provider.usuario_id] || { nombre: provider.nombre_empresa }} size={40} />
                      <span>
                        <span className="admin-strong">{provider.nombre_empresa}</span>
                        <br />
                        <span className="admin-muted">{cityName(provider.ciudad_id)}</span>
                      </span>
                    </button>
                  </td>
                  <td>{provider.rut}</td>
                  <td className="admin-muted">{provider.telefono} · {provider.direccion}</td>
                  <td className="admin-muted">{formatDate(provider.fecha_solicitud)}</td>
                  <td>
                    <span className={`badge badge-${provider.estado_verificacion}`}>{provider.estado_verificacion}</span>
                  </td>
                  <td>
                    <div className="admin-actions">
                      <IconButton
                        icon="eye"
                        label="Ver ficha"
                        variant="info"
                        onClick={() => openFile(provider)}
                      />
                      <IconButton
                        icon="box"
                        label="Ver productos"
                        hidden={provider.estado_verificacion !== 'aprobado'}
                        onClick={() => openFile(provider, 'productos')}
                      />
                      <IconButton
                        icon="dollar"
                        label="Órdenes de pago"
                        variant="primary"
                        hidden={provider.estado_verificacion !== 'aprobado'}
                        onClick={() => openFile(provider, 'ordenes')}
                      />
                      <IconButton
                        icon="check"
                        label="Aprobar"
                        variant="success"
                        hidden={provider.estado_verificacion === 'aprobado'}
                        disabled={busy}
                        onClick={() => setVerification(provider, 'aprobado')}
                      />
                      <IconButton
                        icon="close"
                        label="Rechazar"
                        variant="warning"
                        hidden={provider.estado_verificacion === 'rechazado'}
                        disabled={busy}
                        onClick={() => setVerification(provider, 'rechazado')}
                      />
                      <IconButton
                        icon="trash"
                        label="Eliminar"
                        variant="danger"
                        hidden={provider.estado_verificacion !== 'rechazado'}
                        onClick={() => setDeleting(provider)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay proveedores con esos filtros.</p>}
        </div>
      </div>

      {deleting && (
        <ConfirmDeleteModal
          title="Eliminar proveedor"
          name={`${deleting.nombre_empresa} · RUT ${deleting.rut}`}
          consequences={[
            'Se borra la solicitud de proveedor rechazada.',
            'La cuenta del usuario se conserva como viajero y podrá volver a solicitar.',
          ]}
          request={() => api.delete(`/providers/${deleting.id_proveedor}`)}
          onClose={() => setDeleting(null)}
          onDeleted={async () => {
            const name = deleting.nombre_empresa;
            setDeleting(null);
            await run(() => load(), `${name} eliminado.`);
            onDataChanged();
          }}
        />
      )}
      {dialog}
    </>
  );
}

export default ProvidersSection;
