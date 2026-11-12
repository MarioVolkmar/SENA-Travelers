import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import Icon from '../../../components/Icon/Icon';
import { formatCurrency, formatDate } from '../../../utils/format';
import { matches, PAYMENT_STATUS_LABELS } from '../adminShared';
import ReservationAdminView from './ReservationAdminView';

function PaymentsSection({ goTo, searchParams }) {
  // Detalle del pago dentro de la consola: ?seccion=pagos&pago=<id>
  const selectedId = Number(searchParams?.get('pago')) || null;
  const [payments, setPayments] = useState(null);
  const [reservations, setReservations] = useState({});
  const [query, setQuery] = useState('');

  useEffect(() => {
    Promise.all([api.get('/payments/'), api.get('/reservations/')])
      .then(([paymentsResponse, reservationsResponse]) => {
        setPayments([...paymentsResponse.data].sort((a, b) => b.id_pago - a.id_pago));
        setReservations(Object.fromEntries(reservationsResponse.data.map((item) => [item.id_reserva, item])));
      })
      .catch(() => setPayments([]));
  }, []);

  if (!payments) return <p className="page-status">Cargando pagos...</p>;

  const selected = selectedId && payments.find((payment) => payment.id_pago === selectedId);
  if (selected) {
    return (
      <ReservationAdminView
        key={selected.id_pago}
        reservationId={selected.reserva_id}
        goTo={goTo}
        backLabel="Volver a pagos"
        highlightPayment
        onBack={() => goTo('pagos')}
      />
    );
  }

  const visible = payments.filter(
    (payment) => !query
      || matches(payment.referencia_pago, query)
      || matches(reservations[payment.reserva_id]?.codigo_reserva, query)
  );

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Pagos</h1>
          <p>Pagos simulados de las reservas y su estado de reembolso.</p>
        </div>
      </div>

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por referencia o reserva"
              aria-label="Buscar pagos"
            />
          </label>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="pagos">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Referencia</th>
                <th>Reserva</th>
                <th>Método</th>
                <th>Valor</th>
                <th>Reembolso</th>
                <th>Fecha</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((payment) => {
                const reservation = reservations[payment.reserva_id];

                return (
                  <tr key={payment.id_pago}>
                    <td>
                      <button
                        type="button"
                        className="link-button admin-strong"
                        onClick={() => goTo('pagos', { pago: payment.id_pago })}
                        title="Ver detalle del pago"
                      >
                        {payment.referencia_pago}
                      </button>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => goTo('reservas', { reserva: payment.reserva_id })}
                      >
                        {reservation?.codigo_reserva || `#${payment.reserva_id}`}
                      </button>
                    </td>
                    <td>{payment.metodo_pago}</td>
                    <td className="admin-strong">{formatCurrency(payment.valor)}</td>
                    <td className="admin-muted">
                      {reservation?.reembolso != null ? formatCurrency(reservation.reembolso) : '—'}
                    </td>
                    <td className="admin-muted">{formatDate(payment.fecha_pago)}</td>
                    <td>
                      <span className={`badge badge-${payment.estado_pago === 'aprobado' ? 'aprobado' : 'pendiente'}`}>
                        {PAYMENT_STATUS_LABELS[payment.estado_pago] || payment.estado_pago}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay pagos.</p>}
        </div>
      </div>
    </>
  );
}

export default PaymentsSection;
