import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import Avatar from '../../../components/Avatar/Avatar';
import Icon from '../../../components/Icon/Icon';
import PaymentOrderDetail from '../../../components/PaymentOrderDetail/PaymentOrderDetail';
import { downloadFile, openFile } from '../../../utils/download';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { ORDER_BADGE, ORDER_STATUS_LABELS } from '../../../utils/paymentOrders';
import { IVA_PERCENT } from '../../../utils/taxes';
import { PAYMENT_STATUS_LABELS } from '../adminShared';

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

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' }) : '';
}

/**
 * Ficha de una reserva dentro de la consola: viajero, acompañantes, pago con IVA
 * y órdenes a proveedores. Se usa desde Reservas (clic en el código) y desde Pagos
 * (clic en la referencia), con su propio botón de volver.
 */
function ReservationAdminView({ reservationId, goTo, onBack, backLabel = 'Volver a reservas', highlightPayment = false }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [fileError, setFileError] = useState('');
  const [orderDetail, setOrderDetail] = useState(null);

  useEffect(() => {
    api.get(`/reservations/${reservationId}/detail`)
      .then((response) => setData(response.data))
      .catch((requestError) => setError(getErrorMessage(requestError, 'No fue posible cargar la reserva.')));
  }, [reservationId]);

  const back = (
    <button type="button" className="btn btn-secondary btn-small user-file-back" onClick={onBack}>
      <Icon name="arrowLeft" size={16} /> {backLabel}
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
  if (!data) return <p className="page-status">Cargando reserva...</p>;

  const { reserva, viajero, acompanantes, paquete, pago, ordenes } = data;

  const voucher = async (download) => {
    setFileError('');
    try {
      if (download) await downloadFile(`/vouchers/${reserva.id_reserva}`, `voucher-${reserva.codigo_reserva}.pdf`);
      else await openFile(`/vouchers/${reserva.id_reserva}`);
    } catch (requestError) {
      setFileError(getErrorMessage(requestError, requestError.message || 'No fue posible abrir el voucher.'));
    }
  };

  const paymentSection = (
    <section className={`surface ${highlightPayment ? 'reservation-file-highlight' : ''}`}>
      <h2 className="user-file-title"><Icon name="card" size={18} /> Pago</h2>
      {pago ? (
        <dl className="user-file-fields">
          <Field label="Referencia">{pago.referencia_pago}</Field>
          <Field label="Método">{pago.metodo_pago}</Field>
          <Field label="Fecha">{formatDateTime(pago.fecha_pago)}</Field>
          <Field label="Estado">
            <span className={`badge badge-${pago.estado_pago === 'aprobado' ? 'aprobado' : 'pendiente'}`}>
              {PAYMENT_STATUS_LABELS[pago.estado_pago] || pago.estado_pago}
            </span>
          </Field>
          <Field label="Valor sin IVA">{formatCurrency(reserva.subtotal_sin_iva)}</Field>
          <Field label={`IVA (${IVA_PERCENT} %)`}>{formatCurrency(reserva.iva)}</Field>
          <Field label="Total pagado">{formatCurrency(pago.valor)}</Field>
          {reserva.reembolso != null && Number(reserva.reembolso) > 0 && (
            <Field label="Reembolsado">{formatCurrency(reserva.reembolso)}</Field>
          )}
        </dl>
      ) : (
        <Empty>
          {reserva.estado === 'pendiente'
            ? `Aún no se ha pagado.${reserva.vence_pago ? ` Plazo: ${formatDateTime(reserva.vence_pago)}.` : ''}`
            : 'Esta reserva no tiene pagos registrados.'}
        </Empty>
      )}
    </section>
  );

  return (
    <>
      {back}

      <header className="user-file-header surface">
        <span className="product-file-icon"><Icon name="ticket" size={40} /></span>
        <div className="user-file-identity">
          <p className="eyebrow">Reserva</p>
          <h1>{reserva.codigo_reserva}</h1>
          <p className="admin-muted">
            {paquete ? (
              <button type="button" className="link-button" onClick={() => goTo('paquetes', { paquete: paquete.id_paquete_turistico })}>
                {paquete.nombre}
              </button>
            ) : 'Paquete eliminado'}
            {' · '}viaje el {formatDate(reserva.fecha_reserva)}
          </p>
          <div className="user-file-badges">
            <span className={`badge badge-${reserva.estado}`}>{reserva.estado}</span>
            {reserva.vencida && <span className="badge badge-inactivo">vencida sin pago</span>}
          </div>
        </div>
        {reserva.estado === 'confirmada' && (
          <div className="user-file-actions">
            <button type="button" className="btn btn-secondary btn-small" onClick={() => voucher(false)}>Ver voucher</button>
            <button type="button" className="btn btn-secondary btn-small" onClick={() => voucher(true)}>Descargar</button>
          </div>
        )}
      </header>

      {fileError && <div className="alert alert-error">{fileError}</div>}

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Total (IVA incluido)</span>
          <strong>{formatCurrency(reserva.total_reserva)}</strong>
        </div>
        <div className="admin-stat">
          <span>Viajeros</span>
          <strong>{reserva.cantidad_personas}</strong>
        </div>
        <div className="admin-stat">
          <span>Comprada</span>
          <strong className="reservation-file-date">{formatDate(reserva.fecha_compra)}</strong>
        </div>
        {Number(reserva.descuento_cupon) > 0 && (
          <div className="admin-stat">
            <span>Descuento con cupón</span>
            <strong>{formatCurrency(reserva.descuento_cupon)}</strong>
          </div>
        )}
      </div>

      <div className="admin-two-columns">
        {highlightPayment && paymentSection}

        <section className="surface">
          <h2 className="user-file-title"><Icon name="user" size={18} /> Viajero titular</h2>
          <div className="reservation-file-traveler">
            <Avatar user={viajero} size={52} />
            <div>
              <p className="admin-strong">{viajero.nombre || '—'}</p>
              <p className="admin-muted">{viajero.email}</p>
            </div>
          </div>
          <dl className="user-file-fields user-file-spaced">
            <Field label="Identificación">{viajero.identificacion}</Field>
            <Field label="Nacimiento">{formatDate(viajero.fecha_nacimiento)}</Field>
          </dl>
          {viajero.id_usuario && (
            <button
              type="button"
              className="btn btn-secondary btn-small user-file-spaced"
              onClick={() => goTo('usuarios', { usuario: viajero.id_usuario })}
            >
              Ver ficha del viajero
            </button>
          )}
        </section>

        {!highlightPayment && paymentSection}
      </div>

      {reserva.fecha_cancelacion && (
        <section className="surface user-file-spaced">
          <h2 className="user-file-title"><Icon name="ban" size={18} /> Cancelación</h2>
          <dl className="user-file-fields">
            <Field label="Fecha">{formatDateTime(reserva.fecha_cancelacion)}</Field>
            <Field label="Motivo">{reserva.vencida ? 'No se pagó a tiempo' : 'Cancelada'}</Field>
            <Field label="Penalidad">{reserva.penalidad_cancelacion != null ? formatCurrency(reserva.penalidad_cancelacion) : '—'}</Field>
            <Field label="Reembolso">{reserva.reembolso != null ? formatCurrency(reserva.reembolso) : '—'}</Field>
          </dl>
        </section>
      )}

      <section className="surface user-file-spaced">
        <h2 className="user-file-title"><Icon name="users" size={18} /> Acompañantes ({acompanantes.length})</h2>
        {acompanantes.length === 0 ? <Empty>Viaja solo el titular.</Empty> : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Documento</th>
                  <th>Nacimiento</th>
                </tr>
              </thead>
              <tbody>
                {acompanantes.map((item) => (
                  <tr key={`${item.documento}-${item.nombre}`}>
                    <td className="admin-strong">{item.nombre}</td>
                    <td>{item.documento}</td>
                    <td className="admin-muted">{formatDate(item.fecha_nacimiento)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="surface user-file-spaced">
        <h2 className="user-file-title"><Icon name="dollar" size={18} /> Órdenes a proveedores ({ordenes.length})</h2>
        {ordenes.length === 0 ? <Empty>No hay órdenes (se crean al pagar la reserva).</Empty> : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Orden</th>
                  <th>Proveedor</th>
                  <th>Monto</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {ordenes.map((order) => (
                  <tr key={order.id_orden}>
                    <td>
                      <button type="button" className="link-button admin-strong" onClick={() => setOrderDetail(order)}>
                        {order.codigo}
                      </button>
                    </td>
                    <td>{order.nombre_proveedor}</td>
                    <td className="admin-strong">{formatCurrency(order.monto)}</td>
                    <td><span className={`badge badge-${ORDER_BADGE[order.estado]}`}>{ORDER_STATUS_LABELS[order.estado]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {orderDetail && <PaymentOrderDetail order={orderDetail} onClose={() => setOrderDetail(null)} />}
    </>
  );
}

export default ReservationAdminView;
