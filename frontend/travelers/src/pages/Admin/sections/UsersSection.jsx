import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import Avatar from '../../../components/Avatar/Avatar';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import Modal from '../../../components/Modal/Modal';
import { formatDate, getErrorMessage } from '../../../utils/format';
import { matches, ROLE_NAMES, useAdminAction } from '../adminShared';
import ConfirmDeleteModal from './ConfirmDeleteModal';
import UserProfileView from './UserProfileView';

import Select from '../../../components/Select/Select';
const ROLE_FILTERS = [{ key: '', label: 'Todos' }, ...Object.entries(ROLE_NAMES).map(([key, label]) => ({ key, label }))];

function ResetPasswordModal({ target, onClose, onDone }) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [reviewing, setReviewing] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (password !== confirm) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    // Primer clic: pide confirmación; segundo clic: guarda
    if (!reviewing) {
      setError('');
      setReviewing(true);
      return;
    }

    setSaving(true);
    setError('');

    try {
      await api.patch(`/users/${target.id_usuario}/reset-password`, { new_password: password });
      onDone();
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible restablecer la contraseña.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Restablecer contraseña"
      subtitle={`${target.nombre} · ${target.email}`}
      size="small"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>Cancelar</button>
          {reviewing && (
            <button type="button" className="btn btn-secondary" onClick={() => setReviewing(false)} disabled={saving}>
              Volver
            </button>
          )}
          <button
            type="submit"
            form="reset-form"
            className={`btn ${reviewing ? 'btn-danger-solid' : 'btn-primary'}`}
            disabled={saving}
          >
            {saving ? 'Guardando...' : reviewing ? 'Sí, cambiar contraseña' : 'Continuar'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}
      {reviewing && (
        <div className="alert alert-warning" role="alert">
          <strong>¿Seguro que quieres cambiar la contraseña de {target.nombre}?</strong>
          <br />
          Su contraseña actual dejará de funcionar de inmediato y tendrá que entrar con la nueva.
          {target.google_conectado && ' Podrá seguir entrando con Google.'}
        </div>
      )}
      <form id="reset-form" onSubmit={handleSubmit} hidden={reviewing}>
        <div className="field">
          <label htmlFor="reset-pwd">Nueva contraseña</label>
          <input id="reset-pwd" type="password" autoComplete="new-password" minLength={6} value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="reset-confirm">Confirmar</label>
          <input id="reset-confirm" type="password" autoComplete="new-password" minLength={6} value={confirm} onChange={(event) => setConfirm(event.target.value)} required />
        </div>
        <p className="field-hint">Comunícale la nueva contraseña al usuario por un canal seguro.</p>
      </form>
    </Modal>
  );
}

function UsersSection({ user: currentUser, goTo, searchParams }) {
  const selectedId = Number(searchParams.get('usuario')) || null;
  const [users, setUsers] = useState(null);
  const [query, setQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [resetFor, setResetFor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { busy, message, error, run } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const response = await api.get('/users/');
    setUsers([...response.data].sort((a, b) => b.id_usuario - a.id_usuario));
  }, []);

  useEffect(() => {
    load().catch(() => setUsers([]));
  }, [load]);

  const changeRole = async (target, rol_id) => {
    const accepted = await confirm({
      title: 'Cambiar rol',
      subtitle: `${target.nombre} · ${target.email}`,
      message: `Pasará de ${ROLE_NAMES[target.rol_id]} a ${ROLE_NAMES[rol_id]}.`,
      details: Number(rol_id) === 1 ? ['Tendrá acceso completo a la consola de administración.'] : [],
      confirmLabel: 'Cambiar rol',
      tone: Number(rol_id) === 1 ? 'danger' : 'primary',
    });
    if (!accepted) return false;

    const { ok } = await run(
      () => api.patch(`/users/${target.id_usuario}/role`, { rol_id: Number(rol_id) }),
      `${target.nombre} ahora es ${ROLE_NAMES[rol_id]}.`
    );
    if (ok) await load();
    return ok;
  };

  const toggleActive = async (target) => {
    const activate = target.estado !== 'activo';
    const accepted = await confirm({
      title: activate ? 'Activar cuenta' : 'Desactivar cuenta',
      subtitle: `${target.nombre} · ${target.email}`,
      message: activate
        ? 'La persona podrá volver a iniciar sesión.'
        : 'La persona no podrá iniciar sesión hasta que reactives la cuenta. Sus reservas y datos se conservan.',
      confirmLabel: activate ? 'Activar' : 'Desactivar',
      tone: activate ? 'primary' : 'danger',
    });
    if (!accepted) return false;
    const { ok } = await run(
      () => api.patch(`/users/${target.id_usuario}/${activate ? 'activate' : 'deactivate'}`),
      `${target.nombre} ${activate ? 'activado' : 'desactivado'}.`
    );
    if (ok) await load();
    return ok;
  };

  const resetModal = resetFor && (
    <ResetPasswordModal
      target={resetFor}
      onClose={() => setResetFor(null)}
      onDone={async () => {
        const name = resetFor.nombre;
        setResetFor(null);
        await run(() => load(), `Contraseña de ${name} restablecida.`);
      }}
    />
  );

  if (selectedId) {
    return (
      <>
        <Toast text={message} />
        <Toast text={error} tone="error" />
        <UserProfileView
          key={selectedId}
          userId={selectedId}
          currentUser={currentUser}
          goTo={goTo}
          busy={busy}
          onBack={() => goTo('usuarios')}
          onResetPassword={setResetFor}
          onChangeRole={changeRole}
          onToggleActive={toggleActive}
        />
        {resetModal}
        {dialog}
      </>
    );
  }

  if (!users) return <p className="page-status">Cargando usuarios...</p>;

  const visible = users
    .filter((item) => !roleFilter || String(item.rol_id) === roleFilter)
    .filter((item) => !query || matches(item.nombre, query) || matches(item.email, query));

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Usuarios</h1>
          <p>{users.length} cuentas registradas.</p>
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
              placeholder="Buscar por nombre o correo"
              aria-label="Buscar usuarios"
            />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar por rol">
            {ROLE_FILTERS.map((option) => (
              <button
                key={option.key}
                type="button"
                className="chip"
                aria-pressed={roleFilter === option.key}
                onClick={() => setRoleFilter(option.key)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="usuarios">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Rol</th>
                <th>Acceso</th>
                <th>Desde</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => {
                const isMe = item.id_usuario === currentUser.id_usuario;
                const isActive = item.estado === 'activo';

                return (
                  <tr key={item.id_usuario}>
                    <td>
                      <button
                        type="button"
                        className="admin-thumb-cell user-row-link"
                        onClick={() => goTo('usuarios', { usuario: item.id_usuario })}
                        aria-label={`Ver la ficha de ${item.nombre}`}
                      >
                        <Avatar user={item} size={40} />
                        <span>
                          <span className="admin-strong">{item.nombre}{isMe && ' (tú)'}</span>
                          <br />
                          <span className="admin-muted">{item.email}</span>
                        </span>
                      </button>
                    </td>
                    <td>
                      <Select
                        className="admin-select"
                        value={item.rol_id}
                        disabled={busy || isMe}
                        aria-label={`Rol de ${item.nombre}`}
                        onChange={(event) => changeRole(item, event.target.value)}
                      >
                        {Object.entries(ROLE_NAMES).map(([id, label]) => (
                          <option key={id} value={id}>{label}</option>
                        ))}
                      </Select>
                    </td>
                    <td className="admin-muted">
                      {item.google_conectado ? 'Google' : ''}
                      {item.google_conectado && item.tiene_contrasena ? ' + ' : ''}
                      {item.tiene_contrasena ? 'Contraseña' : ''}
                      {item.verificacion_email !== 'verificado' && ' · correo sin verificar'}
                    </td>
                    <td className="admin-muted">{formatDate(item.fecha_creacion)}</td>
                    <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                    <td>
                      <div className="admin-actions">
                        <IconButton icon="eye" label="Ver ficha" variant="info" onClick={() => goTo('usuarios', { usuario: item.id_usuario })} />
                        <IconButton icon="key" label="Restablecer contraseña" onClick={() => setResetFor(item)} />
                        <IconButton
                          icon={isActive ? 'ban' : 'power'}
                          label={isActive ? 'Desactivar' : 'Activar'}
                          variant={isActive ? 'warning' : 'success'}
                          hidden={isMe}
                          disabled={busy}
                          onClick={() => toggleActive(item)}
                        />
                        <IconButton icon="trash" label="Eliminar" variant="danger" hidden={isMe} onClick={() => setDeleting(item)} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay usuarios con esos filtros.</p>}
        </div>
      </div>

      {deleting && (
        <ConfirmDeleteModal
          title="Eliminar usuario"
          name={`${deleting.nombre} · ${deleting.email}`}
          consequences={[
            'Solo se puede si no tiene reservas ni una empresa con productos; si no, desactívalo.',
            'Se borran su perfil de cliente, su solicitud de proveedor, su foto y sus notificaciones.',
          ]}
          request={() => api.delete(`/users/${deleting.id_usuario}`)}
          onClose={() => setDeleting(null)}
          onDeleted={async () => {
            const name = deleting.nombre;
            setDeleting(null);
            await run(() => load(), `${name} eliminado.`);
          }}
        />
      )}

      {resetModal}
      {dialog}
    </>
  );
}

export default UsersSection;
