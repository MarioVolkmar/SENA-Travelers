import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import fallbackImage from '../../../assets/images/fondo.png';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { daysLabel, orderUrgency } from '../../../utils/paymentOrders';

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Buenos días';
  if (hour < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

function SummarySection({ user, goTo }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [reservations, payments, packages, providers, users, covers, orders, schedule] = await Promise.all([
          api.get('/reservations/'),
          api.get('/payments/'),
          api.get('/packages/admin'),
          api.get('/providers/pending'),
          api.get('/users/'),
          api.get('/packages/images/covers').catch(() => ({ data: [] })),
          api.get('/provider-payments/').catch(() => ({ data: [] })),
          api.get('/provider-payments/schedule').catch(() => ({ data: null })),
        ]);

        setData({
          reservations: [...reservations.data].sort((a, b) => b.id_reserva - a.id_reserva),
          payments: payments.data,
          packages: packages.data,
          pendingProviders: providers.data,
          users: users.data,
          covers: Object.fromEntries(covers.data.map((cover) => [cover.paquete_id, cover.imagen_url])),
          orders: orders.data,
          schedule: schedule.data,
        });
      } catch (requestError) {
        setError(getErrorMessage(requestError, 'No fue posible cargar el resumen.'));
      }
    };

    load();
  }, []);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data) return <p className="page-status">Cargando resumen...</p>;

  const packageName = (id) =>
    data.packages.find((item) => item.id_paquete_turistico === id)?.nombre || `Paquete #${id}`;

  // Ventas = pagos aprobados + lo que se retuvo como penalidad en reembolsos parciales
  // (los pagos reembolsados por cancelación ya no cuentan como venta)
  const penalties = data.reservations.reduce((sum, item) => sum + Number(item.penalidad_cancelacion || 0), 0);
  const approvedSales = data.payments
    .filter((payment) => payment.estado_pago === 'aprobado')
    .reduce((sum, payment) => sum + Number(payment.valor), 0) + penalties;
  const activeReservations = data.reservations.filter((item) => item.estado !== 'cancelada');
  const cancelledCount = data.reservations.length - activeReservations.length;
  const pendingReservations = data.reservations.filter((item) => item.estado === 'pendiente');
  const upcomingEnds = data.packages.filter((item) => item.estado === 'activo');

  // Órdenes de pago a proveedores
  const pendingOrders = data.orders.filter((order) => order.estado === 'pendiente');
  const approvedOrders = data.orders.filter((order) => order.estado === 'aprobada');
  const sumOrders = (list) => list.reduce((sum, order) => sum + Number(order.monto), 0);
  const urgentOrders = [...pendingOrders, ...approvedOrders]
    .map((order) => ({ order, urgency: orderUrgency(order) }))
    .sort((a, b) => a.urgency.sortKey - b.urgency.sortKey);
  const overdueOrders = urgentOrders.filter((item) => ['overdue', 'urgent'].includes(item.urgency.level)).length;

  const cards = [
    { label: 'Ventas netas', value: formatCurrency(approvedSales), highlight: true, section: 'pagos' },
    { label: 'Penalidades cobradas', value: formatCurrency(penalties), section: 'reservas' },
    {
      label: cancelledCount > 0 ? `Reservas activas (${cancelledCount} canceladas)` : 'Reservas activas',
      value: activeReservations.length,
      section: 'reservas',
    },
    {
      label: 'Pendientes de pago',
      value: pendingReservations.length,
      warning: pendingReservations.length > 0,
      section: 'reservas',
    },
    { label: 'Paquetes activos', value: upcomingEnds.length, section: 'paquetes' },
    {
      label: `Órdenes por aprobar (${formatCurrency(sumOrders(pendingOrders))})`,
      value: pendingOrders.length,
      warning: overdueOrders > 0,
      section: 'pagos-proveedores',
    },
    {
      label: data.schedule ? `Por pagar el ${formatDate(data.schedule.proximo_pago)}` : 'Aprobadas por pagar',
      value: formatCurrency(sumOrders(approvedOrders)),
      section: 'pagos-proveedores',
    },
    {
      label: 'Proveedores por aprobar',
      value: data.pendingProviders.length,
      warning: data.pendingProviders.length > 0,
      section: 'proveedores',
    },
  ];

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>{greeting()}, {user.nombre.split(' ')[0]}</h1>
          <p>Resumen de la operación de Travelers.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => goTo('paquetes', { nuevo: '1' })}>
          + Nuevo paquete
        </button>
      </div>

      <div className="admin-summary">
        {cards.map((card) => (
          <button
            key={card.label}
            type="button"
            className={`admin-stat ${card.highlight ? 'highlight' : ''} ${card.warning ? 'warning' : ''}`}
            onClick={() => goTo(card.section)}
          >
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </button>
        ))}
      </div>

      {urgentOrders.length > 0 && (
        <div className="surface" style={{ marginBottom: 20 }}>
          <div className="admin-panel-header">
            <h2>Pagos a proveedores más próximos</h2>
            <button type="button" className="btn btn-secondary btn-small" onClick={() => goTo('pagos-proveedores')}>
              Gestionar
            </button>
          </div>
          <ul className="admin-list">
            {urgentOrders.slice(0, 5).map(({ order, urgency }) => (
              <li key={order.id_orden} className={`order-urgency order-urgency-${urgency.level}`}>
                <span className="admin-strong">{order.codigo} · {order.nombre_proveedor} · {formatCurrency(order.monto)}</span>
                <span className="admin-muted">
                  {urgency.label} <strong>{formatDate(urgency.date)}</strong> ({daysLabel(urgency.days)})
                  {!order.tiene_datos_bancarios && ' · sin datos bancarios'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.pendingProviders.length > 0 && (
        <div className="surface" style={{ marginBottom: 20 }}>
          <div className="admin-panel-header">
            <h2>Proveedores esperando aprobación</h2>
            <button type="button" className="btn btn-secondary btn-small" onClick={() => goTo('proveedores')}>
              Revisar
            </button>
          </div>
          <ul className="admin-list">
            {data.pendingProviders.slice(0, 4).map((provider) => (
              <li key={provider.id_proveedor}>
                <span className="admin-strong">{provider.nombre_empresa}</span>
                <span className="admin-muted">Solicitud del {formatDate(provider.fecha_solicitud)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="surface">
        <div className="admin-panel-header">
          <h2>Últimas reservas</h2>
          <button type="button" className="btn btn-secondary btn-small" onClick={() => goTo('reservas')}>
            Ver todas
          </button>
        </div>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Paquete</th>
                <th>Viaje</th>
                <th>Personas</th>
                <th>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.reservations.slice(0, 6).map((reservation) => (
                <tr key={reservation.id_reserva}>
                  <td>
                    <button
                      type="button"
                      className="link-button admin-strong"
                      onClick={() => goTo('reservas', { reserva: reservation.id_reserva })}
                    >
                      {reservation.codigo_reserva}
                    </button>
                  </td>
                  <td>
                    <span className="admin-thumb-cell">
                      <img
                        src={data.covers[reservation.id_paquete_turistico] || fallbackImage}
                        alt=""
                        loading="lazy"
                      />
                      {packageName(reservation.id_paquete_turistico)}
                    </span>
                  </td>
                  <td className="admin-muted">{formatDate(reservation.fecha_reserva)}</td>
                  <td>{reservation.cantidad_personas}</td>
                  <td className="admin-strong">{formatCurrency(reservation.total_reserva)}</td>
                  <td><span className={`badge badge-${reservation.estado}`}>{reservation.estado}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.reservations.length === 0 && <p className="admin-empty">Todavía no hay reservas.</p>}
        </div>
      </div>
    </>
  );
}

export default SummarySection;
