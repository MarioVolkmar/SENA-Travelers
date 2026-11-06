import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import { downloadFile, openFile } from '../../../utils/download';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { matches, RESERVATION_STATUSES, useAdminAction } from '../adminShared';

import Select from '../../../components/Select/Select';
const FILTERS = [{ key: '', label: 'Todas' }, ...RESERVATION_STATUSES.map((estado) => ({ key: estado, label: estado }))];

function ReservationsSection({ onDataChanged }) {
  const [reservations, setReservations] = useState(null);
  const [packages, setPackages] = useState({});
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const { busy, message, error, run } = useAdminAction();
  const { confirm, dialog } = useConfirm();
  const [voucherError, setVoucherError] = useState('');

  const viewVoucher = async (reservation) => {
    setVoucherError('');
    try {
      await openFile(`/vouchers/${reservation.id_reserva}`);
    } catch (requestError) {
      setVoucherError(getErrorMessage(requestError, requestError.message || 'No fue posible abrir el voucher.'));
    }
  };

  const downloadVoucher = async (reservation) => {
    setVoucherError('');
    try {
      await downloadFile(`/vouchers/${reservation.id_reserva}`, `voucher-${reservation.codigo_reserva}.pdf`);
    } catch (requestError) {
      setVoucherError(getErrorMessage(requestError, requestError.message || 'No fue posible descargar el voucher.'));
    }
  };

  const load = useCallback(async () => {
    const [reservationsResponse, packagesResponse] = await Promise.all([
      api.get('/reservations/'),
      api.get('/packages/admin'),
    ]);

    setReservations([...reservationsResponse.data].sort((a, b) => b.id_reserva - a.id_reserva));
    setPackages(Object.fromEntries(packagesResponse.data.map((item) => [item.id_paquete_turistico, item.nombre])));
  }, []);

  useEffect(() => {
    load().catch(() => setReservations([]));
  }, [load]);

  const changeStatus = async (reservation, estado) => {
    const cancelling = estado === 'cancelada';
    const accepted = await confirm({
      title: cancelling ? 'Cancelar reserva' : 'Cambiar estado de la reserva',
      subtitle: reservation.codigo_reserva,
      message: cancelling
        ? 'La cancelación hecha por Travelers no tiene penalidad: se reembolsa todo lo pagado y se anulan las órdenes a proveedores. No se puede deshacer.'
        : `La reserva pasará a «${estado}».`,
      confirmLabel: cancelling ? 'Cancelar reserva' : 'Cambiar estado',
      tone: cancelling ? 'danger' : 'primary',
    });
    if (!accepted) return;

    const { ok } = await run(
      () => api.patch(`/reservations/${reservation.id_reserva}/status`, { estado }),
      `Reserva ${reservation.codigo_reserva} marcada como ${estado}.`
    );

    if (ok) {
      await load();
      onDataChanged();
    }
  };

  if (!reservations) return <p className="page-status">Cargando reservas...</p>;

  const visible = reservations
    .filter((item) => !filter || item.estado === filter)
    .filter((item) => !query || matches(item.codigo_reserva, query) || matches(packages[item.id_paquete_turistico], query));

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Reservas</h1>
          <p>Cambiar el estado aquí no aplica la política de cancelación (es un ajuste manual del administrador).</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />
      <Toast text={voucherError} tone="error" />

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por código o paquete"
              aria-label="Buscar reservas"
            />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar por estado">
            {FILTERS.map((option) => (
              <button
                key={option.key}
                type="button"
                className="chip"
                aria-pressed={filter === option.key}
                onClick={() => setFilter(option.key)}
              >
                <span style={{ textTransform: 'capitalize' }}>{option.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="reservas">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Paquete</th>
                <th>Viaje</th>
                <th>Personas</th>
                <th>Total</th>
                <th>Cancelación</th>
                <th>Estado</th>
                <th>Voucher</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((reservation) => (
                <tr key={reservation.id_reserva}>
                  <td className="admin-strong">{reservation.codigo_reserva}</td>
                  <td>{packages[reservation.id_paquete_turistico] || `#${reservation.id_paquete_turistico}`}</td>
                  <td className="admin-muted">{formatDate(reservation.fecha_reserva)}</td>
                  <td>{reservation.cantidad_personas}</td>
                  <td className="admin-strong">{formatCurrency(reservation.total_reserva)}</td>
                  <td className="admin-muted">
                    {reservation.fecha_cancelacion
                      ? `Penalidad ${formatCurrency(reservation.penalidad_cancelacion)} · Reembolso ${formatCurrency(reservation.reembolso)}`
                      : '—'}
                  </td>
                  <td>
                    {reservation.estado === 'cancelada' ? (
                      <span className="badge badge-cancelada" title="Una reserva cancelada no se puede reactivar">
                        cancelada
                      </span>
                    ) : (
                    <Select
                      className="admin-select"
                      value={reservation.estado}
                      disabled={busy}
                      aria-label={`Estado de ${reservation.codigo_reserva}`}
                      onChange={(event) => changeStatus(reservation, event.target.value)}
                    >
                      {RESERVATION_STATUSES.map((estado) => (
                        <option key={estado} value={estado}>{estado}</option>
                      ))}
                    </Select>
                    )}
                  </td>
                  <td>
                    <div className="admin-actions">
                      <IconButton
                        icon="eye"
                        label="Ver voucher (PDF)"
                        variant="info"
                        hidden={reservation.estado !== 'confirmada'}
                        onClick={() => viewVoucher(reservation)}
                      />
                      <IconButton
                        icon="download"
                        label="Descargar voucher"
                        hidden={reservation.estado !== 'confirmada'}
                        onClick={() => downloadVoucher(reservation)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay reservas con esos filtros.</p>}
        </div>
      </div>
      {dialog}
    </>
  );
}

export default ReservationsSection;
