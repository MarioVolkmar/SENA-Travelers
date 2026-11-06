import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import Avatar from '../../../components/Avatar/Avatar';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import { openFile } from '../../../utils/download';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { ORDER_BADGE, ORDER_STATUS_LABELS } from '../../../utils/paymentOrders';
import { productTypeLabel, useProductTypes } from '../../../utils/productTypes';
import { PAYMENT_STATUS_LABELS, ROLE_NAMES } from '../adminShared';

import Select from '../../../components/Select/Select';
const EMAIL_STATUS = {
  enviado: { label: 'Enviado', badge: 'confirmada' },
  pendiente: { label: 'Pendiente', badge: 'pendiente' },
  fallido: { label: 'Falló', badge: 'cancelada' },
  desactivado: { label: 'Envío desactivado', badge: 'inactivo' },
};

const PAYMENT_BADGE = {
  aprobado: 'confirmada',
  reembolso_parcial: 'pendiente',
  reembolsado: 'cancelada',
  rechazado: 'cancelada',
  cancelado: 'cancelada',
};

function Field({ label, children }) {
  return (
    <div className="user-file-field">
      <dt>{label}</dt>
      <dd>{children || <span className="admin-muted">—</span>}</dd>
    </div>
  );
}

function Empty({ children }) {
  return <p className="admin-empty">{children}</p>;
}

function UserProfileView({ userId, currentUser, goTo, onBack, onResetPassword, onChangeRole, onToggleActive, busy }) {
  const types = useProductTypes();
  const [data, setData] = useState(null);
  const [cities, setCities] = useState([]);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('resumen');
  const [voucherError, setVoucherError] = useState('');

  const viewVoucher = async (reservation) => {
    setVoucherError('');
    try {
      await openFile(`/vouchers/${reservation.id_reserva}`);
    } catch (requestError) {
      setVoucherError(getErrorMessage(requestError, requestError.message || 'No fue posible abrir el voucher.'));
    }
  };

  const load = useCallback(async () => {
    try {
      const [overview, citiesResponse] = await Promise.all([
        api.get(`/users/${userId}/overview`),
        api.get('/cities/').catch(() => ({ data: [] })),
      ]);
      setData(overview.data);
      setCities(citiesResponse.data);
      setError('');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible cargar la ficha del usuario.'));
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const back = (
    <button type="button" className="btn btn-secondary btn-small user-file-back" onClick={onBack}>
      <Icon name="arrowLeft" size={16} /> Volver a usuarios
    </button>
  );

  if (error) {
    return (
      <>
        {back}
        <div className="alert alert-error">{error}</div>
      </>
    );
  }

  if (!data) return <p className="page-status">Cargando ficha...</p>;

  const { usuario, cliente, proveedor, reservas, pagos, productos, ordenes_pago: ordenes, notificaciones, resumen } = data;
  const isMe = usuario.id_usuario === currentUser.id_usuario;
  const isActive = usuario.estado === 'activo';
  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || (id ? `#${id}` : '');
  const reservationCode = (id) => reservas.find((item) => item.id_reserva === id)?.codigo_reserva || `#${id}`;

  const access = [usuario.google_conectado && 'Google', usuario.tiene_contrasena && 'Contraseña'].filter(Boolean).join(' + ');

  const tabs = [
    { key: 'resumen', label: 'Resumen' },
    { key: 'reservas', label: 'Reservas', count: reservas.length },
    { key: 'pagos', label: 'Pagos', count: pagos.length },
    proveedor && { key: 'proveedor', label: 'Proveedor', count: productos.length },
    { key: 'notificaciones', label: 'Correos', count: notificaciones.length },
  ].filter(Boolean);

  // Las acciones rápidas recargan la ficha al terminar
  const act = (action) => async () => {
    const ok = await action(usuario);
    if (ok) await load();
  };

  return (
    <>
      {back}

      <header className="user-file-header surface">
        <Avatar user={usuario} size={88} />
        <div className="user-file-identity">
          <p className="eyebrow">Ficha #{usuario.id_usuario}</p>
          <h1>{usuario.nombre}{isMe && ' (tú)'}</h1>
          <p className="admin-muted">{usuario.email}</p>
          <div className="user-file-badges">
            <span className="badge badge-activo">{ROLE_NAMES[usuario.rol_id]}</span>
            <span className={`badge badge-${usuario.estado}`}>{usuario.estado}</span>
            <span className={`badge badge-${usuario.verificacion_email === 'verificado' ? 'verificado' : 'pendiente'}`}>
              {usuario.verificacion_email === 'verificado' ? 'correo verificado' : 'correo sin verificar'}
            </span>
            {proveedor && (
              <span className={`badge badge-${proveedor.estado_verificacion}`}>proveedor {proveedor.estado_verificacion}</span>
            )}
          </div>
        </div>

        <div className="user-file-actions">
          <Select
            className="admin-select"
            value={usuario.rol_id}
            disabled={busy || isMe}
            aria-label="Cambiar rol"
            onChange={async (event) => {
              const ok = await onChangeRole(usuario, event.target.value);
              if (ok) await load();
            }}
          >
            {Object.entries(ROLE_NAMES).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </Select>
          <button type="button" className="btn btn-secondary btn-small" onClick={() => onResetPassword(usuario)}>
            Contraseña
          </button>
          {!isMe && (
            <button
              type="button"
              className={`btn btn-small ${isActive ? 'btn-danger' : 'btn-primary'}`}
              disabled={busy}
              onClick={act(onToggleActive)}
            >
              {isActive ? 'Desactivar' : 'Activar'}
            </button>
          )}
        </div>
      </header>

      <div className="admin-summary">
        <div className="admin-stat">
          <span>Reservas</span>
          <strong>{resumen.reservas}</strong>
        </div>
        <div className="admin-stat">
          <span>Viajes confirmados</span>
          <strong>{resumen.reservas_confirmadas}</strong>
        </div>
        <div className="admin-stat highlight">
          <span>Total pagado</span>
          <strong>{formatCurrency(resumen.total_pagado)}</strong>
        </div>
        {Number(resumen.penalidades) > 0 && (
          <div className="admin-stat warning">
            <span>Penalidades</span>
            <strong>{formatCurrency(resumen.penalidades)}</strong>
          </div>
        )}
        {proveedor && (
          <div className="admin-stat">
            <span>Por cobrar (proveedor)</span>
            <strong>{formatCurrency(resumen.por_cobrar)}</strong>
          </div>
        )}
      </div>

      <div className="user-file-tabs" role="tablist" aria-label="Información del usuario">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={tab === item.key}
            className="chip"
            aria-pressed={tab === item.key}
            onClick={() => setTab(item.key)}
          >
            {item.label}
            {item.count > 0 && <span className="user-file-count">{item.count}</span>}
          </button>
        ))}
      </div>

      {tab === 'resumen' && (
        <div className="admin-two-columns">
          <section className="surface">
            <h2 className="user-file-title"><Icon name="user" size={18} /> Cuenta</h2>
            <dl className="user-file-fields">
              <Field label="Nombre">{usuario.nombre}</Field>
              <Field label="Correo">{usuario.email}</Field>
              <Field label="Rol">{ROLE_NAMES[usuario.rol_id]}</Field>
              <Field label="Acceso">{access}</Field>
              <Field label="Registrado">{formatDate(usuario.fecha_creacion)}</Field>
              <Field label="Estado">{usuario.estado}</Field>
            </dl>
          </section>

          <section className="surface">
            <h2 className="user-file-title"><Icon name="ticket" size={18} /> Perfil de viajero</h2>
            {cliente ? (
              <dl className="user-file-fields">
                <Field label="Identificación">{cliente.identificacion}</Field>
                <Field label="Nacimiento">{formatDate(cliente.fecha_nacimiento)}</Field>
                <Field label="Ciudad">{cityName(cliente.ciudad_id)}</Field>
                <Field label="ID cliente">#{cliente.id_cliente}</Field>
              </dl>
            ) : (
              <Empty>Aún no completa su perfil de viajero.</Empty>
            )}
          </section>

          {proveedor && (
            <section className="surface">
              <h2 className="user-file-title"><Icon name="building" size={18} /> Empresa</h2>
              <dl className="user-file-fields">
                <Field label="Empresa">{proveedor.nombre_empresa}</Field>
                <Field label="RUT">{proveedor.rut}</Field>
                <Field label="Teléfono">{proveedor.telefono}</Field>
                <Field label="Dirección">{proveedor.direccion}</Field>
                <Field label="Ciudad">{cityName(proveedor.ciudad_id)}</Field>
                <Field label="Solicitud">{formatDate(proveedor.fecha_solicitud)}</Field>
                <Field label="Verificación">{proveedor.estado_verificacion}</Field>
              </dl>
            </section>
          )}

          {proveedor && (
            <section className="surface">
              <h2 className="user-file-title"><Icon name="card" size={18} /> Datos bancarios</h2>
              {proveedor.numero_cuenta ? (
                <dl className="user-file-fields">
                  <Field label="Banco">{proveedor.banco}</Field>
                  <Field label="Tipo">{proveedor.tipo_cuenta}</Field>
                  <Field label="Número">{proveedor.numero_cuenta}</Field>
                  <Field label="Titular">{proveedor.titular_cuenta}</Field>
                </dl>
              ) : (
                <Empty>No ha registrado una cuenta para recibir pagos.</Empty>
              )}
            </section>
          )}
        </div>
      )}

      {tab === 'reservas' && (
        <div className="surface">
          {voucherError && <div className="alert alert-error">{voucherError}</div>}
          {reservas.length === 0 ? <Empty>No tiene reservas.</Empty> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reserva</th>
                    <th>Fecha del viaje</th>
                    <th>Viajeros</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th><span className="visually-hidden">Voucher</span></th>
                  </tr>
                </thead>
                <tbody>
                  {reservas.map((item) => (
                    <tr key={item.id_reserva}>
                      <td>
                        <span className="admin-strong">{item.paquete}</span>
                        <br />
                        <span className="admin-muted">{item.codigo_reserva} · comprada {formatDate(item.fecha_compra)}</span>
                      </td>
                      <td>{formatDate(item.fecha_reserva)}</td>
                      <td>
                        {item.cantidad_personas}
                        {item.acompanantes.length > 0 && (
                          <span className="admin-muted user-file-companions">
                            {item.acompanantes.map((person) => `${person.nombre} (${person.documento})`).join(', ')}
                          </span>
                        )}
                      </td>
                      <td>
                        <span className="admin-strong">{formatCurrency(item.total_reserva)}</span>
                        {item.fecha_cancelacion && (
                          <span className="admin-muted user-file-companions">
                            Cancelada {formatDate(item.fecha_cancelacion)}
                            {Number(item.penalidad_cancelacion) > 0 && ` · penalidad ${formatCurrency(item.penalidad_cancelacion)}`}
                            {Number(item.reembolso) > 0 && ` · reembolso ${formatCurrency(item.reembolso)}`}
                          </span>
                        )}
                      </td>
                      <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                      <td>
                        <IconButton
                          icon="eye"
                          label="Ver voucher (PDF)"
                          variant="info"
                          hidden={item.estado !== 'confirmada'}
                          onClick={() => viewVoucher(item)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'pagos' && (
        <div className="surface">
          {pagos.length === 0 ? <Empty>No tiene pagos registrados.</Empty> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Referencia</th>
                    <th>Reserva</th>
                    <th>Método</th>
                    <th>Fecha</th>
                    <th>Valor</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {pagos.map((payment) => (
                    <tr key={payment.id_pago}>
                      <td className="admin-strong">{payment.referencia_pago}</td>
                      <td className="admin-muted">{reservationCode(payment.reserva_id)}</td>
                      <td>{payment.metodo_pago}</td>
                      <td className="admin-muted">{formatDate(payment.fecha_pago)}</td>
                      <td className="admin-strong">{formatCurrency(payment.valor)}</td>
                      <td>
                        <span className={`badge badge-${PAYMENT_BADGE[payment.estado_pago] || 'pendiente'}`}>
                          {PAYMENT_STATUS_LABELS[payment.estado_pago] || payment.estado_pago}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'proveedor' && proveedor && (
        <>
          <div className="surface">
            <h2 className="user-file-title"><Icon name="box" size={18} /> Productos ({productos.length})</h2>
            {productos.length === 0 ? <Empty>No ha creado productos.</Empty> : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Producto</th>
                      <th>Tipo</th>
                      <th>Costo</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productos.map((product) => (
                      <tr key={product.id_producto}>
                        <td>
                          <span className="admin-strong">{product.nombre}</span>
                          <br />
                          <span className="admin-muted">{cityName(product.ciudad_id)}</span>
                        </td>
                        <td>{productTypeLabel(types, product.tipo_producto)}</td>
                        <td>{formatCurrency(product.costo)}</td>
                        <td><span className={`badge badge-${product.estado}`}>{product.estado}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="surface user-file-spaced">
            <div className="user-file-title-row">
              <h2 className="user-file-title"><Icon name="card" size={18} /> Órdenes de pago ({ordenes.length})</h2>
              <span className="admin-muted">Cobrado {formatCurrency(resumen.cobrado)} · por cobrar {formatCurrency(resumen.por_cobrar)}</span>
            </div>
            {ordenes.length === 0 ? <Empty>Sin órdenes de pago.</Empty> : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Orden</th>
                      <th>Viaje</th>
                      <th>Vence</th>
                      <th>Monto</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordenes.map((order) => (
                      <tr key={order.id_orden}>
                        <td>
                          <span className="admin-strong">{order.codigo}</span>
                          <br />
                          <span className="admin-muted">{order.paquete} · {order.codigo_reserva}</span>
                        </td>
                        <td className="admin-muted">{formatDate(order.fecha_viaje)} · {order.viajeros} viajeros</td>
                        <td className="admin-muted">{formatDate(order.fecha_vencimiento)}</td>
                        <td className="admin-strong">{formatCurrency(order.monto)}</td>
                        <td><span className={`badge badge-${ORDER_BADGE[order.estado]}`}>{ORDER_STATUS_LABELS[order.estado]}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {ordenes.length > 0 && (
              <button
                type="button"
                className="btn btn-secondary btn-small user-file-spaced"
                onClick={() => goTo('pagos-proveedores')}
              >
                Gestionar en Pagos a proveedores
              </button>
            )}
          </div>
        </>
      )}

      {tab === 'notificaciones' && (
        <div className="surface">
          {notificaciones.length === 0 ? <Empty>No se le han enviado correos.</Empty> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asunto</th>
                    <th>Tipo</th>
                    <th>Fecha</th>
                    <th>Envío</th>
                  </tr>
                </thead>
                <tbody>
                  {notificaciones.map((item) => (
                    <tr key={item.id_notificacion_email}>
                      <td className="admin-strong">{item.asunto}</td>
                      <td className="admin-muted">{item.tipo_notificacion.replaceAll('_', ' ')}</td>
                      <td className="admin-muted">{formatDate(item.fecha_envio)}</td>
                      <td>
                        <span className={`badge badge-${EMAIL_STATUS[item.estado_envio]?.badge || 'pendiente'}`}>
                          {EMAIL_STATUS[item.estado_envio]?.label || item.estado_envio}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default UserProfileView;
